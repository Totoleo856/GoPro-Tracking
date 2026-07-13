from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QTabWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QLineEdit,
    QFormLayout,
    QMessageBox,
    QHBoxLayout,
    QComboBox,
)
from PyQt6.QtGui import QDoubleValidator

from calibration import Calibration
from tracking import Tracker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("GoPro Cinema Tracker")
        self.resize(900, 600)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.create_calibration_tab()
        self.create_tracking_tab()
        self.create_verification_tab()

    def browse_file(self, line_edit, filter="All Files (*)"):
        file_path, _ = QFileDialog.getOpenFileName(self, "Choisir un fichier", "", filter)
        if file_path:
            line_edit.setText(file_path)

    def create_file_row(self, line_edit, button_text="Parcourir", filter="All Files (*)"):
        row_widget = QWidget()
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(line_edit)

        browse_button = QPushButton(button_text)
        browse_button.clicked.connect(lambda: self.browse_file(line_edit, filter))
        row_layout.addWidget(browse_button)

        row_widget.setLayout(row_layout)
        return row_widget

    def create_calibration_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        form = QFormLayout()

        self.gopro_model = QLineEdit()
        self.cinema_calibration_video = QLineEdit()
        self.gopro_calibration_video = QLineEdit()
        self.offset_up = QLineEdit()
        self.offset_forward = QLineEdit()
        self.offset_left = QLineEdit()
        self.focal_length = QLineEdit()
        self.sensor_size = QLineEdit()
        self.resolution = QLineEdit()
        self.aruco_dictionary = QComboBox()
        self.aruco_dictionary.addItems(
            [
                "DICT_4X4_50",
                "DICT_5X5_100",
                "DICT_6X6_250",
                "DICT_7X7_1000",
            ]
        )

        validator = QDoubleValidator()
        self.offset_up.setValidator(validator)
        self.offset_forward.setValidator(validator)
        self.offset_left.setValidator(validator)
        self.focal_length.setValidator(validator)
        self.sensor_size.setValidator(validator)

        self.resolution.setPlaceholderText("1920x1080")

        form.addRow("Modèle GoPro", self.gopro_model)
        form.addRow(
            "Vidéo caméra cinéma + ArUco",
            self.create_file_row(
                self.cinema_calibration_video,
                "Parcourir",
                "Vidéos (*.mp4 *.mov *.avi);;Tous les fichiers (*)",
            ),
        )
        form.addRow(
            "Vidéo GoPro + ArUco",
            self.create_file_row(
                self.gopro_calibration_video,
                "Parcourir",
                "Vidéos (*.mp4 *.mov *.avi);;Tous les fichiers (*)",
            ),
        )
        form.addRow("Offset Up", self.offset_up)
        form.addRow("Offset Forward", self.offset_forward)
        form.addRow("Offset Left", self.offset_left)
        form.addRow("Focale caméra cinéma", self.focal_length)
        form.addRow("Taille capteur", self.sensor_size)
        form.addRow("Résolution", self.resolution)
        form.addRow("Cible ArUco", self.aruco_dictionary)

        layout.addLayout(form)

        calibrate_button = QPushButton("CALIBRATE")
        calibrate_button.clicked.connect(self.run_calibration)
        layout.addWidget(calibrate_button)

        widget.setLayout(layout)
        self.tabs.addTab(widget, "Calibration")

    def parse_resolution(self, text):
        if "x" not in text:
            raise ValueError(
                "La résolution doit être au format largeurxhauteur, par exemple 1920x1080."
            )
        width_str, height_str = text.lower().split("x", 1)
        return int(width_str.strip()), int(height_str.strip())

    def run_calibration(self):
        try:
            offset = {
                "up": float(self.offset_up.text()),
                "forward": float(self.offset_forward.text()),
                "left": float(self.offset_left.text()),
            }
            focal = float(self.focal_length.text())
            sensor = float(self.sensor_size.text())
            resolution = self.parse_resolution(self.resolution.text())
        except ValueError as exc:
            QMessageBox.warning(self, "Erreur de saisie", str(exc))
            return

        calibration = Calibration(
            gopro_model=self.gopro_model.text(),
            cinema_video=self.cinema_calibration_video.text(),
            gopro_video=self.gopro_calibration_video.text(),
            offset=offset,
            camera={
                "focal": focal,
                "sensor": sensor,
                "resolution": resolution,
            },
            aruco_dict=self.aruco_dictionary.currentText(),
        )

        try:
            output_path = calibration.compute()
        except Exception as exc:
            QMessageBox.critical(self, "Erreur de calibration", str(exc))
            return

        QMessageBox.information(
            self,
            "Calibration terminée",
            f"Calibration générée :\n{output_path}",
        )

    def create_tracking_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.capture_video = QLineEdit()
        self.calibration_file = QLineEdit()

        layout.addWidget(QLabel("Vidéo capture GoPro"))
        layout.addWidget(
            self.create_file_row(
                self.capture_video,
                "Parcourir",
                "Vidéos (*.mp4 *.mov *.avi);;Tous les fichiers (*)",
            )
        )

        layout.addWidget(QLabel("Fichier calibration JSON"))
        layout.addWidget(
            self.create_file_row(
                self.calibration_file,
                "Parcourir",
                "JSON (*.json);;Tous les fichiers (*)",
            )
        )

        tracking_button = QPushButton("TRACKING")
        tracking_button.clicked.connect(self.run_tracking)
        layout.addWidget(tracking_button)

        widget.setLayout(layout)
        self.tabs.addTab(widget, "Tracking")

    def run_tracking(self):
        capture_path = self.capture_video.text()
        calibration_path = self.calibration_file.text()

        if not capture_path or not calibration_path:
            QMessageBox.warning(
                self,
                "Entrée manquante",
                "Veuillez sélectionner la vidéo GoPro et le fichier de calibration.",
            )
            return

        try:
            tracker = Tracker(capture_path, calibration_path)
            output_path = tracker.run()
        except Exception as exc:
            QMessageBox.critical(self, "Erreur de tracking", str(exc))
            return

        QMessageBox.information(
            self,
            "Tracking terminé",
            f"Fichier tracking généré :\n{output_path}",
        )

    def create_verification_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.tracking_result_file = QLineEdit()

        layout.addWidget(QLabel("Chargement tracking + visualisation 3D + export"))
        layout.addWidget(
            self.create_file_row(
                self.tracking_result_file,
                "Parcourir",
                "Résultats tracking (*.json *.csv);;Tous les fichiers (*)",
            )
        )

        verify_button = QPushButton("VÉRIFIER / EXPORTER")
        verify_button.clicked.connect(self.run_verification)
        layout.addWidget(verify_button)

        widget.setLayout(layout)
        self.tabs.addTab(widget, "Vérification et Export")

    def run_verification(self):
        result_path = self.tracking_result_file.text()

        if not result_path:
            QMessageBox.warning(
                self,
                "Entrée manquante",
                "Veuillez sélectionner un fichier de résultat de tracking.",
            )
            return

        QMessageBox.information(
            self,
            "Vérification et Export",
            f"Fichier de résultat sélectionné :\n{result_path}",
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
