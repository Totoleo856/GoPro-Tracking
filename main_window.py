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
    QMessageBox
)

from calibration.calibration import Calibration


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


    # ----------------------------
    # CALIBRATION
    # ----------------------------

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


        form.addRow(
            "Modèle GoPro",
            self.gopro_model
        )

        form.addRow(
            "Vidéo caméra cinéma + ArUco",
            self.cinema_calibration_video
        )

        form.addRow(
            "Vidéo GoPro + ArUco",
            self.gopro_calibration_video
        )


        form.addRow(
            "Offset Up",
            self.offset_up
        )

        form.addRow(
            "Offset Forward",
            self.offset_forward
        )

        form.addRow(
            "Offset Left",
            self.offset_left
        )


        form.addRow(
            "Focale caméra cinéma",
            self.focal_length
        )

        form.addRow(
            "Taille capteur",
            self.sensor_size
        )

        form.addRow(
            "Résolution",
            self.resolution
        )


        layout.addLayout(form)


        self.calibrate_button = QPushButton(
            "CALIBRATE"
        )

        self.calibrate_button.clicked.connect(
            self.run_calibration
        )


        layout.addWidget(
            self.calibrate_button
        )


        widget.setLayout(layout)

        self.tabs.addTab(
            widget,
            "Calibration"
        )


    def run_calibration(self):

        calibration = Calibration(

            gopro_model=self.gopro_model.text(),

            cinema_video=self.cinema_calibration_video.text(),

            gopro_video=self.gopro_calibration_video.text(),

            offset={
                "up": self.offset_up.text(),
                "forward": self.offset_forward.text(),
                "left": self.offset_left.text()
            },

            camera={
                "focal": self.focal_length.text(),
                "sensor": self.sensor_size.text(),
                "resolution": self.resolution.text()
            }

        )


        result = calibration.compute()


        QMessageBox.information(
            self,
            "Calibration terminée",
            f"Calibration générée\n\n{result}"
        )


    # ----------------------------
    # TRACKING
    # ----------------------------

    def create_tracking_tab(self):

        widget = QWidget()

        layout = QVBoxLayout()


        self.capture_video = QLineEdit()

        self.calibration_file = QLineEdit()


        layout.addWidget(
            QLabel("Vidéo capture GoPro")
        )

        layout.addWidget(
            self.capture_video
        )


        layout.addWidget(
            QLabel("Fichier calibration JSON")
        )

        layout.addWidget(
            self.calibration_file
        )


        self.tracking_button = QPushButton(
            "TRACKING"
        )

        layout.addWidget(
            self.tracking_button
        )


        widget.setLayout(layout)

        self.tabs.addTab(
            widget,
            "Tracking"
        )


    # ----------------------------
    # VERIFICATION EXPORT
    # ----------------------------

    def create_verification_tab(self):

        widget = QWidget()

        layout = QVBoxLayout()


        layout.addWidget(
            QLabel(
                "Chargement tracking + visualisation 3D + export"
            )
        )


        widget.setLayout(layout)

        self.tabs.addTab(
            widget,
            "Vérification et Export"
        )
