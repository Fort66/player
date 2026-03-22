from PySide6.QtWidgets import QApplication, QPushButton, QMenu
from PySide6.QtGui import QAction

app = QApplication([])

button = QPushButton("Нажми меня (ЛКМ)")

# 1. Создаем объект меню
menu = QMenu()

# 2. Создаем и добавляем действия (Actions) в меню
action1 = QAction("Настройка 1", button)
action1.triggered.connect(lambda: print("Выбрана настройка 1"))

action2 = QAction("Настройка 2", button)
action2.triggered.connect(lambda: print("Выбрана настройка 2"))

menu.addActions([action1, action2])

# 3. Привязываем меню к кнопке
button.setMenu(menu)

button.show()
app.exec()