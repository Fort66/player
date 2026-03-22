# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MainWindow.ui'
##
## Created by: Qt User Interface Compiler version 6.10.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (QApplication, QGridLayout, QHBoxLayout, QLabel,
    QListView, QMainWindow, QMenuBar, QPushButton,
    QSizePolicy, QSlider, QSpacerItem, QStackedWidget,
    QStatusBar, QVBoxLayout, QWidget)
import player_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(857, 600)
        icon = QIcon()
        icon.addFile(u":/images/videos_video_media_.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.stackedWidget = QStackedWidget(self.centralwidget)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.pagePlayList = QWidget()
        self.pagePlayList.setObjectName(u"pagePlayList")
        self.gridLayout = QGridLayout(self.pagePlayList)
        self.gridLayout.setObjectName(u"gridLayout")
        self.listView = QListView(self.pagePlayList)
        self.listView.setObjectName(u"listView")

        self.gridLayout.addWidget(self.listView, 0, 0, 1, 1)

        self.stackedWidget.addWidget(self.pagePlayList)
        self.pageVideo = QWidget()
        self.pageVideo.setObjectName(u"pageVideo")
        self.gridLayout_2 = QGridLayout(self.pageVideo)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.widgetVideo = QVideoWidget(self.pageVideo)
        self.widgetVideo.setObjectName(u"widgetVideo")

        self.gridLayout_2.addWidget(self.widgetVideo, 0, 0, 1, 1)

        self.stackedWidget.addWidget(self.pageVideo)

        self.verticalLayout.addWidget(self.stackedWidget)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)

        self.labelStart = QLabel(self.centralwidget)
        self.labelStart.setObjectName(u"labelStart")
        font = QFont()
        font.setPointSize(12)
        self.labelStart.setFont(font)

        self.horizontalLayout_2.addWidget(self.labelStart)

        self.SliderTime = QSlider(self.centralwidget)
        self.SliderTime.setObjectName(u"SliderTime")
        self.SliderTime.setMinimumSize(QSize(240, 16))
        self.SliderTime.setMaximumSize(QSize(240, 16))
        self.SliderTime.setOrientation(Qt.Orientation.Horizontal)

        self.horizontalLayout_2.addWidget(self.SliderTime)

        self.labelFinish = QLabel(self.centralwidget)
        self.labelFinish.setObjectName(u"labelFinish")
        self.labelFinish.setFont(font)

        self.horizontalLayout_2.addWidget(self.labelFinish)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_4)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButtonPrevios = QPushButton(self.centralwidget)
        self.pushButtonPrevios.setObjectName(u"pushButtonPrevios")
        self.pushButtonPrevios.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        icon1 = QIcon()
        icon1.addFile(u":/images/icons/control-skip-180.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButtonPrevios.setIcon(icon1)
        self.pushButtonPrevios.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButtonPrevios)

        self.pushButtonPlay = QPushButton(self.centralwidget)
        self.pushButtonPlay.setObjectName(u"pushButtonPlay")
        self.pushButtonPlay.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        icon2 = QIcon()
        icon2.addFile(u":/images/icons/control.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButtonPlay.setIcon(icon2)
        self.pushButtonPlay.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButtonPlay)

        self.pushButtonPause = QPushButton(self.centralwidget)
        self.pushButtonPause.setObjectName(u"pushButtonPause")
        self.pushButtonPause.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        icon3 = QIcon()
        icon3.addFile(u":/images/icons/control-pause.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButtonPause.setIcon(icon3)
        self.pushButtonPause.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButtonPause)

        self.pushButtonStop = QPushButton(self.centralwidget)
        self.pushButtonStop.setObjectName(u"pushButtonStop")
        self.pushButtonStop.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        icon4 = QIcon()
        icon4.addFile(u":/images/icons/control-stop-square.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButtonStop.setIcon(icon4)
        self.pushButtonStop.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButtonStop)

        self.pushButtonNext = QPushButton(self.centralwidget)
        self.pushButtonNext.setObjectName(u"pushButtonNext")
        self.pushButtonNext.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        icon5 = QIcon()
        icon5.addFile(u":/images/icons/control-skip.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButtonNext.setIcon(icon5)
        self.pushButtonNext.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButtonNext)

        self.pushButtonSelect = QPushButton(self.centralwidget)
        self.pushButtonSelect.setObjectName(u"pushButtonSelect")
        self.pushButtonSelect.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.pushButtonSelect.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        icon6 = QIcon()
        icon6.addFile(u":/images/icons/odata.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButtonSelect.setIcon(icon6)
        self.pushButtonSelect.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButtonSelect)

        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")
        self.label.setMinimumSize(QSize(20, 24))
        self.label.setMaximumSize(QSize(20, 24))
        self.label.setPixmap(QPixmap(u":/images/icons/speaker.png"))
        self.label.setScaledContents(False)

        self.horizontalLayout.addWidget(self.label)

        self.SliderVolume = QSlider(self.centralwidget)
        self.SliderVolume.setObjectName(u"SliderVolume")
        self.SliderVolume.setMinimumSize(QSize(51, 16))
        self.SliderVolume.setMaximumSize(QSize(51, 16))
        self.SliderVolume.setOrientation(Qt.Orientation.Horizontal)

        self.horizontalLayout.addWidget(self.SliderVolume)

        self.pushButtonColorMusic = QPushButton(self.centralwidget)
        self.pushButtonColorMusic.setObjectName(u"pushButtonColorMusic")
        icon7 = QIcon()
        icon7.addFile(u":/images/icons/color.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButtonColorMusic.setIcon(icon7)
        self.pushButtonColorMusic.setFlat(True)

        self.horizontalLayout.addWidget(self.pushButtonColorMusic)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.verticalLayout.addLayout(self.horizontalLayout)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 857, 20))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.stackedWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"\u041c\u0443\u043b\u044c\u0442\u0438\u043c\u0435\u0434\u0438\u0430 \u043f\u0440\u043e\u0438\u0433\u0440\u044b\u0432\u0430\u0442\u0435\u043b\u044c", None))
        self.labelStart.setText(QCoreApplication.translate("MainWindow", u"00:00:00", None))
        self.labelFinish.setText(QCoreApplication.translate("MainWindow", u"00:00:00", None))
