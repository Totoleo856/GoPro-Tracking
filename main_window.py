from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QSizePolicy,
    QFrame,
)
from PyQt6.QtGui import QDoubleValidator, QIntValidator

from calibration import Calibration
from tracking import Tracker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GoPro Cinema Tracker")
        self.resize(640, 480)
        self.setMinimumSize(600, 420)

        self.button_style = """
            QPushButton {
                background-color: #1976D2;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 22px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #155fa0;
            }
            QPushButton:pressed {
                background-color: #134d83;
            }
        """

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.create_calibration_tab()
        self.create_tracking_tab()
        self.create_verification_tab()

    def browse_file(self, line_edit, filter="All Files (*)"):
        file_path, _ = QFileDialog.getOpenFileName(self, "Choisir un fichier", "", filter)
        if file_path:
            line_edit.setText(file_path)

    def create_scroll_area(self, widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        return scroll

    def create_file_row(self, line_edit, button_text="Parcourir", filter="All Files (*)"):
        line_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)
        row_layout.addWidget(line_edit)
        browse_button = QPushButton(button_text)
        browse_button.clicked.connect(lambda: self.browse_file(line_edit, filter))
        row_layout.addWidget(browse_button)
        return row_widget

    def set_compact_field(self, widget, width=90):
        widget.setFixedWidth(width)
        widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def create_separator(self):
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setLineWidth(1)
        return separator

    def create_calibration_tab(self):
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(10, 10, 10, 10)
        inner_layout.setSpacing(6)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(6)

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

        validator_float = QDoubleValidator()
        validator_int = QIntValidator(1, 10000)

        for edit in (
            self.offset_up,
            self.offset_forward,
            self.offset_left,
            self.focal_length,
            self.sensor_size,
            self.charuco_square_length,
            self.charuco_marker_length,
        ):
            edit.setValidator(validator_float)
        for edit in (
            self.resolution_x,
            self.resolution_y,
            self.charuco_squares_x,
            self.charuco_squares_y,
        ):
            edit.setValidator(validator_int)

        self.set_compact_field(self.offset_up, 70)
        self.set_compact_field(self.offset_forward, 70)
        self.set_compact_field(self.offset_left, 70)
        self.set_compact_field(self.focal_length, 70)
        self.set_compact_field(self.sensor_size, 70)
        self.set_compact_field(self.resolution_x, 55)
        self.set_compact_field(self.resolution_y, 55)
        self.set_compact_field(self.charuco_squares_x, 50)
        self.set_compact_field(self.charuco_squares_y, 50)
        self.set_compact_field(self.charuco_square_length, 70)
        self.set_compact_field(self.charuco_marker_length, 70)
        self.set_compact_field(self.charuco_dictionary, 130)

        self.gopro_model.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.cinema_calibration_video.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.gopro_calibration_video.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        resolution_widget = QWidget()
        resolution_layout = QHBoxLayout(resolution_widget)
        resolution_layout.setContentsMargins(0, 0, 0, 0)
        resolution_layout.setSpacing(4)
        resolution_layout.addWidget(self.resolution_x)
        resolution_layout.addWidget(QLabel("x"))
        resolution_layout.addWidget(self.resolution_y)

        offsets_widget = QWidget()
        offsets_layout = QHBoxLayout(offsets_widget)
        offsets_layout.setContentsMargins(0, 0, 0, 0)
        offsets_layout.setSpacing(6)
        offsets_layout.addWidget(QLabel("U"))
        offsets_layout.addWidget(self.offset_up)
        offsets_layout.addWidget(QLabel("F"))
        offsets_layout.addWidget(self.offset_forward)
        offsets_layout.addWidget(QLabel("L"))
        offsets_layout.addWidget(self.offset_left)

        camera_widget = QWidget()
        camera_layout = QHBoxLayout(camera_widget)
        camera_layout.setContentsMargins(0, 0, 0, 0)
        camera_layout.setSpacing(8)
        camera_layout.addWidget(QLabel("Focale"))
        camera_layout.addWidget(self.focal_length)
        camera_layout.addWidget(QLabel("Capteur"))
        camera_layout.addWidget(self.sensor_size)
        camera_layout.addStretch()

        board_widget = QWidget()
        board_layout = QHBoxLayout(board_widget)
        board_layout.setContentsMargins(0, 0, 0, 0)
        board_layout.setSpacing(8)
        board_layout.addWidget(self.charuco_dictionary)
        board_layout.addWidget(QLabel("X"))
        board_layout.addWidget(self.charuco_squares_x)
        board_layout.addWidget(QLabel("Y"))
        board_layout.addWidget(self.charuco_squares_y)

        size_widget = QWidget()
        size_layout = QHBoxLayout(size_widget)
        size_layout.setContentsMargins(0, 0, 0, 0)
        size_layout.setSpacing(8)
        size_layout.addWidget(QLabel("Square"))
        size_layout.addWidget(self.charuco_square_length)
        size_layout.addWidget(QLabel("Marker"))
        size_layout.addWidget(self.charuco_marker_length)

        grid.addWidget(QLabel("Modèle GoPro"), 0, 0)
        grid.addWidget(self.gopro_model, 0, 1, 1, 3)
        grid.addWidget(QLabel("Vidéo cinéma + Charuco"), 1, 0)
        grid.addWidget(self.create_file_row(
            self.cinema_calibration_video, "Parcourir", "Vidéos (*.mp4 *.mov *.avi);;Tous les fichiers (*)"
        ), 1, 1, 1, 3)
        grid.addWidget(QLabel("Vidéo GoPro + Charuco"), 2, 0)
        grid.addWidget(self.create_file_row(
            self.gopro_calibration_video, "Parcourir", "Vidéos (*.mp4 *.mov *.avi);;Tous les fichiers (*)"
        ), 2, 1, 1, 3)
        grid.addWidget(QLabel("Offsets (m)"), 3, 0)
        grid.addWidget(offsets_widget, 3, 1, 1, 3)
        grid.addWidget(QLabel("Caméra"), 4, 0)
        grid.addWidget(camera_widget, 4, 1, 1, 3)
        grid.addWidget(QLabel("Résolution"), 5, 0)
        grid.addWidget(resolution_widget, 5, 1, 1, 3)
        grid.addWidget(QLabel("Board"), 6, 0)
        grid.addWidget(board_widget, 6, 1, 1, 3)
        grid.addWidget(QLabel("Tailles (m)"), 7, 0)
        grid.addWidget(size_widget, 7, 1, 1, 3)

        calibrate_button = QPushButton("CALIBRATE")
        calibrate_button.setStyleSheet(self.button_style)
        calibrate_button.clicked.connect(self.run_calibration)

        inner_layout.addLayout(grid)
        inner_layout.addStretch()

        scroll_area = self.create_scroll_area(inner)
        content_layout.addWidget(scroll_area)

        content_layout.addWidget(self.create_separator())

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(calibrate_button)
        button_layout.addStretch()
        button_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.addLayout(button_layout)

        self.tabs.addTab(content, "Calibration")

    def run_calibration(self):
        try:
            offset = {
                "up": float(self.offset_up.text()),
                "forward": float(self.offset_forward.text()),
                "left": float(self.offset_left.text()),
            }
            focal = float(self.focal_length.text())
            sensor = float(self.sensor_size.text())
            resolution = (int(self.resolution_x.text()), int(self.resolution_y.text()))
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
            camera={"focal": focal, "sensor": sensor, "resolution": resolution},
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

        QMessageBox.information(self, "Calibration terminée", f"Calibration générée :\n{output_path}")

    def create_tracking_tab(self):
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(10, 10, 10, 10)
        inner_layout.setSpacing(10)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(8)

        self.capture_video = QLineEdit()
        self.calibration_file = QLineEdit()
        self.capture_video.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.calibration_file.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        form.addRow("Vidéo GoPro", self.create_file_row(
            self.capture_video, "Parcourir", "Vidéos (*.mp4 *.mov *.avi);;Tous les fichiers (*)"
        ))
        form.addRow("Calibration JSON", self.create_file_row(
            self.calibration_file, "Parcourir", "JSON (*.json);;Tous les fichiers (*)"
        ))

        inner_layout.addLayout(form)
        inner_layout.addStretch()

        scroll_area = self.create_scroll_area(inner)
        content_layout.addWidget(scroll_area)

        content_layout.addWidget(self.create_separator())

        tracking_button = QPushButton("TRACKING")
        tracking_button.setStyleSheet(self.button_style)
        tracking_button.clicked.connect(self.run_tracking)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(tracking_button)
        button_layout.addStretch()
        button_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.addLayout(button_layout)

        self.tabs.addTab(content, "Tracking")

    def run_tracking(self):
        capture_path = self.capture_video.text()
        calibration_path = self.calibration_file.text()

        if not capture_path or not calibration_path:
            QMessageBox.warning(self, "Entrée manquante", "Veuillez sélectionner la vidéo GoPro et le fichier de calibration.")
            return

        try:
            tracker = Tracker(capture_path, calibration_path)
            output_path = tracker.run()
        except Exception as exc:
            QMessageBox.critical(self, "Erreur de tracking", str(exc))
            return

        QMessageBox.information(self, "Tracking terminé", f"Fichier tracking généré :\n{output_path}")

    def create_verification_tab(self):
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(10, 10, 10, 10)
        inner_layout.setSpacing(10)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(8)

        self.tracking_result_file = QLineEdit()
        self.tracking_result_file.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        form.addRow("Fichier résultat", self.create_file_row(
            self.tracking_result_file, "Parcourir", "Résultats tracking (*.json *.csv);;Tous les fichiers (*)"
        ))

        inner_layout.addLayout(form)
        inner_layout.addStretch()

        scroll_area = self.create_scroll_area(inner)
        content_layout.addWidget(scroll_area)

        content_layout.addWidget(self.create_separator())

        verify_button = QPushButton("VÉRIFIER / EXPORTER")
        verify_button.setStyleSheet(self.button_style)
        verify_button.clicked.connect(self.run_verification)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(verify_button)
        button_layout.addStretch()
        button_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.addLayout(button_layout)

        self.tabs.addTab(content, "Vérification")

    def run_verification(self):
        result_path = self.tracking_result_file.text()
        if not result_path:
            QMessageBox.warning(self, "Entrée manquante", "Veuillez sélectionner un fichier de résultat de tracking.")
            return
        QMessageBox.information(self, "Vérification et Export", f"Fichier de résultat sélectionné :\n{result_path}")

