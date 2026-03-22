"""
Визуализатор аудио в реальном времени с синхронизацией по частотам.

Модуль предоставляет аудиовизуализацию, анализирующую звук с микрофона или
системного микшера и отображающую 10 различных режимов визуализации,
синхронизированных с 3 частотными полосами (НЧ, СЧ, ВЧ).

Основные возможности:
    - Анализ FFT в реальном времени на отдельном потоке
    - 10 режимов визуализации: Облака, Кольца, Спектр, Частицы, Солнце,
      Снег, Тоннель, Спираль, Струны, Океан
    - Режим калейдоскопа (4-кратное симметричное отражение)
    - Автопилот (автоматическая смена режимов по биту или таймеру)
    - Режим релаксации (замедленная анимация)
    - Настраиваемая чувствительность

Требования:
    - Python 3.8+
    - PySide6
    - NumPy

Пример использования:
    >>> from PySide6.QtWidgets import QApplication
    >>> import sys
    >>> app = QApplication(sys.argv)
    >>> win = DiscoWindow()
    >>> win.show()
    >>> sys.exit(app.exec())

Автор: Disco Visualizer Team
Версия: Final Pro Edition
"""

import numpy as np  # Импорт библиотеки для математических вычислений с массивами
import math  # Импорт стандартных математических функций (синусы, косинусы)
import sys  # Импорт системы для управления выходом из программы
import random  # Импорт генератора случайных чисел для снега и частиц
import time  # Импорт функций времени для работы автопилота


# ============================================================================
# КОНСТАНТЫ НАСТРОЕК АУДИОАНАЛИЗА
# ============================================================================

# Настройки аудиоформата
SAMPLE_RATE = 44100          # Частота дискретизации, Гц (стандарт CD-качество)
AUDIO_CHANNELS = 1           # Количество каналов (1 = моно)
AUDIO_FORMAT = 16            # Глубина квантования, бит

# Параметры буфера и FFT
BUFFER_SIZE = 2048           # Размер буфера чтения аудиоданных (степень 2 для FFT)
MIN_BYTES_TO_READ = 2048     # Минимальное количество байт для обработки
HISTORY_FRAMES = 12          # Количество кадров истории для вычисления среднего фона

# Частотные диапазоны (индексы в массиве FFT после преобразования)
# Низкие частоты (бас): ~20-200 Гц -> индексы 2-12
# Средние частоты: ~200-2000 Гц -> индексы 12-150
# Высокие частоты: ~2000-8000 Гц -> индексы 150-500
FFT_BANDS = {
    'low': {'range': (2, 12), 'multiplier': 25},    # НЧ: диапазон индексов, множитель яркости
    'mid': {'range': (12, 150), 'multiplier': 35},  # СЧ: диапазон индексов, множитель яркости
    'high': {'range': (150, 500), 'multiplier': 55} # ВЧ: диапазон индексов, множитель яркости
}

# Параметры сглаживания (инерции) - экспоненциальное скользящее среднее
# Коэффициент для нарастания (когда громкость увеличивается) - быстрая реакция
SMOOTHING_RATE_RISE = 0.92
# Коэффициент для затухания (когда громкость уменьшается) - плавное затухание
SMOOTHING_RATE_FALL = 0.4

# Пороги и множители
BASS_EXPLOSION_THRESHOLD = 180  # Порог баса для срабатывания "вспышки" (0-255)
EXPLOSION_DECAY_RELAX = 0.97    # Коэффициент затухания вспышки в режиме релаксации
EXPLOSION_DECAY_RAVE = 0.93     # Коэффициент затухания вспышки в режиме рейва
SCALE_PULSE_MAX = 0.8           # Максимальная величина пульсации масштаба
SCALE_PULSE_THRESHOLD = 180.0   # Порог цвета для расчёта пульсации

# Настройки автопилота
AUTOPILOT_BEAT_INTERVAL = 4     # Минимальный интервал смены режима по биту, секунды
AUTOPILOT_TIME_INTERVAL = 15    # Интервал смены режима по таймеру, секунды

# Скорости анимации
BASE_ANGLE_SPEED = 0.05          # Базовая скорость вращения за кадр
BASE_ORBIT_SPEED = 0.02          # Базовая скорость изменения фазы орбиты
BASE_TUNNEL_SPEED = 0.03         # Базовая скорость движения тоннеля
RELAX_SPEED_MULTIPLIER = 0.25    # Множитель замедления в режиме релаксации

# Параметры снежинок
SNOWFLAKE_COUNT = 100            # Количество снежинок
SNOWFLAKE_MIN_SPEED = 0.003      # Минимальная скорость падения
SNOWFLAKE_SPEED_RANGE = 0.007    # Диапазон случайной скорости

# Настройки визуализации
SILENCE_THRESHOLD = 5            # Порог тишины (ниже этого значения цвет не рисуется)

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QSlider,
    QLabel,
    QComboBox,
    QMenu,
    QWidgetAction,
    QApplication
    )  # Виджеты интерфейса

