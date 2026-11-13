"""mb3d from Python: 3D fractals of Mandelbulb3D, calculated by mb3d-rs.

    import mb3d

    with mb3d.Engine() as engine:
        scene = engine.preset("Amazing Box")
        scene.set(zoom=0.3, iterations=12)
        scene.render(width=1280, file="box.png")

The engine is the library `libmb3d`, loaded into this program: nothing is
started and nothing else is installed.  An installed package carries the
library and the formula and map folders; otherwise it is looked for in the
`library` argument, the environment variable LIBMB3D, then in this
repository's ffi/target/release.  Only Python's standard library is used.
EXPERIMENTAL.
"""

import base64
import ctypes
import json
import os
import sys
import threading

__all__ = ["Engine", "Scene", "Picture", "Mb3dError", "find_library"]
__version__ = "0.2.0"

PROTOCOL = 1

_here = os.path.dirname(os.path.abspath(__file__))
_NAME = {"win32": "mb3d.dll", "darwin": "libmb3d.dylib"}.get(sys.platform, "libmb3d.so")
_EVENT = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_char_p)
_lock = threading.Lock()
_libraries = {}


class Mb3dError(Exception):
    """What the engine answered instead of a result."""


def find_library(library=None):
    """The path of the library libmb3d, or an error that says where it was looked for."""
    for candidate in (library, os.environ.get("LIBMB3D")):
        if candidate:
            if os.path.isfile(candidate):
                return os.path.abspath(candidate)
            raise Mb3dError(f"{candidate}: no such library")
    for folder in (os.path.join(_here, "lib"), os.path.join(_here, "..", "..", "ffi", "target", "release")):
        candidate = os.path.join(folder, _NAME)
        if os.path.isfile(candidate):
            return os.path.abspath(candidate)
    raise Mb3dError(f"the library {_NAME} was not found: install the package for this system, pass Engine(library=...) or set the environment variable LIBMB3D")


def _load(path):
    """The library, loaded once, with the formula and map folders that came with the package."""
    with _lock:
        lib = _libraries.get(path)
        if lib is None:
            lib = ctypes.CDLL(path)
            P, text = ctypes.c_void_p, ctypes.c_char_p
            for name, result, arguments in (
                ("mb3d_last_error", text, []),
                ("mb3d_finish", None, []),
                ("mb3d_add_formula_folder", ctypes.c_int, [text]),
                ("mb3d_add_map_folder", ctypes.c_int, [text]),
                ("mb3d_session_new", P, []),
                ("mb3d_session_request", P, [P, text, _EVENT, P]),
                ("mb3d_session_cancel", None, [P]),
                ("mb3d_session_free", None, [P]),
                ("mb3d_string_free", None, [P]),
            ):
                f = getattr(lib, name)
                f.restype, f.argtypes = result, arguments
            data = os.path.join(_here, "data")
            for folder, add in (("M3Formulas", lib.mb3d_add_formula_folder), ("EM_JIT_M3Formulas", lib.mb3d_add_formula_folder), ("M3Maps", lib.mb3d_add_map_folder)):
                if os.path.isdir(os.path.join(data, folder)):
                    add(os.fsencode(os.path.join(data, folder)))
            _libraries[path] = lib
        return lib


class Engine:
    """The engine with the scenes it has open.  Close it (or use `with`) when done.

    cpu: calculate on the processor only (otherwise the graphics card helps
    where there is one).  formulas, maps: further folders with formula files
    (.m3f) and map pictures.  library: the path of libmb3d."""

    def __init__(self, library=None, cpu=False, formulas=None, maps=None):
        self._lib = _load(find_library(library))
        if formulas:
            self._lib.mb3d_add_formula_folder(os.fsencode(os.path.abspath(os.fspath(formulas))))
        if maps:
            self._lib.mb3d_add_map_folder(os.fsencode(os.path.abspath(os.fspath(maps))))
        self._session = self._lib.mb3d_session_new()
        if not self._session:
            raise Mb3dError(self._lib.mb3d_last_error().decode())
        self._ask_lock = threading.Lock()
        hello = self._ask({"op": "hello"})
        self.version = hello["version"]
        self.gpu = hello["gpu"]
        if hello["protocol"] != PROTOCOL:
            self.close()
            raise Mb3dError(f"mb3d {self.version} speaks protocol {hello['protocol']}, this module protocol {PROTOCOL}")
        self._ask({"op": "gpu", "on": not cpu})

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self):
        """Ends the engine: its scenes are forgotten."""
        with self._ask_lock:
            session, self._session = self._session, None
            if session:
                self._lib.mb3d_session_free(session)
                self._lib.mb3d_finish()  # (waits for the graphics card's compiles)

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def _ask(self, request, progress=None):
        with self._ask_lock:
            if not self._session:
                raise Mb3dError("the engine is closed")

            def event(_, line):
                if progress:
                    e = json.loads(line)
                    if e.get("event") == "progress":
                        progress(e["stage"], e["done"], e["total"])

            pointer = self._lib.mb3d_session_request(self._session, json.dumps(request).encode(), _EVENT(event), None)
            if not pointer:
                raise Mb3dError(self._lib.mb3d_last_error().decode())
            try:
                answer = json.loads(ctypes.string_at(pointer))
            finally:
                self._lib.mb3d_string_free(pointer)
            if not answer.get("ok"):
                raise Mb3dError(answer.get("error", "unknown error"))
            return answer

    def cancel(self):
        """Stops the picture being calculated (from another thread): its
        render raises Mb3dError("cancelled")."""
        if self._session:
            self._lib.mb3d_session_cancel(self._session)

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
