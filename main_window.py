import json
import re
import shutil
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
    QInputDialog,
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
from sfm_tracking import SfmTracker
from dual_tracking import DualTracker
from profiles import list_profiles, load_profile, save_profile
from version import __version__


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

QGroupBox::indicator {
    width: 15px;
    height: 15px;
    border: 1px solid #4a4d54;
    border-radius: 3px;
    background-color: #1b1c1f;
}

QGroupBox::indicator:unchecked:hover {
    border: 1px solid #5b8def;
}

QGroupBox::indicator:checked {
    background-color: #5b8def;
    border: 1px solid #5b8def;
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

QPushButton:disabled {
    background-color: #232427;
    border: 1px solid #302f34;
    color: #5c5e63;
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
        self.setWindowTitle(f"GoPro Cinema Tracker v{__version__}")
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
    def browse_file(self, line_edit, filter="All Files (*)", on_selected=None):
        file_path, _ = QFileDialog.getOpenFileName(self, "Choisir un fichier", "", filter)
        if file_path:
            line_edit.setText(file_path)
            if on_selected:
                on_selected(file_path)

    def create_scroll_area(self, widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        return scroll

    def create_file_row(self, line_edit, button_text="Parcourir", filter="All Files (*)", on_selected=None):
        line_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)
        row_layout.addWidget(line_edit)
        browse_button = QPushButton(button_text)
        browse_button.clicked.connect(lambda: self.browse_file(line_edit, filter, on_selected))
        row_layout.addWidget(browse_button)
        if on_selected:
            line_edit.editingFinished.connect(lambda: on_selected(line_edit.text()))
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
    # Presets (profils GoPro / Caméra / Planche Charuco)
    # ------------------------------------------------------------------
    def _refresh_profile_combo(self, combo, kind):
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("— Choisir un profil —")
        combo.addItems(list_profiles(kind))
        combo.blockSignals(False)

    def _create_profile_bar(self, kind, on_load, get_current_values, name_field=None):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        combo = QComboBox()
        combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._refresh_profile_combo(combo, kind)

        def handle_selection(index):
            if index <= 0:
                return
            name = combo.itemText(index)
            try:
                data = load_profile(kind, name)
            except Exception as exc:
                QMessageBox.warning(self, "Erreur", f"Impossible de charger le profil :\n{exc}")
                return
            on_load(data)

        combo.currentIndexChanged.connect(handle_selection)

        save_button = QPushButton("Enregistrer...")

        def handle_save():
            if name_field is not None:
                name = name_field.text().strip()
                if not name:
                    QMessageBox.warning(
                        self, "Nom manquant",
                        "Veuillez renseigner le champ \"Modèle\" avant d'enregistrer le profil.",
                    )
                    return
            else:
                name, ok = QInputDialog.getText(self, "Enregistrer le profil", "Nom du profil :")
                name = name.strip()
                if not ok or not name:
                    return
            try:
                data = get_current_values()
                save_profile(kind, name, data)
            except Exception as exc:
                QMessageBox.warning(self, "Erreur", f"Impossible d'enregistrer le profil :\n{exc}")
                return
            self._refresh_profile_combo(combo, kind)
            index = combo.findText(name)
            if index >= 0:
                combo.setCurrentIndex(index)

        save_button.clicked.connect(handle_save)

        layout.addWidget(combo)
        layout.addWidget(save_button)
        return container

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

        self.rig_name = QLineEdit()
        self.rig_name.setPlaceholderText("ex. Rig Alexa Mini + HERO11")
        self.gopro_model = QLineEdit()
        self.gopro_model.setPlaceholderText("ex. HERO11 Black")
        self.cinema_calibration_video = QLineEdit()
        self.gopro_calibration_video = QLineEdit()
        self.offset_up = QLineEdit()
        self.offset_forward = QLineEdit()
        self.offset_left = QLineEdit()

        self.gopro_focal_length = QLineEdit()
        self.gopro_sensor_size = QLineEdit()
        self.gopro_resolution_x = QLineEdit()
        self.gopro_resolution_y = QLineEdit()
        self.gopro_fps = QLineEdit()
        self.gopro_fps.setPlaceholderText("auto")

        self.cinema_model = QLineEdit()
        self.cinema_model.setPlaceholderText("ex. Alexa Mini")
        self.cinema_focal_length = QLineEdit()
        self.cinema_sensor_size = QLineEdit()
        self.cinema_resolution_x = QLineEdit()
        self.cinema_resolution_y = QLineEdit()
        self.cinema_fps = QLineEdit()

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
            self.gopro_focal_length,
            self.gopro_sensor_size,
            self.gopro_fps,
            self.cinema_focal_length,
            self.cinema_sensor_size,
            self.cinema_fps,
            self.charuco_square_length,
            self.charuco_marker_length,
        ):
            edit.setValidator(validator_float)
        for edit in (
            self.gopro_resolution_x,
            self.gopro_resolution_y,
            self.cinema_resolution_x,
            self.cinema_resolution_y,
            self.charuco_squares_x,
            self.charuco_squares_y,
        ):
            edit.setValidator(validator_int)

        for widget, width in (
            (self.offset_up, 70),
            (self.offset_forward, 70),
            (self.offset_left, 70),
            (self.gopro_focal_length, 70),
            (self.gopro_sensor_size, 70),
            (self.gopro_resolution_x, 60),
            (self.gopro_resolution_y, 60),
            (self.gopro_fps, 70),
            (self.cinema_focal_length, 70),
            (self.cinema_sensor_size, 70),
            (self.cinema_resolution_x, 60),
            (self.cinema_resolution_y, 60),
            (self.cinema_fps, 70),
            (self.charuco_squares_x, 50),
            (self.charuco_squares_y, 50),
            (self.charuco_square_length, 70),
            (self.charuco_marker_length, 70),
            (self.charuco_dictionary, 140),
        ):
            self.set_compact_field(widget, width)

        self.rig_name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.gopro_model.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.cinema_model.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

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

        rig_form.addRow("Nom du rig", self.rig_name)
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

        # -- Groupe : Profil GoPro --
        gopro_camera_group = QGroupBox("Profil GoPro")
        gopro_camera_layout = QVBoxLayout(gopro_camera_group)
        gopro_camera_layout.setSpacing(10)
        gopro_camera_layout.addWidget(self._create_profile_bar(
            "gopro", self._load_gopro_profile, self._capture_gopro_profile, name_field=self.gopro_model
        ))

        gopro_form = QFormLayout()
        gopro_form.setHorizontalSpacing(14)
        gopro_form.setVerticalSpacing(10)

        gopro_optics_widget = QWidget()
        gopro_optics_layout = QHBoxLayout(gopro_optics_widget)
        gopro_optics_layout.setContentsMargins(0, 0, 0, 0)
        gopro_optics_layout.setSpacing(8)
        gopro_optics_layout.addWidget(QLabel("Focale (mm)"))
        gopro_optics_layout.addWidget(self.gopro_focal_length)
        gopro_optics_layout.addSpacing(10)
        gopro_optics_layout.addWidget(QLabel("Capteur (mm)"))
        gopro_optics_layout.addWidget(self.gopro_sensor_size)
        gopro_optics_layout.addStretch()

        gopro_resolution_widget = QWidget()
        gopro_resolution_layout = QHBoxLayout(gopro_resolution_widget)
        gopro_resolution_layout.setContentsMargins(0, 0, 0, 0)
        gopro_resolution_layout.setSpacing(4)
        gopro_resolution_layout.addWidget(self.gopro_resolution_x)
        gopro_resolution_layout.addWidget(QLabel("×"))
        gopro_resolution_layout.addWidget(self.gopro_resolution_y)
        gopro_resolution_layout.addStretch()

        gopro_form.addRow("Modèle", self.gopro_model)
        gopro_form.addRow("Optique", gopro_optics_widget)
        gopro_form.addRow("Résolution (px)", gopro_resolution_widget)
        gopro_form.addRow("FPS", self.gopro_fps)
        gopro_camera_layout.addLayout(gopro_form)

        # -- Groupe : Profil Caméra cinéma --
        camera_group = QGroupBox("Profil Caméra cinéma")
        camera_group_layout = QVBoxLayout(camera_group)
        camera_group_layout.setSpacing(10)
        camera_group_layout.addWidget(self._create_profile_bar(
            "camera", self._load_camera_profile, self._capture_camera_profile, name_field=self.cinema_model
        ))

        camera_form = QFormLayout()
        camera_form.setHorizontalSpacing(14)
        camera_form.setVerticalSpacing(10)

        optics_widget = QWidget()
        optics_layout = QHBoxLayout(optics_widget)
        optics_layout.setContentsMargins(0, 0, 0, 0)
        optics_layout.setSpacing(8)
        optics_layout.addWidget(QLabel("Focale (mm)"))
        optics_layout.addWidget(self.cinema_focal_length)
        optics_layout.addSpacing(10)
        optics_layout.addWidget(QLabel("Capteur (mm)"))
        optics_layout.addWidget(self.cinema_sensor_size)
        optics_layout.addStretch()

        resolution_widget = QWidget()
        resolution_layout = QHBoxLayout(resolution_widget)
        resolution_layout.setContentsMargins(0, 0, 0, 0)
        resolution_layout.setSpacing(4)
        resolution_layout.addWidget(self.cinema_resolution_x)
        resolution_layout.addWidget(QLabel("×"))
        resolution_layout.addWidget(self.cinema_resolution_y)
        resolution_layout.addStretch()

        camera_form.addRow("Modèle", self.cinema_model)
        camera_form.addRow("Optique", optics_widget)
        camera_form.addRow("Résolution (px)", resolution_widget)
        camera_form.addRow("FPS", self.cinema_fps)
        camera_group_layout.addLayout(camera_form)

        # -- Groupe : Planche Charuco --
        board_group = QGroupBox("Planche Charuco")
        board_group_layout = QVBoxLayout(board_group)
        board_group_layout.setSpacing(10)
        board_group_layout.addWidget(self._create_profile_bar(
            "charuco_board", self._load_charuco_profile, self._capture_charuco_profile
        ))

        board_form = QFormLayout()
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
        board_group_layout.addLayout(board_form)

        inner_layout.addWidget(rig_group)
        inner_layout.addWidget(videos_group)
        inner_layout.addWidget(gopro_camera_group)
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

    def _load_gopro_profile(self, data):
        if "model" in data:
            self.gopro_model.setText(str(data["model"]))
        if "sensor_width" in data:
            self.gopro_sensor_size.setText(str(data["sensor_width"]))
        if "focal_length" in data:
            self.gopro_focal_length.setText(str(data["focal_length"]))
        resolution = data.get("resolution")
        if resolution:
            self.gopro_resolution_x.setText(str(resolution[0]))
            self.gopro_resolution_y.setText(str(resolution[1]))
        self.gopro_fps.setText(str(data["fps"]) if data.get("fps") else "")

    def _capture_gopro_profile(self):
        fps_text = self.gopro_fps.text().strip()
        return {
            "model": self.gopro_model.text(),
            "sensor_width": float(self.gopro_sensor_size.text()),
            "focal_length": float(self.gopro_focal_length.text()),
            "resolution": [int(self.gopro_resolution_x.text()), int(self.gopro_resolution_y.text())],
            "fps": float(fps_text) if fps_text else 0.0,
        }

    def _load_camera_profile(self, data):
        if "model" in data:
            self.cinema_model.setText(str(data["model"]))
        if "sensor_width" in data:
            self.cinema_sensor_size.setText(str(data["sensor_width"]))
        resolution = data.get("resolution")
        if resolution:
            self.cinema_resolution_x.setText(str(resolution[0]))
            self.cinema_resolution_y.setText(str(resolution[1]))
        self.cinema_fps.setText(str(data["fps"]) if data.get("fps") else "")

    def _capture_camera_profile(self):
        fps_text = self.cinema_fps.text().strip()
        return {
            "model": self.cinema_model.text(),
            "sensor_width": float(self.cinema_sensor_size.text()),
            "resolution": [int(self.cinema_resolution_x.text()), int(self.cinema_resolution_y.text())],
            "fps": float(fps_text) if fps_text else 0.0,
        }

    def _load_charuco_profile(self, data):
        if "dictionary" in data:
            self.charuco_dictionary.setCurrentText(str(data["dictionary"]))
        if "squares_x" in data:
            self.charuco_squares_x.setText(str(data["squares_x"]))
        if "squares_y" in data:
            self.charuco_squares_y.setText(str(data["squares_y"]))
        if "square_length" in data:
            self.charuco_square_length.setText(str(data["square_length"]))
        if "marker_length" in data:
            self.charuco_marker_length.setText(str(data["marker_length"]))

    def _capture_charuco_profile(self):
        return {
            "dictionary": self.charuco_dictionary.currentText(),
            "squares_x": int(self.charuco_squares_x.text()),
            "squares_y": int(self.charuco_squares_y.text()),
            "square_length": float(self.charuco_square_length.text()),
            "marker_length": float(self.charuco_marker_length.text()),
        }

    def _sanitize_filename(self, name: str) -> str:
        return re.sub(r'[\\/:*?"<>|]+', "_", name).strip() or "calibration"

    def run_calibration(self):
        try:
            offset = {
                "up": float(self.offset_up.text()),
                "forward": float(self.offset_forward.text()),
                "left": float(self.offset_left.text()),
            }
            gopro_fps_text = self.gopro_fps.text().strip()
            cinema_fps_text = self.cinema_fps.text().strip()
            gopro_camera = {
                "focal": float(self.gopro_focal_length.text()),
                "sensor": float(self.gopro_sensor_size.text()),
                "resolution": (int(self.gopro_resolution_x.text()), int(self.gopro_resolution_y.text())),
                "fps": float(gopro_fps_text) if gopro_fps_text else 0.0,
            }
            cinema_camera = {
                "focal": float(self.cinema_focal_length.text()),
                "sensor": float(self.cinema_sensor_size.text()),
                "resolution": (int(self.cinema_resolution_x.text()), int(self.cinema_resolution_y.text())),
                "fps": float(cinema_fps_text) if cinema_fps_text else 0.0,
            }
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
            cinema_model=self.cinema_model.text(),
            cinema_video=self.cinema_calibration_video.text(),
            gopro_video=self.gopro_calibration_video.text(),
            offset=offset,
            gopro_camera=gopro_camera,
            cinema_camera=cinema_camera,
            charuco_board=board,
            rig_name=self.rig_name.text(),
        )

        default_name = f"{self._sanitize_filename(self.rig_name.text())}.json"
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer le fichier de calibration",
            default_name,
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

        inputs_group = QGroupBox("GoPro 1")
        form = QFormLayout(inputs_group)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        self.capture_video_1 = QLineEdit()
        self.calibration_file_1 = QLineEdit()
        self.capture_video_1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.calibration_file_1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        form.addRow("Vidéo GoPro", self.create_file_row(
            self.capture_video_1, "Parcourir", "Vidéos (*.mp4 *.mov *.avi);;Tous les fichiers (*)"
        ))
        form.addRow("Calibration JSON", self.create_file_row(
            self.calibration_file_1, "Parcourir", "JSON (*.json);;Tous les fichiers (*)"
        ))

        self.gopro2_group = QGroupBox("GoPro 2 (optionnel)")
        self.gopro2_group.setCheckable(True)
        self.gopro2_group.setChecked(False)
        gopro2_form = QFormLayout(self.gopro2_group)
        gopro2_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        gopro2_form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        gopro2_form.setHorizontalSpacing(14)
        gopro2_form.setVerticalSpacing(10)

        self.capture_video_2 = QLineEdit()
        self.calibration_file_2 = QLineEdit()
        self.capture_video_2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.calibration_file_2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        gopro2_form.addRow("Vidéo GoPro", self.create_file_row(
            self.capture_video_2, "Parcourir", "Vidéos (*.mp4 *.mov *.avi);;Tous les fichiers (*)"
        ))
        gopro2_form.addRow("Calibration JSON", self.create_file_row(
            self.calibration_file_2, "Parcourir", "JSON (*.json);;Tous les fichiers (*)"
        ))

        mode_group = QGroupBox("Mode de tracking")
        mode_layout = QVBoxLayout(mode_group)
        self.tracking_mode = QComboBox()
        self.tracking_mode.addItem(
            "SfM (COLMAP) — cible visible au début seulement", userData="sfm"
        )
        self.tracking_mode.addItem(
            "Charuco continu — cible visible en permanence", userData="charuco"
        )
        mode_layout.addWidget(self.tracking_mode)

        inner_layout.addWidget(inputs_group)
        inner_layout.addWidget(self.gopro2_group)
        inner_layout.addWidget(mode_group)
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
        capture_path = self.capture_video_1.text()
        calibration_path = self.calibration_file_1.text()

        if not capture_path or not calibration_path:
            QMessageBox.warning(self, "Entrée manquante", "Veuillez sélectionner la vidéo GoPro et le fichier de calibration.")
            return

        mode = self.tracking_mode.currentData()

        use_gopro2 = self.gopro2_group.isChecked()
        if use_gopro2:
            capture_path_2 = self.capture_video_2.text()
            calibration_path_2 = self.calibration_file_2.text()
            if not capture_path_2 or not calibration_path_2:
                QMessageBox.warning(
                    self, "Entrée manquante",
                    "Veuillez sélectionner la vidéo et le fichier de calibration de la GoPro 2, "
                    "ou décocher le groupe \"GoPro 2\".",
                )
                return

        try:
            if use_gopro2:
                tracker = DualTracker(capture_path, calibration_path, capture_path_2, calibration_path_2, mode)
            else:
                tracker_class = SfmTracker if mode == "sfm" else Tracker
                tracker = tracker_class(capture_path, calibration_path)
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
            self.tracking_result_file, "Parcourir", "Résultats tracking (*.json *.csv);;Tous les fichiers (*)",
            on_selected=self._auto_preview_tracking,
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
            self._reset_trajectory_plot("Sélectionnez un fichier de tracking pour afficher la trajectoire")
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

        self.export_button = QPushButton("EXPORT")
        self.export_button.setObjectName("primaryButton")
        self.export_button.clicked.connect(self.run_export)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        footer_layout.addLayout(button_layout)

        content_layout.addWidget(footer)

        self.tabs.addTab(content, "3 · Vérification")

    def _load_tracking_positions(self, path):
        path = Path(path)
        if path.suffix.lower() != ".json":
            raise ValueError("L'aperçu 3D ne prend en charge que les fichiers .json pour le moment.")

        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        frames = data["frames"]
        if not frames:
            raise ValueError("Le fichier de tracking ne contient aucune image.")

        matrices = np.array([frame["matrix"] for frame in frames], dtype=np.float64)
        return matrices[:, :3, 3], matrices[:, :3, 2], len(frames)

    def _preview_tracking_file(self, path, notify_errors=True):
        if not path:
            return False

        try:
            positions, forwards, frame_count = self._load_tracking_positions(path)
        except Exception as exc:
            if notify_errors:
                QMessageBox.critical(self, "Erreur de lecture", f"Impossible de lire le fichier de tracking :\n{exc}")
            return False

        if self.verification_canvas is not None:
            self._plot_trajectory(positions, forwards)
            self._set_progress(
                self.verification_progress, self.verification_status, 100,
                f"{frame_count} poses chargées",
            )
        else:
            self._set_progress(
                self.verification_progress, self.verification_status, 100,
                f"{frame_count} poses (installez matplotlib pour l'aperçu 3D)",
            )
        return True

    def _auto_preview_tracking(self, path):
        self._preview_tracking_file(path, notify_errors=True)

    def run_export(self):
        result_path = self.tracking_result_file.text()
        if not result_path:
            QMessageBox.warning(self, "Entrée manquante", "Veuillez sélectionner un fichier de résultat de tracking.")
            return

        if not self._preview_tracking_file(result_path, notify_errors=True):
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self, "Exporter le fichier de tracking", Path(result_path).name, "JSON (*.json)",
        )
        if not output_path:
            return

        try:
            shutil.copyfile(result_path, output_path)
        except Exception as exc:
            QMessageBox.critical(self, "Erreur d'export", str(exc))
            return

        QMessageBox.information(self, "Export terminé", f"Fichier exporté :\n{output_path}")
