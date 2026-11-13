"""Builds what people install, for one system, into dist/:

    python tools/package.py --system linux-x64 --data FOLDER [--lib FILE] [--addon FILE]

* mb3d-VERSION-py3-none-TAG.whl      the Python module with libmb3d
* mb3d-VERSION-SYSTEM.tgz            the Node.js module with its add-on
* libmb3d-VERSION-SYSTEM.tar.gz      the C library with its header

FOLDER holds M3Formulas, EM_JIT_M3Formulas and M3Maps (the folder of an
mb3d-rs release); each package carries them.  --lib and --addon default to
what `cargo build --release` leaves in ffi/ and node/.  Only Python's
standard library is used.
"""

import argparse
import base64
import hashlib
import io
import json
import os
import re
import tarfile
import zipfile

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = ("M3Formulas", "EM_JIT_M3Formulas", "M3Maps")
# system: the wheel's platform tag, the library's and the built add-on's file names, npm's os and cpu
SYSTEMS = {
    "linux-x64": ("manylinux_2_28_x86_64", "libmb3d.so", "libmb3d_node.so", "linux", "x64"),
    "windows-x64": ("win_amd64", "mb3d.dll", "mb3d_node.dll", "win32", "x64"),
    "macos-arm64": ("macosx_11_0_arm64", "libmb3d.dylib", "libmb3d_node.dylib", "darwin", "arm64"),
    "macos-x64": ("macosx_10_12_x86_64", "libmb3d.dylib", "libmb3d_node.dylib", "darwin", "x64"),
}


def read(*path):
    with open(os.path.join(root, *path), "rb") as f:
        return f.read()


def data_files(folder):
    """(path inside the package, bytes) of the formula and map folders."""
    for name in DATA:
        top = os.path.join(folder, name)
        if not os.path.isdir(top):
            raise SystemExit(f"{top}: no such folder")
        for here, dirs, names in os.walk(top):
            dirs.sort()
            for n in sorted(names):
                path = os.path.join(here, n)
                with open(path, "rb") as f:
                    yield "data/" + os.path.relpath(path, folder).replace(os.sep, "/"), f.read()


def wheel(version, tag, lib_name, lib, data, out):
    files = [("mb3d/__init__.py", read("python", "mb3d", "__init__.py")), ("mb3d/notebook.py", read("python", "mb3d", "notebook.py")),
             ("mb3d/lib/" + lib_name, lib), ("mb3d/lib/LICENSE", read("ffi", "LICENSE"))]
    files += [("mb3d/" + name, content) for name, content in data]
    info = f"mb3d-{version}.dist-info/"
    project = read("python", "pyproject.toml").decode()
    description = re.search(r'^description = "(.*)"$', project, re.M).group(1)
    files += [
        (info + "METADATA", (f"Metadata-Version: 2.1\nName: mb3d\nVersion: {version}\nSummary: {description}\n"
                             "Home-page: https://github.com/thr32423/mb3d-bindings\n"
                             "License: MIT (the module), LGPL-2.1-only (the library libmb3d in mb3d/lib)\n"
                             "Requires-Python: >=3.9\nDescription-Content-Type: text/markdown\n\n").encode() + read("python", "README.md")),
        (info + "WHEEL", f"Wheel-Version: 1.0\nGenerator: mb3d-bindings tools/package.py\nRoot-Is-Purelib: false\nTag: py3-none-{tag}\n".encode()),
        (info + "LICENSE", read("LICENSE")),
    ]
    record = "".join(f"{name},sha256={base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b'=').decode()},{len(content)}\n" for name, content in files)
    files.append((info + "RECORD", (record + info + "RECORD,,\n").encode()))
    path = os.path.join(out, f"mb3d-{version}-py3-none-{tag}.whl")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in files:
            z.writestr(zipfile.ZipInfo(name, (2020, 1, 1, 0, 0, 0)), content, zipfile.ZIP_DEFLATED)
    return path


def tar(path, files):
    with tarfile.open(path, "w:gz") as t:
        for name, content in files:
            info = tarfile.TarInfo(name)
            info.size, info.mode = len(content), 0o644
            t.addfile(info, io.BytesIO(content))
    return path


def npm(version, system, npm_os, cpu, addon, data, out):
    package = json.loads(read("js", "package.json"))
    package.update(version=version, os=[npm_os], cpu=[cpu], files=["mb3d.mjs", "mb3d.node", "data", "LICENSE-libmb3d"])
    package.pop("scripts", None)
    files = [("package.json", json.dumps(package, indent=2).encode() + b"\n"), ("mb3d.mjs", read("js", "mb3d.mjs")), ("mb3d.node", addon),
             ("README.md", read("js", "README.md")), ("LICENSE", read("LICENSE")), ("LICENSE-libmb3d", read("ffi", "LICENSE"))] + list(data)
    return tar(os.path.join(out, f"mb3d-{version}-{system}.tgz"), [("package/" + name, content) for name, content in files])


def c_library(version, system, lib_name, lib, import_lib, data, out):
    top = f"libmb3d-{version}-{system}/"
    files = [(lib_name, lib), ("mb3d.h", read("ffi", "include", "mb3d.h")), ("README.md", read("ffi", "README.md")), ("LICENSE", read("ffi", "LICENSE")),
             ("examples/render.c", read("ffi", "examples", "render.c")), ("examples/render.py", read("ffi", "examples", "render.py"))]
    if import_lib:
        files.append(("mb3d.dll.lib", import_lib))
    files += [(name[len("data/"):], content) for name, content in data]
    return tar(os.path.join(out, f"libmb3d-{version}-{system}.tar.gz"), [(top + name, content) for name, content in files])


def main():
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("--system", required=True, choices=sorted(SYSTEMS))
    a.add_argument("--data", required=True, help="the folder with M3Formulas, EM_JIT_M3Formulas and M3Maps")
    a.add_argument("--lib", help="the built libmb3d")
    a.add_argument("--addon", help="the built Node.js add-on")
    a.add_argument("--out", default=os.path.join(root, "dist"))
    o = a.parse_args()
    tag, lib_name, addon_name, npm_os, cpu = SYSTEMS[o.system]
    version = re.search(r'^__version__ = "(.*)"$', read("python", "mb3d", "__init__.py").decode(), re.M).group(1)
    for other, text in (("js/package.json", json.loads(read("js", "package.json"))["version"]),
                        ("ffi/Cargo.toml", re.search(r'^version = "(.*)"$', read("ffi", "Cargo.toml").decode(), re.M).group(1)),
                        ("node/Cargo.toml", re.search(r'^version = "(.*)"$', read("node", "Cargo.toml").decode(), re.M).group(1))):
        if text != version:
            raise SystemExit(f"{other} says version {text}, python/mb3d/__init__.py {version}")
    lib_path = o.lib or os.path.join(root, "ffi", "target", "release", lib_name)
    with open(lib_path, "rb") as f:
        lib = f.read()
    with open(o.addon or os.path.join(root, "node", "target", "release", addon_name), "rb") as f:
        addon = f.read()
    import_lib = None
    if o.system.startswith("windows"):
        with open(lib_path + ".lib", "rb") as f:
            import_lib = f.read()
    data = list(data_files(o.data))
    os.makedirs(o.out, exist_ok=True)
    for path in (wheel(version, tag, lib_name, lib, data, o.out), npm(version, o.system, npm_os, cpu, addon, data, o.out),
                 c_library(version, o.system, lib_name, lib, import_lib, data, o.out)):
        print(f"{os.path.getsize(path) / 1e6:6.1f} MB  {os.path.relpath(path, root)}")


if __name__ == "__main__":
    main()
