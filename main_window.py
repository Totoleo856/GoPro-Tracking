import json
from pathlib import Path

import numpy as np

from PyQt6.QtCore import Qt, QThread, QObject, pyqtSignal
from PyQt6.QtGui import QDoubleValidator, QFont, QIntValidator
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

try:
    import matplotlib
    matplotlib.use("QtAgg")
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    from matplotlib.figure import Figure
    import mpl_toolkits.mplot3d  # noqa: F401  (registers the 3d projection)
except ImportError:
    FigureCanvasQTAgg = None
    Figure = None

from calibration import Calibration
from tracking import Tracker


STYLE_SHEET = """
QMainWindow, QWidget {
    background-color: #202124;
    color: #d7d9db;
    font-size: 10.5pt;
}

QScrollArea {
    background: transparent;
    border: none;
}

QTabWidget::pane {
    border: 1px solid #34363b;
    border-radius: 8px;
    top: -1px;
    background-color: #202124;
}

QTabBar::tab {
    background: transparent;
    color: #9aa0a6;
    padding: 10px 20px;
    margin-right: 2px;
    border-bottom: 2px solid transparent;
    font-weight: 600;
}

QTabBar::tab:selected {
    color: #eaecee;
    border-bottom: 2px solid #5b8def;
}

QTabBar::tab:hover {
    color: #eaecee;
}

QGroupBox {
    background-color: #26272b;
    border: 1px solid #34363b;
    border-radius: 8px;
    margin-top: 14px;
    padding: 16px 14px 14px 14px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    top: -2px;
    padding: 0 6px;
    color: #8fb4ec;
    background-color: #202124;
}

QLabel {
    color: #c7c9cc;
    font-weight: 400;
    background: transparent;
}

QLabel#statusLabel {
    color: #8a8f98;
    font-size: 9pt;
}

QLineEdit, QComboBox {
    background-color: #2b2d31;
    border: 1px solid #3d3f45;
    border-radius: 6px;
    padding: 6px 8px;
    color: #eaecee;
    selection-background-color: #5b8def;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #5b8def;
}

QLineEdit:disabled, QComboBox:disabled {
    color: #6b6e73;
    background-color: #232427;
}

QComboBox::drop-down {
    border: none;
    width: 22px;
}

QComboBox QAbstractItemView {
    background-color: #2b2d31;
    color: #eaecee;
    selection-background-color: #3a5f9f;
    border: 1px solid #3d3f45;
    outline: none;
}

QPushButton {
    background-color: #2f3136;
    border: 1px solid #3d3f45;
    border-radius: 6px;
    padding: 7px 16px;
    color: #d7d9db;
}

QPushButton:hover {
    background-color: #383a40;
}

QPushButton:pressed {
    background-color: #26272b;
}

QPushButton#primaryButton {
    background-color: #3f6fb0;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px 30px;
    font-weight: 600;
    font-size: 11pt;
}

QPushButton#primaryButton:hover {
    background-color: #4d7fc4;
}

QPushButton#primaryButton:pressed {
    background-color: #345b93;
}

QPushButton#primaryButton:disabled {
    background-color: #33475e;
    color: #7c8791;
}

QFrame#separator {
    background-color: #34363b;
    border: none;
    max-height: 1px;
}

QProgressBar {
    background-color: #2b2d31;
    border: 1px solid #3d3f45;
    border-radius: 4px;
    text-align: center;
    color: #d7d9db;
}

QProgressBar::chunk {
    background-color: #5b8def;
    border-radius: 4px;
}

QMessageBox {
    background-color: #26272b;
}

QScrollBar:vertical {
    background: #202124;
    width: 12px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #45474d;
    border-radius: 5px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background: #55575d;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
"""


class CalibrationWorker(QObject):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, calibration, output_path):
        super().__init__()
        self.calibration = calibration
        self.output_path = output_path

    def run(self):
        try:
            output_path = self.calibration.compute(self.output_path, progress_callback=self.progress.emit)
        except Exception as exc:
            self.error.emit(str(exc))
            return
        self.finished.emit(output_path)