from PySide6.QtCore import (
    Qt,
    QThread,
    Signal,
    QPointF,
    QRectF
    )  # Ядро Qt: потоки, сигналы, геометрия

from PySide6.QtGui import (
    QPainter,
    QColor,
    QRadialGradient,
    QLinearGradient,
    QPen,
    QBrush,
    QPainterPath
    )  # Графика

from PySide6.QtMultimedia import (
    QAudioSource,
    QAudioFormat,
    QMediaDevices
    )  # Модули для работы со звуком

class AudioAnalysisThread(QThread):
    """
    Поток для непрерывного анализа аудио в реальном времени.

    Этот класс запускает отдельный поток Qt, который захватывает звук с
    аудиовхода (микрофона или системного микшера), выполняет FFT-анализ
    и передаёт данные о яркости и масштабе в основной поток через сигнал.

    Анализ выполняется по трём частотным полосам:
        - НЧ (низкие частоты, ~20-200 Гц) -> красный канал
        - СЧ (средние частоты, ~200-2000 Гц) -> зелёный канал
        - ВЧ (высокие частоты, ~2000-8000 Гц) -> синий канал

    Для каждой полосы вычисляются два параметра:
        - RGB-значение (0-255): яркость свечения
        - Scale-коэффициент (1.0+): масштаб элементов визуализации

    Используется скользящее окно истории для выделения только резких
    всплесков над фоновым уровнем шума.

    Атрибуты:
        sensitivity (int): Чувствительность детектора (меньше = ярче).
                          Диапазон: 10-150. Значение по умолчанию: 45.

    Сигналы:
        data_signal(int, int, int, float, float, float):
            Испускается после обработки каждого кадра аудио.
            Аргументы:
                r (int): Яркость красного канала (НЧ), диапазон 0-255
                g (int): Яркость зелёного канала (СЧ), диапазон 0-255
                b (int): Яркость синего канала (ВЧ), диапазон 0-255
                s1 (float): Масштаб для НЧ (1.0 - 1.8)
                s2 (float): Масштаб для СЧ (1.0 - 1.8)
                s3 (float): Масштаб для ВЧ (1.0 - 1.8)

    Пример:
        >>> thread = AudioAnalysisThread()
        >>> thread.data_signal.connect(my_callback)
        >>> thread.start()
        >>> # Через некоторое время my_callback будет получать данные
        >>> thread.set_sensitivity(30)  # Увеличить яркость
    """

    # Сигнал передаёт: R, G, B (яркости) и 3 масштаба
    data_signal = Signal(int, int, int, float, float, float)

    def __init__(self):
        """
        Инициализирует поток анализа аудио.

        Конструктор создаёт объект потока с настройками по умолчанию:
            - sensitivity = 45 (средняя чувствительность)
            - is_running = True (поток активен)
            - audio_source = None (источник звука создаётся в run())

        Примечание:
            Аудиоустройство открывается не в конструкторе, а в методе run(),
            чтобы избежать проблем с созданием QMediaDevices в главном потоке
            до запуска QApplication.
        """
        super().__init__()  # Инициализация базового класса QThread
        self.sensitivity = 45  # Чувствительность: меньше = ярче (делитель громкости)
        self.is_running = True  # Флаг работы цикла потока
        self.audio_source = None  # Объект захвата звука (QAudioSource)
        self.io_device = None  # Устройство ввода-вывода для чтения данных

    def set_sensitivity(self, val):
        """
        Устанавливает чувствительность анализатора.

        Параметры:
            val (int): Новое значение чувствительности.
                      Диапазон: 10-150 (рекомендуется).
                      Меньшее значение = более яркая реакция на звук.

        Примечание:
            При высокой чувствительности (низкое значение) анализатор
            будет реагировать даже на тихие звуки. При низкой
            чувствительности (высокое значение) — только на громкие.

        Пример:
            >>> thread.set_sensitivity(20)  # Высокая яркость
            >>> thread.set_sensitivity(100) # Низкая яркость
        """
        self.sensitivity = val

    def run(self):
        """
        Главный цикл потока анализа аудио.

        Этот метод выполняется в отдельном потоке и выполняет:
            1. Поиск и открытие аудиовхода (микрофон или системный микшер)
            2. Непрерывный захват аудиоданных
            3. FFT-преобразование и анализ спектра
            4. Вычисление яркости и масштаба для каждой частотной полосы
            5. Отправка результатов через сигнал data_signal

        Логика работы:
            - Сначала пытается найти системный микшер ("Stereo Mix" или "Monitor")
              для захвата системного звука. Если не найден — использует микрофон.
            - Читает аудиобуфер порциями по 2048 байт
            - Выполняет FFT (быстрое преобразование Фурье)
            - Делит спектр на 3 частотные полосы
            - Для каждой полосы вычисляет всплеск над средним фоном
            - Применяет сглаживание (экспоненциальное скользящее среднее)
            - Рассчитывает коэффициент масштаба на основе яркости

        Алгоритм сглаживания:
            - При нарастании громкости: используется быстрый отклик (0.92)
            - При спаде громкости: используется медленное затухание (0.4)
            - Это создаёт эффект "инерции" визуализации

        Вычисление масштаба:
            - scale = 1.0 + min(0.8, brightness / 180.0)
            - При яркости 0 -> scale = 1.0
            - При яркости 180+ -> scale = 1.8 (максимум)

        Примечание:
            Метод автоматически вызывается при запуске потока через start().
            Цикл работает пока is_running = True. Для остановки
            необходимо установить is_running = False и дождаться finish().

        Обработка ошибок:
            - Если аудиоустройство недоступно — молча продолжает цикл ожидания
            - Если данных недостаточно — спит 10мс и продолжает
            - При ошибках FFT или чтения — пропускает кадр
        """
        devices = QMediaDevices.audioInputs()  # Получаем список всех аудио-входов
        target_device = QMediaDevices.defaultAudioInput()  # Берем устройство по умолчанию

        for dev in devices:  # Перебираем все найденные устройства
            desc = dev.description().lower()  # Переводим описание в нижний регистр

            if "monitor" in desc or "stereo mix" in desc:  # Ищем системный микшер
                target_device = dev  # Назначаем его целью для захвата
                break  # Выходим из цикла поиска

        format = QAudioFormat()  # Создаем объект настроек формата аудио
        format.setSampleRate(SAMPLE_RATE)  # Устанавливаем частоту дискретизации
        format.setChannelCount(AUDIO_CHANNELS)  # Устанавливаем количество каналов
        format.setSampleFormat(QAudioFormat.Int16)  # Устанавливаем 16-битный формат

        if not target_device.isNull():  # Если устройство захвата определено
            self.audio_source = QAudioSource(target_device, format)  # Создаем источник
            self.io_device = self.audio_source.start()  # Запускаем чтение данных

        v_prev = [0, 0, 0]  # Список для хранения прошлых значений яркости
        s_prev = [1.0, 1.0, 1.0]  # Список для хранения прошлых значений масштаба
        hist = [[0.0] * HISTORY_FRAMES for _ in range(3)]  # История громкости для 3 полос

        while self.is_running:  # Пока флаг работы активен
            if self.io_device is None or self.io_device.bytesAvailable() < MIN_BYTES_TO_READ:
                self.msleep(10)  # Спим 10 миллисекунд
                continue  # Переходим к следующей итерации цикла

            raw_data = self.io_device.read(BUFFER_SIZE)  # Читаем порцию сырых байтов
            samples = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32)  # В числа

            if len(samples) == 0:
                continue  # Пропускаем, если данных нет

            fft = np.abs(np.fft.rfft(samples))  # Делаем преобразование Фурье (спектр)

            # Конфигурация частотных полос: (индексы FFT, множитель яркости)
            fft_cfg = [
                {'r': FFT_BANDS['low']['range'], 'm': FFT_BANDS['low']['multiplier']},
                {'r': FFT_BANDS['mid']['range'], 'm': FFT_BANDS['mid']['multiplier']},
                {'r': FFT_BANDS['high']['range'], 'm': FFT_BANDS['high']['multiplier']}
            ]
            rgb_now = [0, 0, 0]  # Обнуляем текущие значения RGB

            for i in range(3):  # Цикл по НЧ, СЧ, ВЧ
                s, e = fft_cfg[i]['r']  # Извлекаем границы диапазона спектра
                val = np.mean(fft[s:e]) if e < len(fft) else 0  # Средняя громкость полосы
                avg = sum(hist[i]) / HISTORY_FRAMES  # Вычисляем средний фон за историю
                diff = max(0, val - (avg if avg > 0 else 1.0))  # Оставляем только всплески
                rgb_now[i] = int(min(255, (diff / max(1, self.sensitivity)) * fft_cfg[i]['m']))
                hist[i].pop(0)  # Удаляем старое значение из истории
                hist[i].append(val)  # Добавляем новое значение в историю

            out_rgb = [0, 0, 0]  # Список итоговых цветов
            out_sc = [1.0, 1.0, 1.0]  # Список итоговых масштабов

            for i in range(3):  # Цикл сглаживания данных
                # Быстрый отклик при нарастании, медленное затухание при спаде
                rate = SMOOTHING_RATE_RISE if rgb_now[i] > v_prev[i] else SMOOTHING_RATE_FALL
                v_prev[i] = int(v_prev[i] * (1 - rate) + rgb_now[i] * rate)  # Формула сглаживания
                out_rgb[i] = max(0, min(255, v_prev[i]))  # Ограничиваем цвет
                st = 1.0 + min(SCALE_PULSE_MAX, out_rgb[i] / SCALE_PULSE_THRESHOLD)  # Рассчитываем пульсацию
                s_prev[i] = s_prev[i] * SMOOTHING_RATE_FALL + st * (1 - SMOOTHING_RATE_FALL)
                out_sc[i] = s_prev[i]  # Записываем результат масштаба
            self.data_signal.emit(*out_rgb, *out_sc)  # Отправляем данные в основное окно

        if self.audio_source:
            self.audio_source.stop()  # Закрываем аудио при выходе

