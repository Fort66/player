from PySide6.QtCore import QTranslator, QLibraryInfo, QLocale
from PySide6.QtWidgets import QApplication

from icecream import ic

import sys

from classes.class_MainWindow import MenuWindow


def main():
    app = QApplication(sys.argv)
    translator = QTranslator(app)
    path = QLibraryInfo.path(QLibraryInfo.TranslationsPath)

    if translator.load(QLocale('ru_RU'), 'qtbase', '_', path):
        app.installTranslator(translator)

    window = MenuWindow()
    window.show()
    app.exec()