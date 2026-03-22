import sys
import os

# Добавляем путь этой папки в начало списка поиска модулей
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.insert(0, path)

from . import player_rc