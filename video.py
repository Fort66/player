import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, 
                             QHBoxLayout, QVBoxLayout, QWidget, QSlider, QFileDialog, QLabel)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import Qt, QUrl, QTime

# class VideoPlayer(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("PySide6 Media Player")
#         self.resize(800, 600)

#         # Инициализация мультимедиа компонентов
#         self.player = QMediaPlayer()
#         self.audio_output = QAudioOutput()
#         self.player.setAudioOutput(self.audio_output)
        
#         # Виджет для вывода видео
#         self.video_widget = QVideoWidget()
#         self.player.setVideoOutput(self.video_widget)

#         # Элементы управления
#         self.play_button = QPushButton("Play")
#         self.play_button.clicked.connect(self.play_video)

#         self.pause_button = QPushButton("Pause")
#         self.pause_button.clicked.connect(self.player.pause)

#         self.open_button = QPushButton("Open File")
#         self.open_button.clicked.connect(self.open_file)

#         self.slider = QSlider(Qt.Orientation.Horizontal)
#         self.slider.sliderMoved.connect(self.set_position)

#         # Привязка прогресса видео к слайдеру
#         self.player.positionChanged.connect(self.position_changed)
#         self.player.durationChanged.connect(self.duration_changed)

#         # Компоновка интерфейса (Layout)
#         controls_layout = QHBoxLayout()
#         controls_layout.addWidget(self.open_button)
#         controls_layout.addWidget(self.play_button)
#         controls_layout.addWidget(self.pause_button)
#         controls_layout.addWidget(self.slider)

#         main_layout = QVBoxLayout()
#         main_layout.addWidget(self.video_widget)
#         main_layout.addLayout(controls_layout)

#         container = QWidget()
#         container.setLayout(main_layout)
#         self.setCentralWidget(container)

#     def open_file(self):
#         file_dialog = QFileDialog(self)
#         file_path, _ = file_dialog.getOpenFileName(self, "Выберите видео")
#         if file_path:
#             self.player.setSource(QUrl.fromLocalFile(file_path))
#             self.play_video()

#     def play_video(self):
#         if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
#             return
#         self.player.play()

#     def position_changed(self, position):
#         self.slider.setValue(position)

#     def duration_changed(self, duration):
#         self.slider.setRange(0, duration)

#     def set_position(self, position):
#         self.player.setPosition(position)

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = VideoPlayer()
#     window.show()
#     sys.exit(app.exec())
    
    
    
class VideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 Media Player Pro")
        self.resize(900, 600)

        # Мультимедиа компоненты
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        self.video_widget = QVideoWidget()
        self.player.setVideoOutput(self.video_widget)

        # Элементы управления
        self.btn_open = QPushButton("Открыть")
        self.btn_open.clicked.connect(self.open_file)

        self.btn_play = QPushButton("Play/Pause")
        self.btn_play.clicked.connect(self.toggle_play)

        # Слайдер времени и метка времени
        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_slider.sliderMoved.connect(self.set_position)

        self.label_time = QLabel("00:00:00 / 00:00:00")

        # Слайдер громкости
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.audio_output.setVolume(0.7) # Громкость от 0.0 до 1.0
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(self.set_volume)

        # Сигналы плеера
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)

        # Компоновка (Layout)
        controls = QHBoxLayout()
        controls.addWidget(self.btn_open)
        controls.addWidget(self.btn_play)
        controls.addWidget(self.time_slider)
        controls.addWidget(self.label_time)
        controls.addWidget(QLabel("Громкость:"))
        controls.addWidget(self.volume_slider)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.video_widget)
        main_layout.addLayout(controls)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выбрать файл")
        if path:
            self.player.setSource(QUrl.fromLocalFile(path))
            self.player.play()

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def set_volume(self, volume):
        self.audio_output.setVolume(volume / 100)

    def set_position(self, position):
        self.player.setPosition(position)

    def update_position(self, position):
        self.time_slider.setValue(position)
        self.update_duration_label(position, self.player.duration())

    def update_duration(self, duration):
        self.time_slider.setRange(0, duration)
        self.update_duration_label(self.player.position(), duration)

    def update_duration_label(self, current, total):
        curr_time = QTime(0, 0).addMSecs(current).toString("hh:mm:ss")
        total_time = QTime(0, 0).addMSecs(total).toString("hh:mm:ss")
        self.label_time.setText(f"{curr_time} / {total_time}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoPlayer()
    window.show()
    sys.exit(app.exec())