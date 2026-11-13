"""mb3d from Python: 3D fractals of Mandelbulb3D, calculated by mb3d-rs.

    import mb3d

    with mb3d.Engine() as engine:
        scene = engine.preset("Amazing Box")
        scene.set(zoom=0.3, iterations=12)
        scene.render(width=1280, file="box.png")

The engine is the program `mb3d` (mb3d-rs), started as `mb3d serve` and
kept running: this module only talks to it.  It is looked for in the
`program` argument, the environment variable MB3D, then on the PATH.
Only Python's standard library is used.  EXPERIMENTAL, like `mb3d serve`.
"""

import base64
import json
import os
import shutil
import subprocess
import threading

__all__ = ["Engine", "Scene", "Picture", "Mb3dError", "find_program"]
__version__ = "0.1.0"

PROTOCOL = 1


class Mb3dError(Exception):
    """What the engine answered instead of a result."""


def find_program(program=None):
    """The path of the `mb3d` program, or an error that says where it was looked for."""
    for candidate in (program, os.environ.get("MB3D")):
        if candidate:
            if os.path.isfile(candidate):
                return candidate
            raise Mb3dError(f"{candidate}: no such program")
    found = shutil.which("mb3d")
    if found:
        return found
    raise Mb3dError("the program mb3d was not found: pass Engine(program=...), set the environment variable MB3D, or put it on the PATH")


class Engine:
    """A running `mb3d serve`.  Close it (or use `with`) when done."""

    def __init__(self, program=None, cpu=False, formulas=None, maps=None):
        args = [find_program(program), "serve"]
        if cpu:
            args.append("--cpu")
        if formulas:
            args += ["--formulas", str(formulas)]
        if maps:
            args += ["--maps", str(maps)]
        self._proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self._ask_lock = threading.Lock()
        self._write_lock = threading.Lock()
        self._next = 0
        hello = self._ask({"op": "hello"})
        self.version = hello["version"]
        self.gpu = hello["gpu"]
        if hello["protocol"] != PROTOCOL:
            self.close()
            raise Mb3dError(f"mb3d {self.version} speaks protocol {hello['protocol']}, this module protocol {PROTOCOL}")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self):
        """Ends the engine."""
        proc, self._proc = self._proc, None
        if proc is None:
            return
        try:
            proc.stdin.close()
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
            proc.wait()
        proc.stdout.close()

    def _write(self, request):
        if self._proc is None:
            raise Mb3dError("the engine is closed")
        line = (json.dumps(request) + "\n").encode()
        with self._write_lock:
            try:
                self._proc.stdin.write(line)
                self._proc.stdin.flush()
            except OSError as e:
                raise Mb3dError(f"the engine has ended ({e})") from None

    def _ask(self, request, progress=None):
        with self._ask_lock:
            self._next += 1
            request = dict(request, id=self._next)
            self._write(request)
            while True:
                line = self._proc.stdout.readline()
                if not line:
                    raise Mb3dError("the engine has ended")
                answer = json.loads(line)
                if answer.get("id") != request["id"]:
                    continue  # the answer to a cancel
                if answer.get("event") == "progress":
                    if progress:
                        progress(answer["stage"], answer["done"], answer["total"])
                    continue
                if not answer.get("ok"):
                    raise Mb3dError(answer.get("error", "unknown error"))
                return answer

    def cancel(self):
        """Stops the picture being calculated (from another thread): its
        render raises Mb3dError("cancelled")."""
        self._write({"op": "cancel", "id": "cancel"})

    def use_gpu(self, on):
        """Calculate on the graphics card (the default) or the processor."""
        self._ask({"op": "gpu", "on": bool(on)})

    def open(self, file):
        """A parameter file: .m3p, .m3i, MB3D text parameters, a scene text."""
        return Scene(self, self._ask({"op": "open", "file": os.path.abspath(os.fspath(file))}))

    def from_text(self, text):
        """A scene text (Scene.text()) or MB3D text parameters."""
        return Scene(self, self._ask({"op": "open", "text": text}))

    def from_bytes(self, data, name="scene.m3p"):
        """The contents of a parameter file; `name` tells its kind."""
        return Scene(self, self._ask({"op": "open", "data": base64.b64encode(data).decode(), "name": name}))

    def preset(self, formula):
        """A formula by name, with a camera that shows it."""
        return Scene(self, self._ask({"op": "open", "preset": formula}))

    def formulas(self):
        """The names of all formulas."""
        return self._ask({"op": "formulas"})["names"]

    def formula_settings(self, name):
        """A formula's settings and their default values."""
        return self._ask({"op": "formulas", "name": name})["settings"]

    def guide(self):
        """Which scene keys do what, as text."""
        return self._ask({"op": "guide"})["text"]