class DiscoWindow(QWidget):
    """
    Основное окно визуализатора аудио.

    Этот класс создаёт окно Qt с 10 режимами визуализации, которые
    синхронизируются с анализом аудио в реальном времени.

    Режимы визуализации (modes):
        1. Облака   - Три вращающихся светящихся круга на орбите
        2. Кольца   - Концентрические светящиеся кольца
        3. Спектр   - Три вертикальные колонки (эквалайзер)
        4. Частицы  - Три группы частиц на вращающейся орбите
        5. Солнце   - Центральное пульсирующее светило
        6. Снег     - Падающие снежинки (только для режима "Снег")
        7. Тоннель  - Вращающийся туннель из квадратов
        8. Спираль  - Винтовая спираль из частиц
        9. Струны   - 35 вибрирующих горизонтальных линий
        10. Океан   - Три волнообразных тумана внизу

    Управление (правый клик мыши):
        - Выбор режима визуализации из выпадающего списка
        - Включение/выключение автопилота
        - Переключение режима Рейв/Релакс
        - Включение/выключение калейдоскопа
        - Настройка чувствительности (яркости)

    Цветовая схема:
        - Красный канал: низкие частоты (бас)
        - Зелёный канал: средние частоты
        - Синий канал: высокие частоты

    Атрибуты:
        colors (list[int]): Текущие значения RGB [R, G, B], диапазон 0-255
        scales (list[float]): Текущие коэффициенты масштаба [S1, S2, S3]
        cur_mode (str): Текущий режим визуализации
        is_relax (bool): Режим релаксации (замедленная анимация)
        kaleido (bool): Режим калейдоскопа (4-кратное отражение)
        auto_pilot (bool): Автоматическая смена режимов
        explosion (float): Сила импульса от баса (0.0 - 1.0)
        angle (float): Текущий угол вращения сцены (радианы)
        orbit_phase (float): Фаза "дыхания" орбиты (для режима Облака)
        tunnel_phase (float): Фаза движения тоннеля (для режима Тоннель)

    Пример:
        >>> app = QApplication(sys.argv)
        >>> win = DiscoWindow()
        >>> win.show()
        >>> sys.exit(app.exec())
    """

    def __init__(self):
        """
        Создаёт окно визуализатора и запускает анализ аудио.

        Инициализация включает:
            - Настройку окна (заголовок, размер 800x800)
            - Подключение контекстного меню (правый клик)
            - Создание хранилищ для цветов, масштабов и состояний анимации
            - Генерацию 100 снежинок со случайными позициями и скоростями
            - Запуск потока AudioAnalysisThread для анализа аудио

        Примечание:
            Поток анализа аудио запускается автоматически в конструкторе.
            Звук будет захватываться с микрофона или системного микшера.
        """
        super().__init__()  # Инициализация родительского QWidget
        self.setWindowTitle("Disco: Final Pro Edition")  # Установка заголовка окна
        self.resize(800, 800)  # Установка размера окна
        self.setContextMenuPolicy(Qt.CustomContextMenu)  # Разрешаем кастомное меню
        self.customContextMenuRequested.connect(self.show_settings)  # Связываем ПКМ с меню
        self.colors = [0, 0, 0]  # Хранилище текущих цветов RGB [R, G, B]
        self.scales = [1.0, 1.0, 1.0]  # Хранилище текущих коэффициентов масштаба
        self.angle = 0.0  # Угол вращения сцены (в радианах)
        self.orbit_phase = 0.0  # Фаза "дыхания" орбиты (для режима Облака)
        self.explosion = 0.0  # Сила импульса от баса (0.0 - 1.0)

        self.modes = [
            "1. Облака",
            "2. Кольца",
            "3. Спектр",
            "4. Частицы",
            "5. Солнце",
            "6. Снег",
            "7. Тоннель",
            "8. Спираль",
            "9. Струны",
            "10. Океан"]  # Список модов визуализации

        self.cur_mode = "1. Облака"  # Текущий активный режим
        self.is_relax = False  # Флаг режима релаксации (замедление анимации в 4 раза)
        self.kaleido = False  # Флаг режима калейдоскопа (4-кратное симметричное отражение)
        self.auto_pilot = False  # Флаг автоматической смены режимов
        self.last_mode_change = time.time()  # Таймер последней смены мода
        # Снежинки: [x (0-1), y (0-1), частотная полоса (0-2), скорость падения]
        self.snow_flakes = [
            [random.random(), random.random(), random.randint(0, 2),
             SNOWFLAKE_MIN_SPEED + random.random() * SNOWFLAKE_SPEED_RANGE]
            for _ in range(SNOWFLAKE_COUNT)
        ]
        self.tunnel_phase = 0.0  # Текущая фаза полета в тоннеле

        # Запуск потока анализа аудио
        self.thread = AudioAnalysisThread()  # Создаем поток анализа
        self.thread.data_signal.connect(self.update_data)  # Связываем сигнал с обновлением
        self.thread.start()  # Запускаем поток анализа

    def update_data(self, r, g, b, s1, s2, s3):
        """
        Обрабатывает новые данные из потока аудиоанализа.

        Этот слот вызывается каждый раз, когда поток AudioAnalysisThread
        отправляет сигнал data_signal с новыми данными анализа.

        Параметры:
            r (int): Яркость красного канала (НЧ), диапазон 0-255
            g (int): Яркость зелёного канала (СЧ), диапазон 0-255
            b (int): Яркость синего канала (ВЧ), диапазон 0-255
            s1 (float): Коэффициент масштаба для НЧ (1.0 - 1.8)
            s2 (float): Коэффициент масштаба для СЧ (1.0 - 1.8)
            s3 (float): Коэффициент масштаба для ВЧ (1.0 - 1.8)

        Выполняемые действия:
            1. Обновляет цвета и масштабы
            2. Обновляет углы вращения (с учётом режима релаксации)
            3. Обрабатывает "вспышку" от баса (explosion)
            4. Обновляет позиции снежинок (если есть)
            5. Вызывает перерисовку окна

        Логика "вспышки" (explosion):
            - Когда уровень баса (r) превышает 180, создаётся вспышка
            - В режиме релаксации сила вспышки меньше (0.4 vs 1.0)
            - При отсутствии баса вспышка плавно затухает
            - Коэффициент затухания также зависит от режима

        Автопилот:
            - По биту: смена режима каждые 4 секунды при обнаружении баса
            - По таймеру: смена режима каждые 15 секунд при отсутствии баса
        """
        self.colors = [r, g, b]  # Обновляем список цветов
        self.scales = [s1, s2, s3]  # Обновляем список масштабов

        # Множитель скорости: замедление в режиме релаксации
        speed_k = RELAX_SPEED_MULTIPLIER if self.is_relax else 1.0

        # Обновление углов вращения
        self.angle += BASE_ANGLE_SPEED * speed_k  # Изменяем угол вращения
        self.orbit_phase += BASE_ORBIT_SPEED * speed_k  # Изменяем фазу орбиты
        self.tunnel_phase += BASE_TUNNEL_SPEED * speed_k * (sum(self.scales) / 3.0)  # Двигаем тоннель

        # Обработка вспышки от баса
        if r > BASS_EXPLOSION_THRESHOLD:  # Если уровень баса выше порога
            # В режиме релаксации вспышка слабее
            self.explosion = 1.0 if not self.is_relax else 0.4
            # Автопилот: смена режима по биту
            if self.auto_pilot and (time.time() - self.last_mode_change > AUTOPILOT_BEAT_INTERVAL):
                self.next_mode()
        else:  # Если баса нет
            # Затухание вспышки
            decay = EXPLOSION_DECAY_RELAX if self.is_relax else EXPLOSION_DECAY_RAVE
            self.explosion *= decay
            # Автопилот: смена режима по таймеру
            if self.auto_pilot and (time.time() - self.last_mode_change > AUTOPILOT_TIME_INTERVAL):
                self.next_mode()

        # Обновление позиций снежинок
        for f in self.snow_flakes:  # Цикл по всем снежинкам
            f[1] += f[3] * speed_k  # Двигаем снежинку вниз (Y координата)
            if f[1] > 1.05:
                f[1] = -0.05
                f[0] = random.random()  # Респаун снежинки

        self.update()  # Вызываем перерисовку окна

    def next_mode(self):
        """
        Переключает на следующий режим визуализации.

        Выполняет циклический переход по списку modes:
        1 -> 2 -> 3 -> ... -> 10 -> 1

        Используется автопилотом для автоматической смены режимов.
        Обновляет таймер last_mode_change для отслеживания интервала смены.
        """
        idx = (self.modes.index(self.cur_mode) + 1) % len(self.modes)  # Считаем следующий индекс
        self.cur_mode = self.modes[idx]  # Устанавливаем название мода
        self.last_mode_change = time.time()  # Обновляем время смены

    def show_settings(self, pos):
        """
        Показывает контекстное меню настроек.

        Вызывается при правом клике мыши на окно. Создаёт меню со следующими
        элементами:

        1. Выпадающий список (QComboBox) для выбора режима визуализации
        2. Переключатель автопилота (ВКЛ/ВЫКЛ)
        3. Переключатель режима Рейв/Релакс
        4. Переключатель калейдоскопа (ВКЛ/ВЫКЛ)
        5. Горизонтальный слайдер для настройки чувствительности

        Параметры:
            pos (QPoint): Позиция курсора на экране, куда будет показано меню

        Примечание:
            Меню автоматически позиционируется в точке клика с помощью
            mapToGlobal() для преобразования локальных координат в глобальные.
        """
        menu = QMenu(self)  # Создаем объект меню
        menu.setStyleSheet("QMenu { background: #1a1a1a; color: white; border: 1px solid #444; }")  # Дизайн
        cb = QComboBox()  # Создаем выпадающий список
        cb.addItems(self.modes)  # Добавляем моды
        cb.setCurrentText(self.cur_mode)  # Ставим текущий мод
        cb.currentTextChanged.connect(lambda t:
            setattr(self, 'cur_mode', t))  # Связь выбора
        wa = QWidgetAction(menu)  # Обертка виджета для меню
        c = QWidget()
        l = QVBoxLayout(c)
        l.addWidget(QLabel("СТИЛЬ:"))
        l.addWidget(cb)  # Слой меню
        wa.setDefaultWidget(c)
        menu.addAction(wa)
        menu.addSeparator()  # Добавляем в меню
        menu.addAction("🤖 Автопилот: " + ("ВКЛ" if self.auto_pilot else "ВЫКЛ"), lambda: setattr(self, 'auto_pilot', not self.auto_pilot))  # Переключатель автопилота
        menu.addAction("🌙 Режим: РЕЛАКС" if self.is_relax else "🔥 Режим: РЕЙВ", lambda: setattr(self, 'is_relax', not self.is_relax))  # Переключатель рейва
        menu.addAction("💠 Калейдоскоп: " + ("ВКЛ" if self.kaleido else "ВЫКЛ"), lambda: setattr(self, 'kaleido', not self.kaleido))  # Калейдоскоп
        sl = QSlider(Qt.Horizontal)
        sl.setRange(10, 150)  # Диапазон чувствительности (10-150)
        sl.setValue(self.thread.sensitivity)
        sl.valueChanged.connect(self.thread.set_sensitivity)  # Слайдер яркости
        wa2 = QWidgetAction(menu)
        c2 = QWidget()
        l2 = QVBoxLayout(c2)
        l2.addWidget(QLabel("ЯРКОСТЬ:"))
        l2.addWidget(sl)  # Слой слайдера
        wa2.setDefaultWidget(c2)
        menu.addAction(wa2)
        menu.exec(self.mapToGlobal(pos))  # Показ меню

    def paintEvent(self, event):
        """
        Основной метод отрисовки кадра визуализации.

        Этот метод вызывается Qt при необходимости перерисовать окно
        (обычно после вызова update()). Является основным циклом отрисовки.

        Технические детали:
            - Использует QPainter с включённым сглаживанием (Antialiasing)
            - Применяет режим CompositionMode_Plus для эффекта свечения
            - Очищает фон чёрным цветом перед каждой отрисовкой

        Внутренняя функция draw_scene():
            Рисует текущий режим визуализации в зависимости от cur_mode.

            Режимы:
                1. Облака   - Три круга на орбите с радиальными градиентами
                2. Кольца   - Концентрические кольца с градиентной заливкой
                3. Спектр   - Три вертикальных столба (эквалайзер)
                4. Частицы  - Три группы частиц, вращающихся по орбите
                5. Солнце   - Центральный круг с пульсацией
                6. Снег     - 100 падающих снежинок
                7. Тоннель  - 12 вращающихся квадратов
                8. Спираль  - 60 точек по спирали
                9. Струны   - 35 синусоидальных линий
                10. Океан   - 3 волнообразных тумана

        Калейдоскоп:
            Если включён режим kaleido, сцена рисуется 4 раза с поворотом
            на 0°, 90°, 180° и 270° вокруг центра окна.

        Параметры:
            event (QPaintEvent): Событие перерисовки от Qt (не используется)
        """
        p = QPainter(self)
        p.fillRect(self.rect(), Qt.black)
        p.setRenderHint(QPainter.Antialiasing)  # Фон и сглаживание
        w, h = self.width(), self.height()
        cx, cy = w/2, h/2  # Размеры окна и центр

        def draw_scene(painter):  # Функция отрисовки сцены
            painter.setCompositionMode(QPainter.CompositionMode_Plus)  # Режим свечения цветов
            if self.cur_mode == "1. Облака":  # Отрисовка Облаков
                orb = (min(w,h)/8.5 + (min(w,h)/3.2 - min(w,h)/8.5)*(0.5+0.5*math.sin(self.orbit_phase))) + (min(w,h)/2.5)*self.explosion  # Радиус орбиты
                angs = [self.angle, self.angle + 2.09, self.angle + 4.18]  # Углы разлета трех точек
                for i in range(3):  # Цикл по трем цветам
                    if self.colors[i] < SILENCE_THRESHOLD:
                        continue  # Пропуск тишины
                    pos = QPointF(cx + orb*math.cos(angs[i]), cy + orb*math.sin(angs[i]))  # Позиция круга
                    rad = (max(w,h)/1.6) * self.scales[i]  # Радиус круга
                    grad = QRadialGradient(pos, rad)
                    c = [0,0,0]
                    c[i] = self.colors[i]  # Создание градиента
                    grad.setColorAt(0, QColor(*c))
                    grad.setColorAt(1, Qt.black)  # Цвет к краям гаснет
                    painter.setBrush(grad)
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(pos, rad, rad)  # Рисуем круг
            elif self.cur_mode == "2. Кольца":  # Отрисовка Колец
                limit = min(w, h) * 0.4  # Лимит размера
                for i in range(3):  # Цикл по полосам
                    if self.colors[i] < SILENCE_THRESHOLD:
                        continue  # Пропуск тишины
                    center_rad = limit * (0.2 + i * 0.25) * self.scales[i]  # Радиус кольца
                    thickness = (35 + self.explosion * 60) * (min(w,h)/800) * self.scales[i]  # Толщина
                    total_r = center_rad + thickness  # Итоговый радиус
                    grad = QRadialGradient(QPointF(cx, cy), total_r)
                    c = [0,0,0]; c[i] = self.colors[i]  # Градиент кольца
                    grad.setColorAt(max(0, (center_rad - thickness) / total_r), Qt.black)  # Внутри пусто
                    grad.setColorAt(center_rad / total_r, QColor(*c)); grad.setColorAt(1.0, Qt.black)  # Светящийся ободок
                    painter.setBrush(grad); painter.setPen(Qt.NoPen)
                    painter.drawEllipse(QPointF(cx, cy), total_r, total_r)  # Рисуем кольцо
            elif self.cur_mode == "3. Спектр":  # Отрисовка Спектра
                bw = w / 3  # Ширина колонки
                for i in range(3):  # Для каждой полосы
                    if self.colors[i] < SILENCE_THRESHOLD: continue  # Пропуск тишины
                    bh, glow_w = (h * 0.95) * self.scales[i], bw * 1.5  # Высота и ширина сияния
                    center_x = i * bw + bw / 2  # Центр колонки
                    grad = QRadialGradient(QPointF(center_x, h), glow_w)
                    c = [0,0,0]
                    c[i] = self.colors[i]  # Градиент снизу
                    grad.setFocalPoint(QPointF(center_x, h - bh/3))  # Смещение фокуса вверх
                    grad.setColorAt(0, QColor(*c))
                    grad.setColorAt(0.6, QColor(c[i]//3, c[i]//3, c[i]//3, 100))
                    grad.setColorAt(1.0, Qt.black)  # Плавное затухание
                    painter.setBrush(grad)
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(QPointF(center_x, h), glow_w, bh)  # Рисуем столб
            elif self.cur_mode == "4. Частицы":  # Отрисовка Частиц
                orb = min(w, h) / 4.0 + (self.explosion * (min(w,h)/10))  # Орбита частиц
                for i in range(3):  # По трем цветам
                    if self.colors[i] < SILENCE_THRESHOLD:
                        continue  # Пропуск тишины
                    ang = self.angle + (i * 2.09)
                    pos = QPointF(cx + orb * math.cos(ang), cy + orb * math.sin(ang))  # Позиция
                    part_rad = (min(w, h) / 3.5) * self.scales[i]  # Радиус сияния
                    grad = QRadialGradient(pos, part_rad); c = [0,0,0]
                    c[i] = self.colors[i]  # Создание градиента
                    grad.setColorAt(0, QColor(*c))
                    grad.setColorAt(1, Qt.black)  # Цвет в центре гаснет
                    painter.setBrush(grad)
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(pos, part_rad, part_rad)  # Рисуем пятно
            elif self.cur_mode == "5. Солнце":  # Отрисовка Солнца
                rad = (min(w,h)/2.6) * max(self.scales) + (self.explosion*80)  # Радиус от общего звука
                grad = QRadialGradient(QPointF(cx, cy), rad)
                grad.setColorAt(0, QColor(*self.colors))
                grad.setColorAt(1, Qt.black)  # Цветное солнце
                painter.setBrush(grad)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(cx, cy), rad, rad)  # Рисуем центр
            elif self.cur_mode == "6. Снег":  # Отрисовка Снега
                for f in self.snow_flakes:  # Цикл по снежинкам
                    i = f[2]; pos = QPointF(f[0]*w, f[1]*h); rad = (8 + self.scales[i] * 15) * (min(w,h)/800)  # Координаты и размер
                    grad = QRadialGradient(pos, rad); c = [0,0,0]
                    c[i] = self.colors[i]  # Цвет снежинки от частоты
                    grad.setColorAt(0, QColor(*c))
                    grad.setColorAt(1, Qt.black)  # Градиент
                    painter.setBrush(grad)
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(pos, rad, rad)  # Рисуем снежинку
            elif self.cur_mode == "7. Тоннель":  # Отрисовка Тоннеля
                for n in range(12):  # 12 слоев квадратов
                    size_mod = (n + (self.tunnel_phase % 1.0)) / 12.0  # Модификатор размера
                    side = (max(w, h) * 1.2) * size_mod + (self.explosion * 150 * size_mod)  # Сторона квадрата
                    if side < 10:
                        continue  # Пропуск слишком маленьких
                    rect = QRectF(cx - side/2, cy - side/2, side, side)
                    opacity = int(255 * (1.0 - size_mod))  # Геометрия и прозрачность
                    painter.save()
                    painter.translate(cx, cy)
                    painter.rotate(self.angle * 10 + n * 15)
                    painter.translate(-cx, -cy)  # Поворот слоя
                    painter.setPen(QPen(QColor(*self.colors, opacity), 1 + (1.0-size_mod)*5))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawRect(rect)
                    painter.restore()  # Рисуем квадрат
            elif self.cur_mode == "8. Спираль":  # Отрисовка Спирали
                max_r = max(w, h) * 0.7  # Максимальный радиус спирали
                for i in range(60):  # 60 точек в спирали
                    norm = i / 60.0; a = self.angle * 3 + i * 0.4
                    r_spiral = (norm * max_r * self.scales[i%3]) + (self.explosion * 40)  # Геометрия спирали
                    pos = QPointF(cx + r_spiral * math.cos(a), cy + r_spiral * math.sin(a)); rad = (10 + norm * 40) * self.scales[i%3]  # Позиция и радиус
                    grad = QRadialGradient(pos, rad)
                    c = [0,0,0]
                    c[i%3] = self.colors[i%3]  # Градиент точки
                    grad.setColorAt(0, QColor(*c))
                    grad.setColorAt(1, Qt.black)  # Затухание
                    painter.setBrush(grad)
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(pos, rad, rad)  # Рисуем точку спирали
            elif self.cur_mode == "9. Струны":  # Отрисовка Струн
                painter.setBrush(Qt.NoBrush)  # Отключаем заливку
                for i in range(35):  # 35 вибрирующих линий
                    idx = i % 3; alpha = int(self.colors[idx] * (1.0 - abs(i-17)/17))  # Индекс полосы и прозрачность
                    c = [0,0,0]; c[idx] = self.colors[idx]
                    painter.setPen(QPen(QColor(*c, alpha), 1))  # Цвет линии
                    path = QPainterPath(); y_base = h * (i / 35.0)
                    path.moveTo(0, y_base)  # Начало линии
                    for x in range(0, int(w) + 30, 30):  # Цикл построения кривой
                        vib = math.sin(x * 0.008 + self.angle * 4 + i) * (55 * self.scales[idx] * (self.colors[idx]/255))  # Сила вибрации
                        path.lineTo(x, y_base + vib)  # Точка кривой
                    painter.drawPath(path)  # Рисуем всю струну целиком
            elif self.cur_mode == "10. Океан":  # Отрисовка Океана
                painter.setPen(Qt.NoPen)  # Отключаем обводку
                for i in range(3):  # Для каждого частотного тумана
                    if self.colors[i] < SILENCE_THRESHOLD: continue  # Пропуск тишины
                    mist_pos = QPointF(w * (0.2 + i * 0.3), h * 1.1)
                    mist_rad = (w * 0.8) * self.scales[i]  # Позиция и радиус тумана
                    grad = QRadialGradient(mist_pos, mist_rad)
                    c = [0,0,0]
                    c[i] = self.colors[i]  # Градиент облака
                    grad.setColorAt(0, QColor(*c, 180))
                    grad.setColorAt(0.5, QColor(*c, 40))
                    grad.setColorAt(1, Qt.black)  # Перелив цвета
                    painter.setBrush(grad)
                    painter.drawEllipse(mist_pos, mist_rad, mist_rad * 0.7)  # Рисуем мягкое облако тумана

        if self.kaleido:  # Проверка режима калейдоскопа
            for i in range(4):  # Повторяем отрисовку 4 раза
                p.save()
                p.translate(cx, cy)
                p.rotate(i*90)
                p.translate(-cx, -cy)
                draw_scene(p)
                p.restore()  # Поворот на 90 градусов
        else: draw_scene(p)  # Обычная отрисовка кадра
        p.end()  # Завершение рисования художника

if __name__ == "__main__":
    """
    Точка входа в приложение.

    Создаёт Qt-приложение, окно визуализатора и запускает главный цикл.

    Этот блок выполняется только при запуске скрипта напрямую:
        $ python class_Visualizer.py

    При импорте как модуль (from class_Visualizer import DiscoWindow)
    этот код не выполняется.

    Порядок запуска:
        1. Создание объекта QApplication (необходим для всех Qt-виджетов)
        2. Создание экземпляра DiscoWindow
        3. Показ окна на экране
        4. Запуск главного цикла обработки событий (app.exec())
        5. Возврат кода завершения при выходе

    Примечание:
        На некоторых системах может потребоваться указание стиля:
        >>> app.setStyle("Fusion")  # для более современного вида
    """
    app = QApplication(sys.argv)  # Создание приложения Qt
    win = DiscoWindow()
    win.show()
    sys.exit(app.exec())  # Запуск окна и цикла событий Qt






