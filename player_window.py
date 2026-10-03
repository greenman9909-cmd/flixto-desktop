import sys
from PySide6.QtCore import Qt, QUrl, QTime
from PySide6.QtGui import QIcon, QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QComboBox, QSizePolicy
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

class FlixtoNativePlayer(QMainWindow):
    def __init__(self, title="Flixto Stream", stream_url=None):
        super().__init__()
        self.setWindowTitle(f"Flixto Player — {title} (Ad-Free Direct Stream)")
        self.resize(1100, 650)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0a0a0b;
            }
            QWidget {
                background-color: #0a0a0b;
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton {
                background-color: #141416;
                color: #ffffff;
                border: 1px solid #27272a;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #ff3d47;
                border-color: #ff3d47;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #27272a;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #ff3d47;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                width: 14px;
                margin-top: -4px;
                margin-bottom: -4px;
                border-radius: 7px;
            }
            QLabel {
                color: #a1a1aa;
                font-size: 12px;
            }
            QComboBox {
                background-color: #141416;
                border: 1px solid #27272a;
                border-radius: 6px;
                padding: 4px 10px;
                color: #fff;
            }
        """)

        # Player setup
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.85)

        # Main video widget
        self.video_widget = QVideoWidget(self)
        self.player.setVideoOutput(self.video_widget)

        # Controls layout
        self.controls_widget = QWidget(self)
        controls_layout = QVBoxLayout(self.controls_widget)
        controls_layout.setContentsMargins(16, 8, 16, 12)
        controls_layout.setSpacing(8)

        # Timeline row
        time_row = QHBoxLayout()
        self.time_label = QLabel("00:00:00 / 00:00:00", self)
        self.seek_slider = QSlider(Qt.Horizontal, self)
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.sliderMoved.connect(self.set_position)
        time_row.addWidget(self.seek_slider)
        time_row.addWidget(self.time_label)
        controls_layout.addLayout(time_row)

        # Buttons row
        btn_row = QHBoxLayout()
        self.play_btn = QPushButton("Pause", self)
        self.play_btn.clicked.connect(self.toggle_play)
        btn_row.addWidget(self.play_btn)

        self.seek_back_btn = QPushButton("◀◀ -10s", self)
        self.seek_back_btn.clicked.connect(lambda: self.seek_relative(-10000))
        btn_row.addWidget(self.seek_back_btn)

        self.seek_fwd_btn = QPushButton("+10s ▶▶", self)
        self.seek_fwd_btn.clicked.connect(lambda: self.seek_relative(10000))
        btn_row.addWidget(self.seek_fwd_btn)

        btn_row.addSpacing(16)
        vol_label = QLabel("Vol:", self)
        btn_row.addWidget(vol_label)

        self.vol_slider = QSlider(Qt.Horizontal, self)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(85)
        self.vol_slider.setMaximumWidth(100)
        self.vol_slider.valueChanged.connect(lambda v: self.audio_output.setVolume(v / 100.0))
        btn_row.addWidget(self.vol_slider)

        btn_row.addStretch()

        # Quality indicator
        self.quality_label = QLabel("⚡ AD-FREE DIRECT STREAM", self)
        self.quality_label.setStyleSheet("color: #4ade80; font-weight: bold; font-family: monospace;")
        btn_row.addWidget(self.quality_label)

        btn_row.addSpacing(16)
        self.fs_btn = QPushButton("Fullscreen [F]", self)
        self.fs_btn.clicked.connect(self.toggle_fullscreen)
        btn_row.addWidget(self.fs_btn)

        controls_layout.addLayout(btn_row)

        # Central Layout
        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.video_widget, stretch=1)
        main_layout.addWidget(self.controls_widget, stretch=0)

        # Player listeners
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)

        # Keyboard shortcuts
        QShortcut(QKeySequence("Space"), self, self.toggle_play)
        QShortcut(QKeySequence("F"), self, self.toggle_fullscreen)
        QShortcut(QKeySequence("Left"), self, lambda: self.seek_relative(-10000))
        QShortcut(QKeySequence("Right"), self, lambda: self.seek_relative(10000))
        QShortcut(QKeySequence("Escape"), self, self.exit_fullscreen)

        if stream_url:
            self.load_stream(stream_url)

    def load_stream(self, url: str):
        print(f"[Player] Loading direct stream: {url}")
        self.player.setSource(QUrl(url))
        self.player.play()
        self.play_btn.setText("Pause")

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_btn.setText("Play")
        else:
            self.player.play()
            self.play_btn.setText("Pause")

    def seek_relative(self, delta_ms: int):
        new_pos = max(0, min(self.player.duration(), self.player.position() + delta_ms))
        self.player.setPosition(new_pos)

    def set_position(self, slider_val: int):
        if self.player.duration() > 0:
            target_ms = int((slider_val / 1000.0) * self.player.duration())
            self.player.setPosition(target_ms)

    def on_position_changed(self, pos_ms: int):
        dur_ms = self.player.duration()
        if dur_ms > 0:
            val = int((pos_ms / float(dur_ms)) * 1000)
            self.seek_slider.setValue(val)
        pos_str = self.format_time(pos_ms)
        dur_str = self.format_time(dur_ms)
        self.time_label.setText(f"{pos_str} / {dur_str}")

    def on_duration_changed(self, dur_ms: int):
        pos_str = self.format_time(self.player.position())
        dur_str = self.format_time(dur_ms)
        self.time_label.setText(f"{pos_str} / {dur_str}")

    def format_time(self, ms: int) -> str:
        s = ms // 1000
        m = s // 60
        h = m // 60
        return f"{h:02d}:{m % 60:02d}:{s % 60:02d}"

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.fs_btn.setText("Fullscreen [F]")
        else:
            self.showFullScreen()
            self.fs_btn.setText("Exit Fullscreen [Esc]")

    def exit_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.fs_btn.setText("Fullscreen [F]")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = FlixtoNativePlayer(
        title="Test HLS Stream",
        stream_url="https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
    )
    player.show()
    print("Player window shown successfully.")
    sys.exit(app.exec())
