"""The smallest web use: a page with one fractal picture.

    python server.py      then open http://127.0.0.1:8766

GET /fractal.png?formula=Amazing%20Box&zoom=0.3&width=640 gives a PNG.
"""

import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, "..", "..", "python"))
import mb3d

engine = mb3d.Engine()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            if url.path == "/fractal.png":
                scene = engine.preset(q.get("formula", "Amazing Box"))
                scene.set(zoom=float(q.get("zoom", 0.17)))
                body, kind = scene.render(width=min(int(q.get("width", 640)), 1920)).png, "image/png"
                scene.close()
            else:
                with open(os.path.join(here, "index.html"), "rb") as f:
                    body, kind = f.read(), "text/html; charset=utf-8"
            status = 200
        except (mb3d.Mb3dError, ValueError) as e:
            body, kind, status = str(e).encode(), "text/plain; charset=utf-8", 400
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


print("open http://127.0.0.1:8766")
try:
    HTTPServer(("127.0.0.1", 8766), Handler).serve_forever()
except KeyboardInterrupt:
    engine.close()