class TrackingWorker(QObject):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, tracker):
        super().__init__()
        self.tracker = tracker

    def run(self):
        try:
            output_path = self.tracker.run(progress_callback=self.progress.emit)
        except Exception as exc:
            self.error.emit(str(exc))
            return
        self.finished.emit(output_path)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GoPro Cinema Tracker")
        self.resize(780, 780)
        self.setMinimumSize(700, 620)

        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(STYLE_SHEET)
            app.setFont(QFont("Segoe UI", 10))

        self._calibration_thread = None
        self._calibration_worker = None
        self._tracking_thread = None
        self._tracking_worker = None

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.create_calibration_tab()
        self.create_tracking_tab()
        self.create_verification_tab()

    # ------------------------------------------------------------------
    # Helpers communs
    # ------------------------------------------------------------------
    def browse_file(self, line_edit, filter="All Files (*)"):
        file_path, _ = QFileDialog.getOpenFileName(self, "Choisir un fichier", "", filter)
        if file_path:
            line_edit.setText(file_path)

    def create_scroll_area(self, widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
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
        separator.setObjectName("separator")
        separator.setFixedHeight(1)
        return separator

    def create_progress_row(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setTextVisible(False)
        progress_bar.setFixedHeight(8)

        status_label = QLabel("")
        status_label.setObjectName("statusLabel")

        layout.addWidget(progress_bar)
        layout.addWidget(status_label)
        return container, progress_bar, status_label

    def _set_progress(self, progress_bar, status_label, pct, message=""):
        if pct is not None and pct < 0:
            progress_bar.setRange(0, 0)
        else:
            progress_bar.setRange(0, 100)
            if pct is not None:
                progress_bar.setValue(pct)
        if message:
            status_label.setText(message)

    def _reset_progress(self, progress_bar, status_label, message=""):
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        status_label.setText(message)

    # ------------------------------------------------------------------
    # Aperçu 3D de la trajectoire
    # ------------------------------------------------------------------
    def _style_3d_axes(self, ax):
        background = "#202124"
        panel = "#26272b"
        grid_color = (0.20, 0.21, 0.23, 1)
        text_color = "#c7c9cc"

        self.verification_figure.patch.set_facecolor(background)
        ax.set_facecolor(background)
        for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
            axis.pane.set_facecolor(panel)
            axis.pane.set_edgecolor("#34363b")
            axis._axinfo["grid"]["color"] = grid_color
            axis.label.set_color(text_color)
        ax.tick_params(colors=text_color)
        ax.title.set_color("#eaecee")

    def _set_axes_equal(self, ax, positions):
        mins = positions.min(axis=0)
        maxs = positions.max(axis=0)
        mins = np.minimum(mins, 0.0)
        maxs = np.maximum(maxs, 0.0)
        half_range = max((maxs - mins).max() / 2.0, 0.1)
        center = (maxs + mins) / 2.0
        ax.set_xlim(center[0] - half_range, center[0] + half_range)
        ax.set_ylim(center[1] - half_range, center[1] + half_range)
        ax.set_zlim(center[2] - half_range, center[2] + half_range)
        return half_range

    def _decorate_empty_axes(self, ax, message=""):
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.set_zlabel("Z (m)")
        ax.set_title("Trajectoire caméra cinéma")
        if message:
            ax.text2D(
                0.5, 0.5, message, transform=ax.transAxes,
                ha="center", va="center", color="#8a8f98", fontsize=9,
            )

    def _reset_trajectory_plot(self, message=""):
        if self.verification_canvas is None:
            return
        ax = self.verification_axes
        ax.clear()
        self._style_3d_axes(ax)
        self._decorate_empty_axes(ax, message)
        self.verification_canvas.draw()

    def _plot_trajectory(self, positions, forwards):
        if self.verification_canvas is None:
            return
        ax = self.verification_axes
        ax.clear()
        self._style_3d_axes(ax)
        self._decorate_empty_axes(ax)

        ax.plot(positions[:, 0], positions[:, 1], positions[:, 2], color="#5b8def", linewidth=2, label="Trajectoire")
        ax.scatter(*positions[0], color="#4caf50", s=45, label="Départ", depthshade=False)
        ax.scatter(*positions[-1], color="#e05252", s=45, label="Fin", depthshade=False)

        half_range = self._set_axes_equal(ax, positions)

        step = max(1, len(positions) // 25)
        indices = np.arange(0, len(positions), step)
        arrow_length = half_range * 0.15
        ax.quiver(
            positions[indices, 0], positions[indices, 1], positions[indices, 2],
            forwards[indices, 0], forwards[indices, 1], forwards[indices, 2],
            length=arrow_length, normalize=True, color="#8fb4ec", linewidth=1, arrow_length_ratio=0.35,
        )

        axis_length = half_range * 0.2
        ax.quiver(0, 0, 0, 1, 0, 0, length=axis_length, color="#e05252")
        ax.quiver(0, 0, 0, 0, 1, 0, length=axis_length, color="#4caf50")
        ax.quiver(0, 0, 0, 0, 0, 1, length=axis_length, color="#5b8def")
        ax.scatter(0, 0, 0, color="#eaecee", s=35, marker="x", label="Origine (cible Charuco)", depthshade=False)

        ax.legend(facecolor="#26272b", labelcolor="#c7c9cc", edgecolor="#34363b", loc="upper right", fontsize=8)
        self.verification_canvas.draw()

    # ------------------------------------------------------------------
    # Onglet Calibration
    # ------------------------------------------------------------------
    def create_calibration_tab(self):
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(16, 16, 16, 16)
        inner_layout.setSpacing(14)

        self.gopro_model = QLineEdit()
        self.gopro_model.setPlaceholderText("ex. HERO11 Black")
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

        for widget, width in (
            (self.offset_up, 70),
            (self.offset_forward, 70),
            (self.offset_left, 70),
            (self.focal_length, 70),
            (self.sensor_size, 70),
            (self.resolution_x, 60),
            (self.resolution_y, 60),
            (self.charuco_squares_x, 50),
            (self.charuco_squares_y, 50),
            (self.charuco_square_length, 70),
            (self.charuco_marker_length, 70),
            (self.charuco_dictionary, 140),
        ):
            self.set_compact_field(widget, width)

        self.gopro_model.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # -- Groupe : Rig --
        rig_group = QGroupBox("Rig")
        rig_form = QFormLayout(rig_group)
        rig_form.setHorizontalSpacing(14)
        rig_form.setVerticalSpacing(10)

        offsets_widget = QWidget()
        offsets_layout = QHBoxLayout(offsets_widget)
        offsets_layout.setContentsMargins(0, 0, 0, 0)
        offsets_layout.setSpacing(6)
        offsets_layout.addWidget(QLabel("Haut"))
        offsets_layout.addWidget(self.offset_up)
        offsets_layout.addWidget(QLabel("Avant"))
        offsets_layout.addWidget(self.offset_forward)
        offsets_layout.addWidget(QLabel("Gauche"))
        offsets_layout.addWidget(self.offset_left)
        offsets_layout.addStretch()

        rig_form.addRow("Modèle GoPro", self.gopro_model)
        rig_form.addRow("Offsets (m)", offsets_widget)

        # -- Groupe : Vidéos de calibration --
        videos_group = QGroupBox("Vidéos de calibration")
        videos_form = QFormLayout(videos_group)
        videos_form.setHorizontalSpacing(14)
        videos_form.setVerticalSpacing(10)
        videos_form.addRow("Vidéo cinéma + Charuco", self.create_file_row(
            self.cinema_calibration_video, "Parcourir", "Vidéos (*.mp4 *.mov *.avi);;Tous les fichiers (*)"
        ))
        videos_form.addRow("Vidéo GoPro + Charuco", self.create_file_row(
            self.gopro_calibration_video, "Parcourir", "Vidéos (*.mp4 *.mov *.avi);;Tous les fichiers (*)"
        ))

        # -- Groupe : Caméra cinéma --
        camera_group = QGroupBox("Caméra cinéma")
        camera_form = QFormLayout(camera_group)
        camera_form.setHorizontalSpacing(14)
        camera_form.setVerticalSpacing(10)

        optics_widget = QWidget()
        optics_layout = QHBoxLayout(optics_widget)
        optics_layout.setContentsMargins(0, 0, 0, 0)
        optics_layout.setSpacing(8)
        optics_layout.addWidget(QLabel("Focale (mm)"))
        optics_layout.addWidget(self.focal_length)
        optics_layout.addSpacing(10)
        optics_layout.addWidget(QLabel("Capteur (mm)"))
        optics_layout.addWidget(self.sensor_size)
        optics_layout.addStretch()

        resolution_widget = QWidget()
        resolution_layout = QHBoxLayout(resolution_widget)
        resolution_layout.setContentsMargins(0, 0, 0, 0)
        resolution_layout.setSpacing(4)
        resolution_layout.addWidget(self.resolution_x)
        resolution_layout.addWidget(QLabel("×"))
        resolution_layout.addWidget(self.resolution_y)
        resolution_layout.addStretch()

        camera_form.addRow("Optique", optics_widget)
        camera_form.addRow("Résolution (px)", resolution_widget)

        # -- Groupe : Planche Charuco --
        board_group = QGroupBox("Planche Charuco")
        board_form = QFormLayout(board_group)
        board_form.setHorizontalSpacing(14)
        board_form.setVerticalSpacing(10)

        board_widget = QWidget()
        board_layout = QHBoxLayout(board_widget)
        board_layout.setContentsMargins(0, 0, 0, 0)
        board_layout.setSpacing(8)
        board_layout.addWidget(self.charuco_dictionary)
        board_layout.addSpacing(6)
        board_layout.addWidget(QLabel("Cases X"))
        board_layout.addWidget(self.charuco_squares_x)
        board_layout.addWidget(QLabel("Cases Y"))
        board_layout.addWidget(self.charuco_squares_y)
        board_layout.addStretch()

        size_widget = QWidget()
        size_layout = QHBoxLayout(size_widget)
        size_layout.setContentsMargins(0, 0, 0, 0)
        size_layout.setSpacing(8)
        size_layout.addWidget(QLabel("Case"))
        size_layout.addWidget(self.charuco_square_length)
        size_layout.addWidget(QLabel("Marqueur"))
        size_layout.addWidget(self.charuco_marker_length)
        size_layout.addStretch()

        board_form.addRow("Dictionnaire", board_widget)
        board_form.addRow("Tailles (m)", size_widget)

        inner_layout.addWidget(rig_group)
        inner_layout.addWidget(videos_group)
        inner_layout.addWidget(camera_group)
        inner_layout.addWidget(board_group)
        inner_layout.addStretch()

        scroll_area = self.create_scroll_area(inner)
        content_layout.addWidget(scroll_area)

        content_layout.addWidget(self.create_separator())

        footer = QWidget()
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(16, 12, 16, 16)
        footer_layout.setSpacing(10)

        progress_container, self.calibration_progress, self.calibration_status = self.create_progress_row()
        footer_layout.addWidget(progress_container)

        self.calibrate_button = QPushButton("LANCER LA CALIBRATION")
        self.calibrate_button.setObjectName("primaryButton")
        self.calibrate_button.clicked.connect(self.run_calibration)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.calibrate_button)
        button_layout.addStretch()
        footer_layout.addLayout(button_layout)

        content_layout.addWidget(footer)

        self.tabs.addTab(content, "1 · Calibration")

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

        self.calibrate_button.setEnabled(False)
        self._set_progress(self.calibration_progress, self.calibration_status, 0, "Démarrage de la calibration...")

        self._calibration_thread = QThread(self)
        self._calibration_worker = CalibrationWorker(calibration, output_path)
        self._calibration_worker.moveToThread(self._calibration_thread)

        self._calibration_thread.started.connect(self._calibration_worker.run)
        self._calibration_worker.progress.connect(self._on_calibration_progress)
        self._calibration_worker.finished.connect(self._on_calibration_finished)
        self._calibration_worker.error.connect(self._on_calibration_error)
        self._calibration_worker.finished.connect(self._calibration_thread.quit)
        self._calibration_worker.error.connect(self._calibration_thread.quit)
        self._calibration_thread.finished.connect(self._calibration_worker.deleteLater)

        self._calibration_thread.start()

    def _on_calibration_progress(self, pct, message):
        self._set_progress(self.calibration_progress, self.calibration_status, pct, message)

    def _on_calibration_finished(self, output_path):
        self.calibrate_button.setEnabled(True)
        self._set_progress(self.calibration_progress, self.calibration_status, 100, "Calibration terminée")
        QMessageBox.information(self, "Calibration terminée", f"Calibration générée :\n{output_path}")

    def _on_calibration_error(self, message):
        self.calibrate_button.setEnabled(True)
        self._reset_progress(self.calibration_progress, self.calibration_status, "Échec de la calibration")
        QMessageBox.critical(self, "Erreur de calibration", message)

    # ------------------------------------------------------------------
    # Onglet Tracking
    # ------------------------------------------------------------------
    def create_tracking_tab(self):
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(16, 16, 16, 16)
        inner_layout.setSpacing(14)

        inputs_group = QGroupBox("Fichiers d'entrée")
        form = QFormLayout(inputs_group)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

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

        inner_layout.addWidget(inputs_group)
        inner_layout.addStretch()

        scroll_area = self.create_scroll_area(inner)
        content_layout.addWidget(scroll_area)

        content_layout.addWidget(self.create_separator())

        footer = QWidget()
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(16, 12, 16, 16)
        footer_layout.setSpacing(10)

        progress_container, self.tracking_progress, self.tracking_status = self.create_progress_row()
        footer_layout.addWidget(progress_container)

        self.tracking_button = QPushButton("LANCER LE TRACKING")
        self.tracking_button.setObjectName("primaryButton")
        self.tracking_button.clicked.connect(self.run_tracking)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.tracking_button)
        button_layout.addStretch()
        footer_layout.addLayout(button_layout)

        content_layout.addWidget(footer)

        self.tabs.addTab(content, "2 · Tracking")

    def run_tracking(self):
        capture_path = self.capture_video.text()
        calibration_path = self.calibration_file.text()

        if not capture_path or not calibration_path:
            QMessageBox.warning(self, "Entrée manquante", "Veuillez sélectionner la vidéo GoPro et le fichier de calibration.")
            return

        try:
            tracker = Tracker(capture_path, calibration_path)
        except Exception as exc:
            QMessageBox.critical(self, "Erreur de tracking", str(exc))
            return

        self.tracking_button.setEnabled(False)
        self._set_progress(self.tracking_progress, self.tracking_status, 0, "Démarrage du tracking...")

        self._tracking_thread = QThread(self)
        self._tracking_worker = TrackingWorker(tracker)
        self._tracking_worker.moveToThread(self._tracking_thread)

        self._tracking_thread.started.connect(self._tracking_worker.run)
        self._tracking_worker.progress.connect(self._on_tracking_progress)
        self._tracking_worker.finished.connect(self._on_tracking_finished)
        self._tracking_worker.error.connect(self._on_tracking_error)
        self._tracking_worker.finished.connect(self._tracking_thread.quit)
        self._tracking_worker.error.connect(self._tracking_thread.quit)
        self._tracking_thread.finished.connect(self._tracking_worker.deleteLater)

        self._tracking_thread.start()

    def _on_tracking_progress(self, pct, message):
        self._set_progress(self.tracking_progress, self.tracking_status, pct, message)

    def _on_tracking_finished(self, output_path):
        self.tracking_button.setEnabled(True)
        self._set_progress(self.tracking_progress, self.tracking_status, 100, "Tracking terminé")
        QMessageBox.information(self, "Tracking terminé", f"Fichier tracking généré :\n{output_path}")

    def _on_tracking_error(self, message):
        self.tracking_button.setEnabled(True)
        self._reset_progress(self.tracking_progress, self.tracking_status, "Échec du tracking")
        QMessageBox.critical(self, "Erreur de tracking", message)

    # ------------------------------------------------------------------
    # Onglet Vérification
    # ------------------------------------------------------------------
    def create_verification_tab(self):
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(16, 16, 16, 16)
        inner_layout.setSpacing(14)

        result_group = QGroupBox("Résultat de tracking")
        form = QFormLayout(result_group)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        self.tracking_result_file = QLineEdit()
        self.tracking_result_file.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        form.addRow("Fichier résultat", self.create_file_row(
            self.tracking_result_file, "Parcourir", "Résultats tracking (*.json *.csv);;Tous les fichiers (*)"
        ))

        inner_layout.addWidget(result_group)
        inner_layout.addStretch()

        scroll_area = self.create_scroll_area(inner)
        content_layout.addWidget(scroll_area, 0)

        viewer_group = QGroupBox("Aperçu 3D de la trajectoire")
        viewer_layout = QVBoxLayout(viewer_group)
        viewer_layout.setContentsMargins(10, 10, 10, 10)

        if FigureCanvasQTAgg is not None:
            self.verification_figure = Figure(figsize=(5, 4))
            self.verification_canvas = FigureCanvasQTAgg(self.verification_figure)
            self.verification_canvas.setMinimumHeight(300)
            self.verification_axes = self.verification_figure.add_subplot(111, projection="3d")
            self._reset_trajectory_plot("Chargez un fichier de tracking puis cliquez sur Vérifier / Exporter")
            viewer_layout.addWidget(self.verification_canvas)
        else:
            self.verification_canvas = None
            placeholder = QLabel(
                "Visionneuse 3D indisponible : installez matplotlib (pip install matplotlib)."
            )
            placeholder.setWordWrap(True)
            viewer_layout.addWidget(placeholder)

        content_layout.addWidget(viewer_group, 1)

        content_layout.addWidget(self.create_separator())

        footer = QWidget()
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(16, 12, 16, 16)
        footer_layout.setSpacing(10)

        progress_container, self.verification_progress, self.verification_status = self.create_progress_row()
        footer_layout.addWidget(progress_container)

        verify_button = QPushButton("VÉRIFIER / EXPORTER")
        verify_button.setObjectName("primaryButton")
        verify_button.clicked.connect(self.run_verification)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(verify_button)
        button_layout.addStretch()
        footer_layout.addLayout(button_layout)

        content_layout.addWidget(footer)

        self.tabs.addTab(content, "3 · Vérification")

    def run_verification(self):
        result_path = self.tracking_result_file.text()
        if not result_path:
            QMessageBox.warning(self, "Entrée manquante", "Veuillez sélectionner un fichier de résultat de tracking.")
            return

        path = Path(result_path)
        if path.suffix.lower() != ".json":
            QMessageBox.warning(
                self, "Format non supporté",
                "L'aperçu 3D ne prend en charge que les fichiers .json pour le moment.",
            )
            return

        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
            frames = data["frames"]
            if not frames:
                raise ValueError("Le fichier de tracking ne contient aucune image.")
            matrices = np.array([frame["matrix"] for frame in frames], dtype=np.float64)
        except Exception as exc:
            QMessageBox.critical(self, "Erreur de lecture", f"Impossible de lire le fichier de tracking :\n{exc}")
            return

        positions = matrices[:, :3, 3]
        forwards = matrices[:, :3, 2]

        if self.verification_canvas is not None:
            self._plot_trajectory(positions, forwards)
            self._set_progress(
                self.verification_progress, self.verification_status, 100,
                f"{len(frames)} poses chargées",
            )
        else:
            self._set_progress(
                self.verification_progress, self.verification_status, 100,
                f"{len(frames)} poses (installez matplotlib pour l'aperçu 3D)",
            )
