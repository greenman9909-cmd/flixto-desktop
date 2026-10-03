# language: Python, file: server.py, target: Windows 11
import http.server
import socketserver
import os
import urllib.parse
from pathlib import Path

PORT = 3005
ROOT_DIR = Path(__file__).parent.resolve()

class SPAServerHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT_DIR), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        clean_path = parsed.path.lstrip("/")
        local_file = ROOT_DIR / clean_path

        # If it's a real file that exists on disk, serve it directly
        if clean_path and local_file.is_file():
            return super().do_GET()

        # For assets that exist inside assets directory
        if clean_path.startswith("assets/") and local_file.is_file():
            return super().do_GET()

        # Fallback to SPA root index.html for all client-side routes (e.g. /watch/movie/123, /movies, /shows, /search)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        index_file = ROOT_DIR / "index.html"
        with open(index_file, "rb") as f:
            self.wfile.write(f.read())

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), SPAServerHandler) as httpd:
        print(f"[*] Authentic Flixto SPA Server listening on http://127.0.0.1:{PORT}")
        httpd.serve_forever()
