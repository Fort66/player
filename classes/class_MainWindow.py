"""
Главное окно медиаплеера с визуализацией.

Модуль отвечает за:
    - Воспроизведение аудио и видео файлов
    - Управление плейлистом (добавление, удаление, навигация)
    - Отображение окна визуализации (DiscoWindow)
    - Синхронизацию визуализации с аудио через AudioAnalysisThread

Возможности:
    - Воспроизведение аудио: MP3, WAV, OGG, FLAC, M4A, WMA, AAC
    - Воспроизведение видео
    - Плейлист с возможностью удаления (клавиша Delete)
    - Управление воспроизведением (play, pause, stop, prev, next)
    - Ползунок позиции воспроизведения
    - Ползунок громкости
    - Окно визуализации с 10 режимами

Требования:
    - Python 3.8+
    - PySide6
    - Модуль UI_MainWindow из screens/py_screens
    - Модуль class_Visualizer

Пример использования:
    >>> from PySide6.QtWidgets import QApplication
    >>> import sys
    >>> app = QApplication(sys.argv)
    >>> win = MenuWindow()
    >>> win.show()
    >>> sys.exit(app.exec())
"""

from PySide6.QtWidgets import QMainWindow, QFileDialog, QMenu
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QStringListModel, Qt, QTime, QUrl, QSize
from PySide6.QtGui import QKeyEvent, QAction, QIcon

from screens.py_screens.UI_MainWindow import Ui_MainWindow
from classes.class_Visualizer import AudioAnalysisThread, DiscoWindow


# ============================================================================
# КОНСТАНТЫ НАСТРОЕК
# ============================================================================

# Настройки громкости
DEFAULT_VOLUME = 0.5          # Громкость по умолчанию (0.0 - 1.0)
VOLUME_MIN = 0                # Минимальное значение ползунка громкости
VOLUME_MAX = 100              # Максимальное значение ползунка громкости
VOLUME_DEFAULT = 50           # Значение ползунка громкости по умолчанию

# Настройки навигации по видео (перемотка)
VIDEO_REWIND_BACK = -20000    # Перемотка назад при отсутствии плейлиста (мс)
VIDEO_REWIND_FORWARD = 20000   # Перемотка вперёд при отсутствии плейлиста (мс)

# Фильтры файлов
AUDIO_FILE_FILTER = 'Audio files (*.mp3 *.wav *.ogg *.flac *.m4a *.wma *.aac)'
VIDEO_FILE_FILTER = 'Video files (*.mp4 *.avi *.mkv *.mov *.wmv)'

# Текстовые константы
TIME_FORMAT_PLAYLIST = 'mm:ss'    # Формат времени для плейлиста (минуты:секунды)
TIME_FORMAT_VIDEO = 'hh:mm:ss'    # Формат времени для видео (часы:минуты:секунды)
DEFAULT_TIME_LABEL = '00:00'


