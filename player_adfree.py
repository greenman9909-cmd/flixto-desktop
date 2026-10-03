import sys
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import (
    QWebEngineProfile, QWebEnginePage, QWebEngineSettings
)

SERVERS = [
    {"name": "Server 1 (VidLink Auto)", "url_m": "https://vidlink.pro/movie/{id}?autoplay=true", "url_tv": "https://vidlink.pro/tv/{id}/{s}/{e}?autoplay=true"},
    {"name": "Server 2 (Videasy HD)", "url_m": "https://player.videasy.to/movie/{id}?color=ff3d47&autoplay=true", "url_tv": "https://player.videasy.to/tv/{id}/{s}/{e}?color=ff3d47&autoplay=true"},
    {"name": "Server 3 (VidSrc.to)", "url_m": "https://vidsrc.to/embed/movie/{id}?autoplay=1", "url_tv": "https://vidsrc.to/embed/tv/{id}/{s}/{e}?autoplay=1"},
    {"name": "Server 4 (VidSrc PM)", "url_m": "https://vidsrc.pm/embed/movie?tmdb={id}&autoplay=1", "url_tv": "https://vidsrc.pm/embed/tv?tmdb={id}&season={s}&episode={e}&autoplay=1"},
    {"name": "Server 5 (MultiEmbed)", "url_m": "https://multiembed.mov/?video_id={id}&tmdb=1&autoplay=1", "url_tv": "https://multiembed.mov/?video_id={id}&tmdb=1&s={s}&e={e}&autoplay=1"},
]

AD_BLOCK_DOMAINS = [
    "adexchangerapid.com", "popads.net", "adsterra.com", "propellerads.com",
    "bancadeltempoidea.org", "intellipopup.com", "xgrowth.pro", "histats.com",
    "syndication.exdynsrv.com", "deloton.com", "mndtrk.com", "adnxs.com",
    "ad-delivery.net", "trafficfactory.biz", "bet365.com", "1xbet.com",
    "clkmr.com", "clickadu.com", "hilltopads.net", "turnstile"
]

KILL_POPUPS_SCRIPT = """
(function() {
    window.open = function() { console.log('[AdBlock] Blocked window.open popup'); return null; };
    window.alert = function() { return null; };
    window.confirm = function() { return true; };
    window.prompt = function() { return null; };

    // Block top redirects
    try {
        Object.defineProperty(window, 'location', {
            configurable: false,
            writable: false
        });
    } catch(e) {}

    // Remove ad overlays
    setInterval(function() {
        var selectors = [
            'iframe[src*="adexchangerapid"]', 'iframe[src*="pop"]',
            'div[class*="banner"]', 'div[id*="container-"]',
            'a[target="_blank"][href*="ad"]'
        ];
        selectors.forEach(function(sel) {
            document.querySelectorAll(sel).forEach(function(el) {
                el.remove();
            });
        });
    }, 1000);
})();
"""

class AdFreeWebPage(QWebEnginePage):
    def createWindow(self, _type):
        print("[AdBlock] BLOCKED POPUP WINDOW REQUEST!")
        return None

class FlixtoAdFreePlayer(QMainWindow):
    def __init__(self, title="Flixto Stream", media_type="movie", tmdb_id=550, season=1, episode=1):
        super().__init__()
        self.media_type = media_type
        self.tmdb_id = tmdb_id
        self.season = season
        self.episode = episode
        self.title_str = title
        self.server_idx = 0

        self.setWindowTitle(f"Flixto Player — {title}")
        self.resize(1180, 720)
        self.setStyleSheet("""
            QMainWindow { background-color: #0a0a0b; }
            QWidget { background-color: #0a0a0b; color: #fff; font-family: 'Segoe UI', sans-serif; }
            QPushButton {
                background-color: #141416; color: #fff; border: 1px solid #27272a;
                border-radius: 6px; padding: 6px 14px; font-weight: 600; font-size: 12px;
            }
            QPushButton:hover { background-color: #ff3d47; border-color: #ff3d47; }
            QComboBox {
                background-color: #141416; border: 1px solid #27272a;
                border-radius: 6px; padding: 4px 10px; color: #fff; font-size: 12px;
            }
        """)

        # Setup WebEngine View
        self.view = QWebEngineView(self)
        self.custom_page = AdFreeWebPage(self.view)
        self.view.setPage(self.custom_page)

        # Settings
        settings = self.view.settings()
        settings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, False)

        # Inject Adblock JS on page load
        self.view.loadFinished.connect(self.on_page_loaded)

        # Top Bar
        top_bar = QWidget(self)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(12, 8, 12, 8)

        self.title_lbl = QLabel(f"▶ {title}", self)
        self.title_lbl.setStyleSheet("font-weight: bold; font-size: 13px; color: #fff;")
        top_layout.addWidget(self.title_lbl)

        top_layout.addSpacing(16)
        top_layout.addWidget(QLabel("Server:", self))
        self.server_cb = QComboBox(self)
        for s in SERVERS:
            self.server_cb.addItem(s["name"])
        self.server_cb.currentIndexChanged.connect(self.switch_server)
        top_layout.addWidget(self.server_cb)

        top_layout.addStretch()

        badge = QLabel("🛡 ZERO-ADS SHIELD ACTIVE", self)
        badge.setStyleSheet("color: #4ade80; font-weight: bold; font-family: monospace; font-size: 11px;")
        top_layout.addWidget(badge)

        top_layout.addSpacing(12)
        self.fs_btn = QPushButton("Fullscreen [F]", self)
        self.fs_btn.clicked.connect(self.toggle_fullscreen)
        top_layout.addWidget(self.fs_btn)

        # Main Layout
        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(top_bar)
        main_layout.addWidget(self.view, stretch=1)

        # Shortcuts
        QShortcut(QKeySequence("F"), self, self.toggle_fullscreen)
        QShortcut(QKeySequence("Escape"), self, self.exit_fullscreen)

        # Load first server
        self.load_current_server()

    def get_server_url(self, s_dict):
        if self.media_type == "tv":
            return s_dict["url_tv"].format(id=self.tmdb_id, s=self.season, e=self.episode)
        return s_dict["url_m"].format(id=self.tmdb_id)

    def load_current_server(self):
        s_dict = SERVERS[self.server_idx]
        url = self.get_server_url(s_dict)
        print(f"[Player] Loading: {url}")
        self.view.setUrl(QUrl(url))

    def switch_server(self, idx):
        self.server_idx = idx
        self.load_current_server()

    def on_page_loaded(self, ok):
        if ok:
            print("[Player] Page loaded. Injecting Ad-Shield scripts...")
            self.view.page().runJavaScript(KILL_POPUPS_SCRIPT)

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
    p = FlixtoAdFreePlayer("Fight Club (1999)", "movie", 550)
    p.show()
    sys.exit(app.exec())
