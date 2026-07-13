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
from PyQt6.QtGui import QDoubleValidator, QIntValidator

from calibration import Calibration
from tracking import Tracker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GoPro Cinema Tracker")
        self.resize(900, 640)
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
        self.resolution_x = QLineEdit()
        self.resolution_y = QLineEdit()

        self.charuco_squares_x = QLineEdit("5")
        self.charuco_squares_y = QLineEdit("7")
        self.charuco_square_length = QLineEdit("0.04")
        self.charuco_marker_length = QLineEdit("0.03")
        self.charuco_dictionary = QComboBox()
        self.charuco_dictionary.addItems(
            ["DICT_4X4_50", "DICT_5X5_100", "DICT_6X6_250", "DICT_7X7_1000"]
        )
        self.charuco_dictionary.setCurrentText("DICT_6X6_250")

        validator_float = QDoubleValidator()
        validator_int = QIntValidator(1, 10000)

        self.offset_up.setValidator(validator_float)
        self.offset_forward.setValidator(validator_float)
        self.offset_left.setValidator(validator_float)
        self.focal_length.setValidator(validator_float)
        self.sensor_size.setValidator(validator_float)
        self.charuco_square_length.setValidator(validator_float)
        self.charuco_marker_length.setValidator(validator_float)
        self.charuco_squares_x.setValidator(validator_int)
        self.charuco_squares_y.setValidator(validator_int)
        self.resolution_x.setValidator(validator_int)
        self.resolution_y.setValidator(validator_int)

        self.resolution_x.setPlaceholderText("1920")
        self.resolution_y.setPlaceholderText("1080")

        resolution_widget = QWidget()
        resolution_layout = QHBoxLayout()
        resolution_layout.setContentsMargins(0, 0, 0, 0)
        resolution_layout.addWidget(self.resolution_x)
        resolution_layout.addWidget(QLabel("x"))
        resolution_layout.addWidget(self.resolution_y)
        resolution_widget.setLayout(resolution_layout)

        form.addRow("Modèle GoPro", self.gopro_model)
        form.addRow(
            "Vidéo caméra cinéma + Charuco",
            self.create_file_row(
                self.cinema_calibration_video,
                "Parcourir",
                "Vidéos (*.mp4 *.mov *.avi);;Tous les fichiers (*)",
            ),
        )
        form.addRow(
            "Vidéo GoPro + Charuco",
            self.create_file_row(
                self.gopro_calibration_video,
                "Parcourir",
                "Vidéos (*.mp4 *.mov *.avi);;Tous les fichiers (*)",
            ),
        )
        form.addRow("Offset Up (m)", self.offset_up)
        form.addRow("Offset Forward (m)", self.offset_forward)
        form.addRow("Offset Left (m)", self.offset_left)
        form.addRow("Focale caméra cinéma (mm)", self.focal_length)
        form.addRow("Largeur capteur (mm)", self.sensor_size)
        form.addRow("Résolution", resolution_widget)
        form.addRow("Dictionary Charuco", self.charuco_dictionary)
        form.addRow("Squares X", self.charuco_squares_x)
        form.addRow("Squares Y", self.charuco_squares_y)
        form.addRow("Square length (m)", self.charuco_square_length)
        form.addRow("Marker length (m)", self.charuco_marker_length)

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
            resolution = (
                int(self.resolution_x.text()),
                int(self.resolution_y.text()),
            )
            board = {
                "dictionary": self.charuco_dictionary.currentText(),
                "squares_x": int(self.charuco_squares_x.text()),
                "squares_y": int(self.charuco_squares_y.text()),
                "square_length": float(self.charuco_square_length.text()),
                "marker_length": float(self.charuco_marker_length.text()),
            }
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
            charuco_board=board,
        )

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer le fichier de calibration",
            "calibration.json",
            "JSON (*.json)",
        )
        if not output_path:
            return

        try:
            output_path = calibration.compute(output_path)
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