class MenuWindow(QMainWindow, Ui_MainWindow):
    """
    Главное окно медиаплеера.

    Наследует QMainWindow и Ui_MainWindow (сгенерированный из .ui файла).
    Управляет воспроизведением медиа, плейлистом и окном визуализации.

    Атрибуты:
        disco_window (DiscoWindow): Окно визуализации или None
        audio_thread (AudioAnalysisThread): Поток анализа аудио или None
        player (QMediaPlayer): Объект медиаплеера Qt
        audio_output (QAudioOutput): Выход аудио
        file_urls (list): Список путей к файлам плейлиста
        current_index (int): Индекс текущего файла (-1 если ничего не играет)
        playlist_model (QStringListModel): Модель данных для списка файлов
        is_tracking (bool): Флаг, удерживает ли пользователь ползунок времени

    Управление:
        - Delete: удалить выбранный файл из плейлиста
        - Правый клик на кнопку "Выбрать": добавить аудио или видео
    """
    def __init__(self, *args, **kwargs):
        """
        Инициализирует главное окно медиаплеера.

        Выполняет:
            1. Настройку UI из .ui файла (setupUi)
            2. Создание объектов визуализации (DiscoWindow, AudioAnalysisThread)
            3. Создание меню выбора файлов
            4. Настройку мультимедиа-компонентов (плеер, аудиовыход)
            5. Создание модели данных плейлиста
            6. Подключение модели к списку файлов
            7. Настройку ползунков (время, громкость)
            8. Подключение сигналов кнопок
            9. Запуск окна визуализации

        Примечание:
            Окно визуализации создаётся сразу при запуске, но скрыто.
            Отображается при первом вызове start_visualization().
        """
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        # Иконки для кнопок навигации (аудио и видео режимы)
        # Используются для переключения между режимами плейлиста и видео
        self.icon_previos_audio = self.icon_previos_video = QIcon()
        self.icon_next_audio = self.icon_next_video = QIcon()

        # Окно визуализации и поток анализа аудио (создаются лениво)
        self.disco_window = None
        self.audio_thread = None

        # Последовательная инициализация компонентов
        self.set_icon_buttons_navigation()
        self.create_select_menu()          # Меню выбора файлов
        self.set_multimedia_components()   # Плеер и аудиовыход
        self.create_data_model()           # Модель плейлиста
        self.connecting_model_to_list()    # Подключение модели к listView
        self.settings_slider_time()        # Ползунок времени
        self.settings_slider_volume()      # Ползунок громкости
        self.connect_signals()             # Сигналы кнопок

        # Запуск визуализации (окно будет показано)
        self.visualization()

    def set_icon_buttons_navigation(self):
        """
        Устанавливает иконки на кнопки навигации в зависимости от режима.

        Режим плейлиста (pagePlayList):
            - Предыдущий: control-skip-180.png (перемотка назад по трекам)
            - Следующий: control-skip.png (перемотка вперёд по трекам)

        Режим видео (pageVideo):
            - Предыдущий: control-double-180.png (перемотка назад по времени)
            - Следующий: control-double.png (перемотка вперёд по времени)

        Примечание:
            Иконки загружаются из ресурсов Qt (://images/icons/...).
            Этот метод вызывается при переключении между страницами.
        """
        if self.stackedWidget.currentWidget() == self.pagePlayList:
            # Режим плейлиста: иконки перемотки треков
            self.pushButtonPrevios.setIcon(QIcon(':/images/icons/control-skip-180.png'))
            self.pushButtonNext.setIcon(QIcon(':/images/icons/control-skip.png'))
        else:
            # Режим видео: иконки перемотки времени
            self.pushButtonPrevios.setIcon(QIcon(':/images/icons/control-double-180.png'))
            self.pushButtonNext.setIcon(QIcon(':/images/icons/control-double.png'))

    def visualization(self):
        """
        Создаёт (лениво) объекты визуализации при первом вызове.

        Этот метод вызывается один раз в __init__ для создания:
            - DiscoWindow: окно визуализации
            - AudioAnalysisThread: поток анализа аудио

        Связь сигналов:
            audio_thread.data_signal -> disco_window.update_data
            (поток передаёт данные о частотах, окно обновляет визуализацию)

        Примечание:
            Метод создаёт объекты только один раз при первом вызове.
            Последующие вызовы не создают новые объекты (проверка в start_visualization).
        """
        if not self.disco_window:
            # Создаём окно визуализации
            self.disco_window = DiscoWindow()
            # Создаём поток анализа аудио
            self.audio_thread = AudioAnalysisThread()
            # Подключаем сигнал данных от потока к слоту обновления окна
            self.audio_thread.data_signal.connect(self.disco_window.update_data)

    def start_visualization(self):
        """
        Переключает видимость окна визуализации.

        Вызывается при нажатии кнопки "Визуализация" (pushButtonColorMusic).

        Логика:
            - Если окно видимо: скрывает его и останавливает поток анализа
            - Если окно скрыто: показывает его и запускает/перезапускает поток

        Остановка потока:
            - Устанавливает audio_thread.is_running = False
            - Окно скрывается методом hide()

        Запуск потока:
            - Устанавливает audio_thread.is_running = True
            - Запускает поток методом start()

        Примечание:
            Поток не пересоздаётся, а перезапускается. Это позволяет
            избежать задержек при частом переключении визуализации.
        """
        if self.disco_window.isVisible():
            # Окно видно - скрываем и останавливаем поток
            self.audio_thread.is_running = False
            self.disco_window.hide()
        else:
            # Окно скрыто - показываем и запускаем поток
            self.audio_thread.is_running = True
            self.disco_window.show()
            self.audio_thread.start()

    def create_select_menu(self):
        """
        Создаёт выпадающее меню на кнопке выбора файлов.

        Создаёт QMenu с двумя пунктами:
            - "Аудио": открывает диалог выбора аудиофайлов
            - "Видео": открывает диалог выбора видеофайла

        Меню привязывается к кнопке pushButtonSelect через setMenu().
        """
        self.menu = QMenu(self.pushButtonSelect)

        # Пункт меню "Аудио"
        actionAudio = QAction("Аудио", self)
        actionAudio.triggered.connect(self.add_audio_files)

        # Пункт меню "Видео"
        actionVideo = QAction("Видео", self)
        actionVideo.triggered.connect(self.add_video_file)

        self.menu.addActions([actionAudio, actionVideo])
        # Привязываем меню к кнопке
        self.pushButtonSelect.setMenu(self.menu)

    def set_multimedia_components(self):
        """
        Инициализирует мультимедиа-компоненты плеера.

        Создаёт и настраивает:
            - QMediaPlayer: основной плеер для аудио/видео
            - QAudioOutput: аудиовыход с настраиваемой громкостью
            - widgetVideo: виджет для вывода видео

        Громкость по умолчанию: 50% (0.5)
        """
        # Основной плеер
        self.player = QMediaPlayer()

        # Аудиовыход
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        # Видеовыход (виджет из UI)
        self.player.setVideoOutput(self.widgetVideo)

        # Установка громкости по умолчанию
        self.audio_output.setVolume(DEFAULT_VOLUME)

    def create_data_model(self):
        """
        Создаёт модель данных для плейлиста.

        Атрибуты:
            file_urls (list): Список полных путей к файлам
            current_index (int): Индекс текущего файла (-1 = ничего не выбрано)
            playlist_model (QStringListModel): Модель для отображения в listView

        Примечание:
            QStringListModel - стандартная модель Qt для простых текстовых списков.
        """
        self.file_urls = []                 # Список путей к файлам
        self.current_index = -1             # Индекс текущего файла
        self.playlist_model = QStringListModel()  # Модель для listView

    def connecting_model_to_list(self):
        """
        Подключает модель данных к представлению списка.

        Настраивает:
            - listView: отображает файлы из playlist_model
            - doubleClicked: воспроизведение при двойном клике
            - clicked: установка индекса при одинарном клике
            - eventFilter: обработка клавиши Delete

        eventFilter нужен для перехвата событий клавиатуры в listView,
        поскольку стандартный keyPressEvent не всегда срабатывает для виджетов.
        """
        # Подключаем модель к представлению
        self.listView.setModel(self.playlist_model)

        # Двойной клик - воспроизведение файла
        self.listView.doubleClicked.connect(self.play_from_list)

        # Одинарный клик - установка индекса
        self.listView.clicked.connect(self.set_index_on_click)

        # Установка фильтра событий для обработки Delete
        self.listView.installEventFilter(self)

    def settings_slider_time(self):
        """
        Настраивает ползунок времени воспроизведения.

        Инициализация:
            - is_tracking = False (пользователь не двигает ползунок)
            - Метки времени устанавливаются в '00:00'

        Подключение сигналов:
            - sliderPressed: пользователь начал двигать ползунок
            - sliderReleased: пользователь отпустил ползунок
            - positionChanged: обновление позиции (во время воспроизведения)
            - durationChanged: обновление диапазона ползунка
            - mediaStatusChanged: проверка окончания воспроизведения

        Логика is_tracking:
            Когда пользователь двигает ползунок, не нужно обновлять его
            значение из плеера (иначе будет "прыгать"). Флаг блокирует
            обновление до тех пор, пока пользователь не отпустит ползунок.
        """
        # Флаг отслеживания взаимодействия пользователя с ползунком
        self.is_tracking = False

        # Установка начальных значений времени
        self.labelStart.setText(DEFAULT_TIME_LABEL)
        self.labelFinish.setText(DEFAULT_TIME_LABEL)

        # Подключение сигналов ползунка
        self.SliderTime.sliderPressed.connect(self.slider_pressed)
        self.SliderTime.sliderReleased.connect(self.slider_released)

        # Подключение сигналов плеера
        self.player.positionChanged.connect(self.update_slider_position)    # Позиция изменилась
        self.player.durationChanged.connect(self.update_slider_range)        # Длительность изменилась
        self.player.mediaStatusChanged.connect(self.check_status)            # Статус изменился

    def settings_slider_volume(self):
        """
        Настраивает ползунок громкости.

        Диапазон: 0-100
        Значение по умолчанию: 50

        Примечание:
            Внутреннее значение громкости плеера 0.0-1.0,
            поэтому при установке и чтении используется деление/умножение на 100.
        """
        self.SliderVolume.setRange(VOLUME_MIN, VOLUME_MAX)
        self.SliderVolume.setValue(VOLUME_DEFAULT)

    def connect_signals(self):
        """
        Подключает сигналы кнопок управления воспроизведением.

        Кнопки:
            - pushButtonPrevios: предыдущий файл
            - pushButtonPlay: воспроизведение
            - pushButtonPause: пауза/возобновление
            - pushButtonStop: остановка
            - pushButtonNext: следующий файл

        Также подключается ползунок громкости.
        """
        # Кнопки навигации по файлам
        self.pushButtonPrevios.clicked.connect(self.previos_file)
        self.pushButtonPlay.clicked.connect(self.play_file)
        self.pushButtonPause.clicked.connect(self.pause_file)
        self.pushButtonStop.clicked.connect(self.stop_file)
        self.pushButtonNext.clicked.connect(self.next_file)
        self.pushButtonColorMusic.clicked.connect(self.start_visualization)

        # Ползунок громкости
        self.SliderVolume.valueChanged.connect(self.change_volume)

    def keyPressEvent(self, event: QKeyEvent):
        """
        Обрабатывает нажатия клавиш клавиатуры.

        Обрабатывает Delete:
            - Получает текущий выбранный элемент списка
            - Удаляет файл из file_urls и плейлиста
            - Если удалён играющий трек - останавливает плеер
            - Корректирует current_index если нужно

        Аргументы:
            event: Событие нажатия клавиши

        Примечание:
            Вызов super().keyPressEvent(event) в конце обязателен
            для обработки других клавиш системой.
        """
        if event.key() == Qt.Key.Key_Delete:
            selected = self.listView.currentIndex()
            if selected.isValid():
                row = selected.row()
                # Удаляем из списка путей и из модели
                self.file_urls.pop(row)
                self.playlist_model.removeRow(row)

                # Если удален играющий трек
                if row == self.current_index:
                    self.player.stop()
                    self.current_index = -1
                # Если удаленный индекс меньше текущего - уменьшаем индекс
                elif row < self.current_index:
                    self.subtract_index()

            # Обновляем визуальное выделение в списке
            self.list_view_update()

        # Вызов родительского обработчика для других клавиш
        super().keyPressEvent(event)

    def list_view_update(self):
        """
        Обновляет визуальное выделение в списке плейлиста.

        Устанавливает текущий индекс в listView на позицию current_index.
        Вызывается после изменения текущего файла или удаления файлов.
        """
        self.listView.setCurrentIndex(self.playlist_model.index(self.current_index))

    # -------------------------------------------------------------------------
    # Методы работы с ползунком времени
    # -------------------------------------------------------------------------

    def slider_pressed(self):
        """
        Обработка начала перетаскивания ползунка.

        Устанавливает флаг is_tracking = True, чтобы заблокировать
        автоматическое обновление позиции плеером во время перетаскивания.
        """
        self.is_tracking = True

    def slider_released(self, value=0):
        """
        Обработка отпускания ползунка.

        Устанавливает позицию воспроизведения на значение ползунка
        плюс необязательное смещение (value).

        Аргументы:
            value: Смещение в миллисекундах (для перемотки видео)

        Примечание:
            После установки позиции сбрасывается флаг is_tracking,
            чтобы плеер снова мог обновлять положение ползунка.
        """
        self.player.setPosition(self.SliderTime.value() + value)
        self.is_tracking = False

    def update_slider_position(self, pos):
        """
        Обновляет положение ползунка и метки времени.

        Вызывается при изменении позиции воспроизведения плеером.
        Обновляет ползунок только если пользователь его не перемещает.

        Аргументы:
            pos: Текущая позиция в миллисекундах
        """
        if not self.is_tracking:
            # Обновляем ползунок (только если пользователь не двигает)
            self.SliderTime.setValue(pos)

        # Обновляем метки времени
        self.update_time_label(pos)

    def update_slider_range(self, duration):
        """
        Обновляет диапазон ползунка времени.

        Вызывается при загрузке нового файла для установки
        максимального значения ползунка равным длительности трека.

        Аргументы:
            duration: Длительность файла в миллисекундах
        """
        self.SliderTime.setRange(0, duration)

    def update_time_label(self, pos):
        """
        Обновляет метки текущего времени и общей длительности.

        Формат времени зависит от текущей страницы:
            - Плейлист: mm:ss (минуты:секунды)
            - Видео: hh:mm:ss (часы:минуты:секунды)

        Аргументы:
            pos: Текущая позиция в миллисекундах
        """
        # Выбор формата времени в зависимости от режима
        if self.stackedWidget.currentWidget() == self.pagePlayList:
            format_time = TIME_FORMAT_PLAYLIST
        else:
            format_time = TIME_FORMAT_VIDEO

        # Форматирование текущей позиции
        curr = QTime(0, 0).addMSecs(pos).toString(format_time)
        # Форматирование общей длительности
        total = QTime(0, 0).addMSecs(self.player.duration()).toString(format_time)

        # Обновление меток
        self.labelStart.setText(curr)
        self.labelFinish.setText(total)

    # -------------------------------------------------------------------------
    # Методы управления громкостью
    # -------------------------------------------------------------------------

    def change_volume(self, value):
        """
        Изменяет громкость воспроизведения.

        Преобразует значение ползунка (0-100) во внутреннее
        значение громкости плеера (0.0-1.0).

        Аргументы:
            value: Значение ползунка громкости (0-100)
        """
        self.audio_output.setVolume(value / 100)

    # -------------------------------------------------------------------------
    # Методы добавления файлов
    # -------------------------------------------------------------------------

    def add_audio_files(self):
        """
        Открывает диалог выбора аудиофайлов.

        Переключает интерфейс на страницу плейлиста.
        Позволяет выбрать несколько файлов (MP3, WAV, OGG, FLAC, M4A, WMA, AAC).

        Добавленные файлы:
            - Добавляются в file_urls
            - Отображаются в listView через playlist_model
            - Показываются только имена файлов (без пути)
        """
        # Переключаем на страницу плейлиста
        self.stackedWidget.setCurrentWidget(self.pagePlayList)
        self.set_icon_buttons_navigation()

        # Открытие диалога выбора файлов
        files, _ = QFileDialog.getOpenFileNames(
            self,
            'Выбор музыки',
            '',
            AUDIO_FILE_FILTER
        )

        if files:
            # Добавление файлов в список
            self.file_urls.extend(files)

            # Обновление модели списком имён файлов
            self.playlist_model.setStringList([f.split('/')[-1] for f in self.file_urls])

    def add_video_file(self):
        """
        Открывает диалог выбора видеофайла.

        Переключает интерфейс на страницу видео.
        Позволяет выбрать один видеофайл.

        После выбора файл автоматически начинает воспроизводиться.
        """
        # Переключаем на страницу видео
        self.stackedWidget.setCurrentWidget(self.pageVideo)
        self.set_icon_buttons_navigation()

        # Открытие диалога выбора файла
        path, _ = QFileDialog.getOpenFileName(self, "Выбрать файл", "", VIDEO_FILE_FILTER)

        if path:
            # Установка источника и воспроизведение
            self.player.setSource(QUrl.fromLocalFile(path))
            self.player.play()

    # -------------------------------------------------------------------------
    # Методы воспроизведения
    # -------------------------------------------------------------------------

    def play_from_list(self, index):
        """
        Начинает воспроизведение файла из плейлиста по индексу.

        Вызывается при двойном клике на элемент списка.

        Аргументы:
            index: QModelIndex выбранного элемента

        Процесс:
            1. Устанавливает current_index = index.row()
            2. Вызывает play_current() для воспроизведения
        """
        self.current_index = index.row()
        self.play_current()

    def play_current(self):
        """
        Воспроизводит текущий файл из плейлиста.

        Проверяет, что current_index в пределах списка file_urls,
        затем устанавливает источник и запускает воспроизведение.

        Обновляет визуальное выделение в списке после старта.
        """
        if 0 <= self.current_index < len(self.file_urls):
            # Установка источника
            self.player.setSource(QUrl.fromLocalFile(self.file_urls[self.current_index]))
            # Воспроизведение
            self.player.play()
            # Обновление выделения в списке
            self.list_view_update()

    def play_file(self):
        """
        Обработка нажатия кнопки Play.

        Логика:
            - Если плеер пуст и есть файлы в плейлисте:
                - Если current_index = -1, устанавливает 0
                - Воспроизводит текущий файл
            - Иначе: просто продолжает воспроизведение (play() без параметров)

        Примечание:
            player.play() без источника продолжает воспроизведение
            текущего источника после паузы.
        """
        # Если источник не установлен, но есть плейлист
        if self.player.source().isEmpty() and self.file_urls:
            if self.current_index < 0:
                self.current_index = 0
            self.play_current()
        elif self.player.playbackState() == self.player.PlaybackState.PausedState:
            # Продолжить воспроизведение (после паузы)
            self.player.play()
        elif self.current_index != -1:
            self.play_current()


    def check_status(self, status):
        """
        Проверяет статус медиа и обрабатывает окончание воспроизведения.

        При достижении конца файла (EndOfMedia):
            - Переходит к следующему файлу (add_index)
            - Автоматически начинает воспроизведение (play_current)

        Аргументы:
            status: Текущий статус медиа (MediaStatus)
        """
        if status == self.player.MediaStatus.EndOfMedia:
            self.add_index()
            self.play_current()

    def pause_file(self):
        """
        Переключает состояние паузы.

        Логика:
            - Если играет -> ставит на паузу
            - Если на паузе -> возобновляет воспроизведение
        """
        if self.player.playbackState() == self.player.PlaybackState.PlayingState:
            self.player.pause()
        elif self.player.playbackState() == self.player.PlaybackState.PausedState:
            self.player.play()

    def stop_file(self):
        """
        Останавливает воспроизведение.

        Сбрасывает позицию на начало и останавливает плеер.
        """
        self.player.stop()

    # -------------------------------------------------------------------------
    # Методы навигации по плейлисту
    # -------------------------------------------------------------------------

    def previos_file(self):
        """
        Обработка нажатия кнопки "Предыдущий файл".

        Режим плейлиста:
            - Останавливает текущее воспроизведение
            - Переходит к предыдущему файлу
            - Воспроизводит его (если есть)

        Режим видео:
            - Перематывает на 20 секунд назад
        """
        if self.stackedWidget.currentWidget() == self.pagePlayList:
            self.stop_file()
            self.subtract_index()
            if self.current_index >= 0:
                self.play_current()
            self.list_view_update()
        else:
            # Перемотка видео назад
            self.slider_released(VIDEO_REWIND_BACK)

    def next_file(self):
        """
        Обработка нажатия кнопки "Следующий файл".

        Режим плейлиста:
            - Останавливает текущее воспроизведение
            - Переходит к следующему файлу
            - Воспроизводит его (если есть)

        Режим видео:
            - Перематывает на 20 секунд вперёд
        """
        if self.stackedWidget.currentWidget() == self.pagePlayList:
            self.stop_file()
            self.add_index()
            if self.current_index >= 0:
                self.play_current()
            self.list_view_update()
        else:
            # Перемотка видео вперёд
            self.slider_released(VIDEO_REWIND_FORWARD)

    def add_index(self):
        """
        Увеличивает индекс текущего файла.

        Если это был последний файл в плейлисте:
            - Устанавливает current_index = -1
            - Останавливает плеер
            - Очищает источник

        Иначе просто увеличивает индекс на 1.
        """
        if self.current_index + 1 < len(self.file_urls):
            self.current_index += 1
        else:
            # Достигнут конец плейлиста
            self.current_index = -1
            self.player.stop()
            self.player.setSource(QUrl())

    def subtract_index(self):
        """
        Уменьшает индекс текущего файла.

        Если current_index > 0: уменьшает на 1.

        Если current_index = 0:
            - Устанавливает current_index = -1
            - Останавливает плеер
            - Очищает источник
        """
        if self.current_index > 0:
            self.current_index -= 1
        else:
            # Был на первом файле
            self.current_index = -1
            self.player.stop()
            self.player.setSource(QUrl())

    def set_index_on_click(self, index):
        """
        Устанавливает индекс текущего файла при клике в списке.

        Вызывается при одинарном клике на элемент плейлиста.
        Позволяет визуально выбрать файл без немедленного воспроизведения.

        Аргументы:
            index: QModelIndex выбранного элемента
        """
        self.current_index = index.row()