#if QT_CONFIG(tooltip)
        self.pushButtonPrevios.setToolTip(QCoreApplication.translate("MainWindow", u"\u041f\u0440\u0435\u0434\u044b\u0434\u0443\u0449\u0438\u0439", None))
#endif // QT_CONFIG(tooltip)
        self.pushButtonPrevios.setText("")
#if QT_CONFIG(tooltip)
        self.pushButtonPlay.setToolTip(QCoreApplication.translate("MainWindow", u"\u0418\u0433\u0440\u0430\u0442\u044c", None))
#endif // QT_CONFIG(tooltip)
        self.pushButtonPlay.setText("")
#if QT_CONFIG(tooltip)
        self.pushButtonPause.setToolTip(QCoreApplication.translate("MainWindow", u"\u041f\u0430\u0443\u0437\u0430/\u0421\u043d\u044f\u0442\u044c \u0441 \u043f\u0430\u0443\u0437\u044b", None))
#endif // QT_CONFIG(tooltip)
        self.pushButtonPause.setText("")
#if QT_CONFIG(tooltip)
        self.pushButtonStop.setToolTip(QCoreApplication.translate("MainWindow", u"\u0421\u0442\u043e\u043f", None))
#endif // QT_CONFIG(tooltip)
        self.pushButtonStop.setText("")
#if QT_CONFIG(tooltip)
        self.pushButtonNext.setToolTip(QCoreApplication.translate("MainWindow", u"\u0421\u043b\u0435\u0434\u0443\u044e\u0449\u0438\u0439", None))
#endif // QT_CONFIG(tooltip)
        self.pushButtonNext.setText("")
#if QT_CONFIG(tooltip)
        self.pushButtonSelect.setToolTip(QCoreApplication.translate("MainWindow", u"\u0412\u044b\u0431\u0440\u0430\u0442\u044c", None))
#endif // QT_CONFIG(tooltip)
        self.pushButtonSelect.setText("")
#if QT_CONFIG(tooltip)
        self.label.setToolTip(QCoreApplication.translate("MainWindow", u"\u0413\u0440\u043e\u043c\u043a\u043e\u0441\u0442\u044c", None))
#endif // QT_CONFIG(tooltip)
        self.label.setText("")
#if QT_CONFIG(tooltip)
        self.pushButtonColorMusic.setToolTip(QCoreApplication.translate("MainWindow", u"\u0426\u0432\u0435\u0442\u043e\u043c\u0443\u0437\u044b\u043a\u0430", None))
#endif // QT_CONFIG(tooltip)
        self.pushButtonColorMusic.setText("")
    # retranslateUi

