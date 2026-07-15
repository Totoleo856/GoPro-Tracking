import sys

from PyQt6.QtCore import QLocale
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow


if __name__ == "__main__":
    # Force le point "." comme séparateur décimal partout dans l'app, quelle que
    # soit la locale régionale de la machine (une locale utilisant la virgule
    # bloquerait sinon la saisie de "." dans les champs numériques validés par
    # QDoubleValidator).
    QLocale.setDefault(QLocale(QLocale.Language.C))

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
