"""Local preview of public/ with the same clean URLs as the live Caddy config.

    python serve.py            ->  http://localhost:8000
    python serve.py 9000       ->  another port

/cv serves cv.html, /projects serves projects.html, unknown paths get 404.html.
Standard library only; for previewing, not for production.
"""
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PUBLIC = Path(__file__).resolve().parent / "public"


class CleanURLHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        if path != "/" and not path.endswith("/") and "." not in path.rsplit("/", 1)[-1]:
            if (PUBLIC / (path.lstrip("/") + ".html")).is_file():
                self.path = path + ".html"
        target = Path(self.translate_path(self.path))
        if not target.exists():
            self.send_response(404)
            body = (PUBLIC / "404.html").read_bytes()
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            from io import BytesIO
            return BytesIO(body)
        return super().send_head()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    handler = partial(CleanURLHandler, directory=str(PUBLIC))
    print(f"serving {PUBLIC} at http://localhost:{port}  (Ctrl+C to stop)")
    ThreadingHTTPServer(("127.0.0.1", port), handler).serve_forever()