def _value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (list, tuple)):
        return ", ".join(_value(x) for x in v)
    return str(v)


class Scene:
    """A fractal scene held by the engine."""

    def __init__(self, engine, about):
        self._engine = engine
        self._id = about["scene"]
        self._about(about)

    def _about(self, about):
        self.width = about["width"]
        self.height = about["height"]
        self.formulas = [(f["name"], f["iterations"]) for f in about["formulas"]]
        # the same with each formula's place (slot) and its own values
        self.formula_values = about["formulas"]
        self.rotation = about.get("rotation")
        self.notes = about["notes"]

    def _ask(self, op, _progress=None, **members):
        return self._engine._ask(dict(members, op=op, scene=self._id), _progress)

    def text(self):
        """The scene as `key = value` lines."""
        return self._ask("text")["text"]

    def get(self, key):
        """The value of a global key, as text (None if the scene has no such line)."""
        for line in self.text().splitlines():
            if line.startswith("["):
                break
            k, sep, v = line.partition("=")
            if sep and k.strip() == key:
                return v.strip()
        return None

    def set(self, changes=None, **keys):
        """Changes global keys: `key = value` lines, a dict, or keywords
        (scene.set(zoom=1.2, rotation=(10, 20, 0)))."""
        lines = []
        if isinstance(changes, str):
            lines.append(changes)
        elif changes:
            keys = dict(changes, **keys)
        lines += [f"{k} = {_value(v)}" for k, v in keys.items()]
        self._about(self._ask("set", changes="\n".join(lines)))
        return self

    def set_formula(self, slot, values=None, iterations=None):
        """Changes a formula's own values: scene.set_formula(0, {"Scale": 2.2}).
        `slot` is the formula's place, as scene.formula_values tells it."""
        members = {"slot": slot, "settings": dict(values or {})}
        if iterations is not None:
            members["iterations"] = iterations
        self._about(self._ask("formula", **members))
        return self

    def resize(self, width=None, height=None):
        """Another picture size; one of the two follows the proportions."""
        members = {k: v for k, v in (("width", width), ("height", height)) if v}
        self._about(self._ask("resize", **members))
        return self

    def copy(self):
        """A second scene with the same settings."""
        return Scene(self._engine, self._ask("copy"))

    def save(self, file):
        """Writes a .m3p (a .m3s or .txt name: the scene text)."""
        self._ask("save", file=os.path.abspath(os.fspath(file)))

    def close(self):
        """Forgets the scene in the engine."""
        self._ask("close")

    def render(self, width=None, height=None, file=None, depth_file=None, depth=False, pixels=False, progress=None):
        """Calculates the picture.

        width, height: for this picture only (one follows the proportions).
        file, depth_file: PNG files to write.
        pixels: return the raw pixels (Picture.rgb) instead of a PNG.
        depth: return the depth too.
        progress: a function (stage, done, total) called while it runs.

        Without `file` the picture comes back in the Picture (png or rgb).
        """
        members = {k: v for k, v in (("width", width), ("height", height)) if v}
        if file:
            members["file"] = os.path.abspath(os.fspath(file))
        if depth_file:
            members["depth_file"] = os.path.abspath(os.fspath(depth_file))
        if pixels:
            members["format"] = "rgb"
        elif depth and file:
            members["format"] = "png"
        if depth:
            members["depth"] = True
        if progress:
            members["progress"] = True
        return Picture(self._ask("render", progress, **members))


class Picture:
    """A calculated picture."""

    def __init__(self, answer):
        self.width = answer["width"]
        self.height = answer["height"]
        self.seconds = answer["seconds"]
        self.device = answer["device"]
        self.file = answer.get("file")
        self.depth_file = answer.get("depth_file")
        d = lambda k: base64.b64decode(answer[k]) if k in answer else None
        # the picture as the bytes of a PNG file
        self.png = d("png")
        # the depth as a 16 bit greyscale PNG
        self.depth_png = d("depth_png")
        # raw pixels: 3 bytes each, rows from the top (render(pixels=True))
        self.rgb = d("rgb")
        # raw depth: 2 bytes each, little endian; 65535 nearest, 0 background
        self.depth = d("depth")

    def save(self, file):
        """Writes the PNG to a file."""
        if self.png is None:
            raise Mb3dError("this picture holds no PNG (rendered with pixels=True or into a file)")
        with open(file, "wb") as f:
            f.write(self.png)

    def _repr_png_(self):
        # a notebook shows the picture itself
        return self.png

    def __repr__(self):
        return f"<mb3d.Picture {self.width}x{self.height}, {self.seconds} s, {self.device}>"
