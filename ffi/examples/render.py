"""The C library from Python, without the mb3d program: the pixels come
straight from the engine's memory.

    cargo build --release          (in ffi/)
    python examples/render.py [file.m3p]
"""

import ctypes
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
name = {"win32": "mb3d.dll", "darwin": "libmb3d.dylib"}.get(sys.platform, "libmb3d.so")
lib = ctypes.CDLL(os.environ.get("LIBMB3D") or os.path.join(here, "..", "target", "release", name))

P = ctypes.c_void_p
PROGRESS = ctypes.CFUNCTYPE(ctypes.c_int, P, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_size_t)
for fn, res, args in [
    ("mb3d_last_error", ctypes.c_char_p, []),
    ("mb3d_use_gpu", None, [ctypes.c_int]),
    ("mb3d_finish", None, []),
    ("mb3d_open", P, [ctypes.c_char_p]),
    ("mb3d_preset", P, [ctypes.c_char_p]),
    ("mb3d_scene_set", ctypes.c_int, [P, ctypes.c_char_p]),
    ("mb3d_scene_resize", ctypes.c_int, [P, ctypes.c_uint32, ctypes.c_uint32]),
    ("mb3d_scene_free", None, [P]),
    ("mb3d_render", P, [P, PROGRESS, P]),
    ("mb3d_picture_width", ctypes.c_uint32, [P]),
    ("mb3d_picture_height", ctypes.c_uint32, [P]),
    ("mb3d_picture_rgb", ctypes.POINTER(ctypes.c_uint8), [P]),
    ("mb3d_picture_save_png", ctypes.c_int, [P, ctypes.c_char_p]),
    ("mb3d_picture_free", None, [P]),
]:
    getattr(lib, fn).restype, getattr(lib, fn).argtypes = res, args


def check(result):
    if not result:
        raise SystemExit(lib.mb3d_last_error().decode())
    return result


@PROGRESS
def progress(user, stage, done, total):
    print(f"\r{stage.decode() or 'calculating'} {100 * done // max(total, 1)} %   ", end="", file=sys.stderr)
    return 0


scene = check(lib.mb3d_open(sys.argv[1].encode()) if len(sys.argv) > 1 else lib.mb3d_preset(b"Amazing Box"))
lib.mb3d_use_gpu(1)
lib.mb3d_scene_resize(scene, 640, 480)
picture = check(lib.mb3d_render(scene, progress, None))
w, h = lib.mb3d_picture_width(picture), lib.mb3d_picture_height(picture)
pixels = ctypes.string_at(lib.mb3d_picture_rgb(picture), w * h * 3)  # a copy, e.g. for numpy.frombuffer or PIL.Image.frombytes
print(f"\n{w} x {h}: {len(pixels)} bytes of pixels, the first {tuple(pixels[:3])}")
lib.mb3d_picture_save_png(picture, b"picture.png")
print("picture.png")
lib.mb3d_picture_free(picture)
lib.mb3d_scene_free(scene)
lib.mb3d_finish()
