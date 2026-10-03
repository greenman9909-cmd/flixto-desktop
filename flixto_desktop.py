import sys
import os
import json
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import Qt, QThread, Signal, Slot, QSize, QTimer
from PySide6.QtGui import QIcon, QPixmap, QFont, QColor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QScrollArea, QGridLayout,
    QFrame, QDialog, QComboBox, QMessageBox, QProgressBar
)

from player_window import FlixtoNativePlayer
from flixto_resolver import resolve_stream

TMDB_API_KEY = "4a1e36ee37d8dbb5691e45ecf61c7dcb"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"
TMDB_BACKDROP_BASE = "https://image.tmdb.org/t/p/w780"

class TMDbWorker(QThread):
    results_ready = Signal(list, str)

    def __init__(self, endpoint, category):
        super().__init__()
        self.endpoint = endpoint
        self.category = category

    def run(self):
        try:
            req = urllib.request.Request(
                self.endpoint,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                items = data.get('results', [])
                self.results_ready.emit(items, self.category)
        except Exception as e:
            print(f"[TMDb Error]: {e}")
            self.results_ready.emit([], self.category)

class StreamResolveWorker(QThread):
    stream_resolved = Signal(dict)

    def __init__(self, media_type, tmdb_id, season=1, episode=1):
        super().__init__()
        self.media_type = media_type
        self.tmdb_id = tmdb_id
        self.season = season
        self.episode = episode

    def run(self):
        res = resolve_stream(self.media_type, self.tmdb_id, self.season, self.episode)
        self.stream_resolved.emit(res)

class MediaCard(QFrame):
    clicked = Signal(dict)

    def __init__(self, item_data):
        super().__init__()
        self.item_data = item_data
        self.setFixedSize(170, 290)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            MediaCard {
                background-color: #141416;
                border: 1px solid #27272a;
                border-radius: 8px;
            }
            MediaCard:hover {
                border: 1px solid #ff3d47;
                background-color: #1c1c1f;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Poster Image
        self.poster_label = QLabel(self)
        self.poster_label.setFixedSize(158, 220)
        self.poster_label.setStyleSheet("background-color: #1f1f23; border-radius: 6px;")
        self.poster_label.setAlignment(Qt.AlignCenter)
        self.poster_label.setText("Loading...")
        layout.addWidget(self.poster_label)

        # Title
        title_text = item_data.get('title') or item_data.get('name') or "Untitled"
        self.title_label = QLabel(title_text, self)
        self.title_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 11px;")
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(32)
        layout.addWidget(self.title_label)

        # Subtitle / Year / Rating
        year = (item_data.get('release_date') or item_data.get('first_air_date') or "")[:4]
        rating = item_data.get('vote_average', 0.0)
        meta_label = QLabel(f"★ {rating:.1f}  •  {year}", self)
        meta_label.setStyleSheet("color: #a1a1aa; font-size: 10px;")
        layout.addWidget(meta_label)

    def set_poster(self, pixmap):
        scaled = pixmap.scaled(158, 220, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.poster_label.setPixmap(scaled)
        self.poster_label.setText("")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.item_data)

class MediaDetailDialog(QDialog):
    def __init__(self, parent, item_data):
        super().__init__(parent)
        self.item_data = item_data
        self.media_type = "tv" if ("first_air_date" in item_data or "name" in item_data) else "movie"
        self.tmdb_id = item_data.get("id")
        self.title_text = item_data.get("title") or item_data.get("name") or "Untitled"

        self.setWindowTitle(f"Flixto — {self.title_text}")
        self.resize(750, 480)
        self.setStyleSheet("""
            QDialog {
                background-color: #0e0e11;
                color: #ffffff;
            }
            QLabel {
                color: #d4d4d8;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton {
                background-color: #ff3d47;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                border-radius: 6px;
                padding: 10px 20px;
                border: none;
            }
            QPushButton:hover {
                background-color: #e0242e;
            }
            QComboBox {
                background-color: #1a1a1e;
                border: 1px solid #3f3f46;
                border-radius: 6px;
                color: #fff;
                padding: 6px 10px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Left: Poster
        self.poster = QLabel(self)
        self.poster.setFixedSize(200, 300)
        self.poster.setStyleSheet("background-color: #18181b; border-radius: 8px;")
        layout.addWidget(self.poster)

        # Right: Info & Controls
        info_layout = QVBoxLayout()
        layout.addLayout(info_layout, stretch=1)

        title_lbl = QLabel(self.title_text, self)
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 800; color: #fff;")
        title_lbl.setWordWrap(True)
        info_layout.addWidget(title_lbl)

        rating = item_data.get('vote_average', 0.0)
        year = (item_data.get('release_date') or item_data.get('first_air_date') or "")[:4]
        type_str = "TV Series" if self.media_type == "tv" else "Feature Film"
        meta_lbl = QLabel(f"★ {rating:.1f} / 10  •  {year}  •  {type_str}", self)
        meta_lbl.setStyleSheet("color: #ff3d47; font-weight: 600; font-size: 12px;")
        info_layout.addWidget(meta_lbl)

        overview_lbl = QLabel(item_data.get('overview', 'No synopsis available.'), self)
        overview_lbl.setWordWrap(True)
        overview_lbl.setStyleSheet("color: #a1a1aa; font-size: 12px; margin-top: 8px;")
        overview_lbl.setMaximumHeight(110)
        info_layout.addWidget(overview_lbl)

        # TV Episode Controls
        if self.media_type == "tv":
            ep_row = QHBoxLayout()
            ep_row.addWidget(QLabel("Season:", self))
            self.season_cb = QComboBox(self)
            for s in range(1, 15):
                self.season_cb.addItem(f"Season {s}", s)
            ep_row.addWidget(self.season_cb)

            ep_row.addWidget(QLabel("Episode:", self))
            self.episode_cb = QComboBox(self)
            for e in range(1, 35):
                self.episode_cb.addItem(f"Episode {e}", e)
            ep_row.addWidget(self.episode_cb)
            info_layout.addLayout(ep_row)

        info_layout.addSpacing(10)

        # Status label
        self.status_lbl = QLabel("Direct stream routing ready. Zero ads.", self)
        self.status_lbl.setStyleSheet("color: #4ade80; font-family: monospace; font-size: 11px;")
        info_layout.addWidget(self.status_lbl)

        # Play Button
        self.play_btn = QPushButton("▶ Watch Now (Instant Ad-Free Stream)", self)
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.clicked.connect(self.start_stream)
        info_layout.addWidget(self.play_btn)

        info_layout.addStretch()

        # Load poster async
        poster_path = item_data.get('poster_path')
        if poster_path:
            self.load_poster(f"{TMDB_IMAGE_BASE}{poster_path}")

    def load_poster(self, url):
        def fetch():
            try:
                data = urllib.request.urlopen(url, timeout=5).read()
                pm = QPixmap()
                pm.loadFromData(data)
                QTimer.singleShot(0, lambda: self.poster.setPixmap(pm.scaled(200, 300, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)))
            except Exception:
                pass
        ThreadPoolExecutor(max_workers=1).submit(fetch)

    def start_stream(self):
        self.play_btn.setEnabled(False)
        self.play_btn.setText("⚡ Resolving direct stream...")
        season = self.season_cb.currentData() if self.media_type == "tv" else 1
        episode = self.episode_cb.currentData() if self.media_type == "tv" else 1

        self.worker = StreamResolveWorker(self.media_type, self.tmdb_id, season, episode)
        self.worker.stream_resolved.connect(self.on_stream_resolved)
        self.worker.start()

    def on_stream_resolved(self, res):
        self.play_btn.setEnabled(True)
        self.play_btn.setText("▶ Watch Now (Instant Ad-Free Stream)")

        if not res.get('success') or not res.get('streams'):
            QMessageBox.warning(self, "No Stream", "Could not resolve a direct stream for this title.")
            return

        stream = res['streams'][0]
        stream_url = stream.get('url')
        print(f"[Flixto] Launching native player with: {stream_url}")

        self.player_window = FlixtoNativePlayer(
            title=f"{self.title_text} ({stream.get('quality', 'HD')})",
            stream_url=stream_url
        )
        self.player_window.show()
        self.accept()

class FlixtoDesktopApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flixto — Ad-Free Desktop Streaming Engine")
        self.resize(1280, 800)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0a0a0b;
            }
            QWidget {
                background-color: #0a0a0b;
                color: #ffffff;
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }
            QLineEdit {
                background-color: #141416;
                border: 1px solid #27272a;
                border-radius: 8px;
                padding: 8px 14px;
                color: #ffffff;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #ff3d47;
            }
            QPushButton.tab-btn {
                background-color: transparent;
                border: none;
                color: #a1a1aa;
                font-size: 13px;
                font-weight: 600;
                padding: 6px 12px;
                border-radius: 6px;
            }
            QPushButton.tab-btn:hover {
                color: #ffffff;
                background-color: #18181b;
            }
            QPushButton.tab-btn[active="true"] {
                color: #ffffff;
                background-color: #ff3d47;
            }
            QScrollArea {
                border: none;
            }
        """)

        # Main Layout
        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(24, 16, 24, 16)
        main_layout.setSpacing(16)

        # Header Bar
        header = QHBoxLayout()
        logo_lbl = QLabel("FLIXTO", self)
        logo_lbl.setStyleSheet("font-size: 24px; font-weight: 900; color: #ff3d47; letter-spacing: 1px;")
        header.addWidget(logo_lbl)

        header.addSpacing(24)

        # Tabs
        self.tabs = {}
        for tab_name, key in [("Trending Movies", "trending_movies"), ("Popular Series", "popular_tv"), ("Top Anime", "anime")]:
            btn = QPushButton(tab_name, self)
            btn.setProperty("class", "tab-btn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self.switch_category(k))
            self.tabs[key] = btn
            header.addWidget(btn)

        header.addStretch()

        # Search box
        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText("Search movies, TV shows, anime...")
        self.search_box.setFixedWidth(280)
        self.search_box.returnPressed.connect(self.perform_search)
        header.addWidget(self.search_box)

        main_layout.addLayout(header)

        # Status Bar / Section Header
        self.section_lbl = QLabel("Trending Movies", self)
        self.section_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #ffffff;")
        main_layout.addWidget(self.section_lbl)

        # Scroll Area for Media Grid
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(14)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self.grid_container)
        main_layout.addWidget(scroll, stretch=1)

        # Poster loader pool
        self.poster_pool = ThreadPoolExecutor(max_workers=6)

        # Active tab
        self.active_category = "trending_movies"
        self.switch_category("trending_movies")

    def switch_category(self, cat):
        self.active_category = cat
        for k, btn in self.tabs.items():
            btn.setStyleSheet("background-color: #ff3d47; color: #fff;" if k == cat else "background-color: transparent; color: #a1a1aa;")

        if cat == "trending_movies":
            self.section_lbl.setText("Trending Movies — Ad-Free 1080p")
            url = f"https://api.themoviedb.org/3/trending/movie/week?api_key={TMDB_API_KEY}"
        elif cat == "popular_tv":
            self.section_lbl.setText("Popular TV Shows — All Seasons & Episodes")
            url = f"https://api.themoviedb.org/3/trending/tv/week?api_key={TMDB_API_KEY}"
        else:
            self.section_lbl.setText("Top Anime Series")
            url = f"https://api.themoviedb.org/3/discover/tv?api_key={TMDB_API_KEY}&with_genres=16&with_keywords=210024|287501"

        self.worker = TMDbWorker(url, cat)
        self.worker.results_ready.connect(self.populate_grid)
        self.worker.start()

    def perform_search(self):
        query = self.search_box.text().strip()
        if not query:
            return
        self.section_lbl.setText(f"Search Results for: \"{query}\"")
        url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&query={urllib.parse.quote(query)}"
        self.worker = TMDbWorker(url, "search")
        self.worker.results_ready.connect(self.populate_grid)
        self.worker.start()

    def populate_grid(self, items, category):
        # Clear existing cards
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        cols = 6
        for idx, item in enumerate(items):
            if not item.get('poster_path'):
                continue
            card = MediaCard(item)
            card.clicked.connect(self.open_detail)
            row = idx // cols
            col = idx % cols
            self.grid_layout.addWidget(card, row, col)

            # Async fetch poster image
            poster_url = f"{TMDB_IMAGE_BASE}{item['poster_path']}"
            self.poster_pool.submit(self.load_poster_image, card, poster_url)

    def load_poster_image(self, card, url):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = resp.read()
                pm = QPixmap()
                pm.loadFromData(data)
                QTimer.singleShot(0, lambda c=card, p=pm: c.set_poster(p))
        except Exception:
            pass

    def open_detail(self, item_data):
        dlg = MediaDetailDialog(self, item_data)
        dlg.exec()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FlixtoDesktopApp()
    window.show()
    sys.exit(app.exec())
