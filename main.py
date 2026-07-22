import sys

from PyQt6.QtCore import QLocale
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from app_paths import resource_path
from main_window import MainWindow


if __name__ == "__main__":
    # Force le point "." comme séparateur décimal partout dans l'app, quelle que
    # soit la locale régionale de la machine (une locale utilisant la virgule
    # bloquerait sinon la saisie de "." dans les champs numériques validés par
    # QDoubleValidator).
    QLocale.setDefault(QLocale(QLocale.Language.C))

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(resource_path("assets/Icone.png"))))

    window = MainWindow()
    window.setWindowIcon(QIcon(str(resource_path("assets/Icone.png"))))
    window.show()

    sys.exit(app.exec())
