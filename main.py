import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
from mainwindow import Mainwindow

if __name__ == '__main__':
  app = QApplication([])
  # app.setStyle('Fusion')
  
  # # dark theme
  # # palette = QPalette()
  # # palette.setColor(QPalette.Window, QColor(53, 53, 53))
  # # palette.setColor(QPalette.WindowText, Qt.white)
  # # palette.setColor(QPalette.Base, QColor(25, 25, 25))
  # # palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
  # # palette.setColor(QPalette.ToolTipBase, Qt.white)
  # # palette.setColor(QPalette.ToolTipText, Qt.white)
  # # palette.setColor(QPalette.Text, Qt.white)
  # # palette.setColor(QPalette.Button, QColor(53, 53, 53))
  # # palette.setColor(QPalette.ButtonText, Qt.white)
  # # palette.setColor(QPalette.BrightText, Qt.red)
  # # palette.setColor(QPalette.Link, QColor(42, 130, 218))
  # # palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
  # # palette.setColor(QPalette.HighlightedText, Qt.black)
  # # app.setPalette(palette)
  
  # app.setApplicationName('OCR Tester')
  win = Mainwindow()
  sys.exit(app.exec_())