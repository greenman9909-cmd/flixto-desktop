# Flixto Desktop ⚡

> **Native Ad-Free Streaming Engine & Standalone Windows Player for Movies, TV Shows, and Anime.**

[![Platform](https://img.shields.io/badge/Platform-Windows_11_%2F_10-blue.svg)](https://github.com/greenman9909-cmd/flixto-desktop)
[![Engine](https://img.shields.io/badge/Engine-QtMultimedia_%2F_DirectX_WMF-red.svg)](https://github.com/greenman9909-cmd/flixto-desktop)
[![Ads](https://img.shields.io/badge/Ads-Zero_%2F_Eradicated-success.svg)](https://github.com/greenman9909-cmd/flixto-desktop)

---

## 🌟 Overview

Flixto Desktop bypasses third-party embed iframes and browser webviews that plague streaming websites with popunders, redirects, and malicious scripts. 

Instead of opening ad-ridden iframes, Flixto Desktop uses a reverse-engineered **XSalsa20-Poly1305** token engine to communicate directly with upstream streaming providers, extracting raw master video streams (1080p, 720p, 480p) and rendering them inside a 100% native hardware-accelerated media player.

## 🚀 Key Features

- **No WebView / Zero Ads**: No iframes, no banners, no popups, no redirects.
- **Master Quality**: Direct 1080p / 720p / 480p stream resolution.
- **Hardware Acceleration**: Windows Media Foundation & DirectX video rendering at 60fps.
- **Instant Seeking**: Spacebar for Play/Pause, `Left`/`Right` arrow keys for ±10s seeking, `F` or double-click for Fullscreen.
- **Multi-Language Subtitles**: Automatic subtitle extraction across 15+ languages.
- **Full TMDb Catalogue**: Live search and browsing for trending movies, television series, and anime.

---

## 🛠️ Building & Running from Source

### Prerequisites
- Python 3.10+
- Windows 10 / 11

### Installation
```bash
git clone https://github.com/greenman9909-cmd/flixto-desktop.git
cd flixto-desktop
pip install -r requirements.txt
```

### Launch Desktop App
```bash
python flixto_desktop.py
```

### Build Standalone Executable (.exe)
```bash
python -m PyInstaller Flixto.spec
```
The output executable will be created at `dist/Flixto.exe`.

---

## 📦 Architecture

- **`flixto_desktop.py`**: Main Qt6 dark-themed application window with TMDb integration.
- **`player_window.py`**: Dedicated Ad-Free video player using `PySide6.QtMultimedia` and `QVideoWidget`.
- **`flixto_resolver.py`**: Stream decryption and upstream resolver.
- **`web-client/`**: Authentic production SPA frontend ripped from Flixto with ad scripts removed.
