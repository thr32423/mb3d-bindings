"""The explorer's back end in Python.   python server.py   then open http://127.0.0.1:8765

The page (index.html) asks this small web server, which asks the mb3d engine
through the Python module.  It listens on this computer only.
"""

import json
import os
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, "..", "..", "python"))
import mb3d

engine = mb3d.Engine()
scene = engine.preset("Amazing Box")
progress = {"stage": "", "done": 0, "total": 0}
latest = 0  # the newest picture the page asked for (its `seq`)
order = threading.Lock()


def about(s):
    return {"width": s.width, "height": s.height, "formulas": s.formulas, "rotation": s.rotation, "notes": s.notes, "text": s.text()}


class Handler(BaseHTTPRequestHandler):
    def send(self, body, kind="application/json", status=200, headers=()):
        if not isinstance(body, bytes):
            body = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        for k, v in headers:
            self.send_header(k, str(v))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        try:
            path = self.path.partition("?")[0]
            if path == "/":
                with open(os.path.join(here, "index.html"), "rb") as f:
                    self.send(f.read(), "text/html; charset=utf-8")
            elif path == "/api/info":
                self.send({"version": engine.version, "formulas": engine.formulas()})
            elif path == "/api/progress":
                self.send(progress)
            elif path == "/api/m3p":
                with tempfile.TemporaryDirectory() as d:
                    scene.save(os.path.join(d, "scene.m3p"))
                    with open(os.path.join(d, "scene.m3p"), "rb") as f:
                        self.send(f.read(), "application/octet-stream")
            else:
                self.send({"error": "not found"}, status=404)
        except mb3d.Mb3dError as e:
            self.send({"error": str(e)}, status=400)

    def do_POST(self):
        global scene, latest
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            path = self.path.partition("?")[0]
            if path == "/api/open":
                if "preset" in body:
                    new = engine.preset(body["preset"])
                elif "text" in body:
                    new = engine.from_text(body["text"])
                else:
                    import base64
                    new = engine.from_bytes(base64.b64decode(body["data"]), body.get("name", "scene.m3p"))
                with order:
                    old, scene, latest = scene, new, 0
                old.close()
                self.send(about(new))
            elif path == "/api/render":
                with order:
                    # the page counts its requests: one that arrives after a
                    # newer one is dropped (each carries all the changes)
                    newest = body.get("seq", latest + 1) >= latest
                    latest = max(latest, body.get("seq", latest + 1))
                    if newest:
                        engine.cancel()  # a picture still on its way is not wanted any more
                if body.get("changes") and newest:
                    scene.set(body["changes"])
                if not newest:
                    raise mb3d.Mb3dError("cancelled")

                def report(stage, done, total):
                    progress.update(stage=stage, done=done, total=total)

                p = scene.render(width=body.get("width"), progress=report if body.get("progress") else None)
                self.send(p.png, "image/png", headers=[("X-Width", p.width), ("X-Height", p.height), ("X-Seconds", p.seconds), ("X-Device", p.device)])
            else:
                self.send({"error": "not found"}, status=404)
        except mb3d.Mb3dError as e:
            self.send({"error": str(e)}, status=409 if str(e) == "cancelled" else 400)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"mb3d {engine.version}: open http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        engine.close()
