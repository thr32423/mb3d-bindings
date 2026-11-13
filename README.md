# mb3d-bindings

[mb3d-rs](https://github.com/thr32423/mb3d-rs) (Mandelbulb3D's 3D fractals)
from other languages. EXPERIMENTAL: everything here may still change.

| folder | what | needs |
|---|---|---|
| [python/](python) | the module `mb3d` for Python | the program `mb3d`, Python 3.9+ |
| [js/](js) | the module `mb3d` for Node.js | the program `mb3d`, Node 18+ |
| [ffi/](ffi) | `libmb3d`, a C library, with a C and a Python example | Rust to build it |
| [demos/](demos) | web pages that use the modules | one of the modules |
| [notebook/](notebook) | a Jupyter notebook: the examples in Python and JavaScript, sliders; runs online | Jupyter |

The Python and JavaScript modules start the program `mb3d serve` and talk
to it (mb3d-rs: docs/API.md); they have no other dependencies. The C library
holds the engine itself, for programs that want the pixels in their own
memory.

## Installing the program mb3d

The modules need the program `mb3d` of mb3d-rs, version 0.3.10 or later
(`mb3d --version` tells; an older one has no `mb3d serve`). Installing the
latest release over an older one updates it.

**Linux and macOS**, one line: fetches the latest release into `~/mb3d-rs`,
checks it and makes `mb3d` a command (run it again later to update):

    curl -fsSL https://raw.githubusercontent.com/thr32423/mb3d-rs/master/download.sh | sh

**Debian, Ubuntu, Mint**: download
[mb3d-rs-linux-x64.deb](https://github.com/thr32423/mb3d-rs/releases/latest/download/mb3d-rs-linux-x64.deb), then

    sudo apt install ./mb3d-rs-linux-x64.deb

**Fedora, RHEL, Rocky** (openSUSE: `zypper` instead of `dnf`): download
[mb3d-rs-linux-x64.rpm](https://github.com/thr32423/mb3d-rs/releases/latest/download/mb3d-rs-linux-x64.rpm), then

    sudo dnf install ./mb3d-rs-linux-x64.rpm

**Windows**: unpack
[mb3d-rs-windows-x64.zip](https://github.com/thr32423/mb3d-rs/releases/latest/download/mb3d-rs-windows-x64.zip)
into a folder of your choice; the program is `mb3d.exe` in it.

**By hand** (any system): unpack the archive of your system from the
[latest release](https://github.com/thr32423/mb3d-rs/releases/latest); the
program `mb3d` is in the unpacked folder. On macOS run
`xattr -dr com.apple.quarantine .` in that folder once.

When `mb3d` is not a command (Windows, unpacked by hand, or an older one
comes first on the PATH), tell the modules where it is:

    export MB3D=/path/to/mb3d                  (Windows: set MB3D=C:\path\to\mb3d.exe)

or in the code: `mb3d.Engine(program="/path/to/mb3d")`,
`Engine.start({ program: "/path/to/mb3d" })`.

## Try it online

[The notebook](https://mybinder.org/v2/gh/thr32423/mb3d-bindings/main?urlpath=lab%2Ftree%2Fnotebook%2Fmb3d.ipynb)
on [mybinder.org](https://mybinder.org): no account, nothing to install;
the start takes a minute or two. Choose Run > Run All Cells: `mb3d serve`
by hand, the Python and JavaScript examples below, sliders.
([In Colab](https://colab.research.google.com/github/thr32423/mb3d-bindings/blob/main/notebook/mb3d.ipynb),
with a Google account.)

That machine has no graphics card: the pictures are the same, slower.

## Python

    import mb3d

    with mb3d.Engine() as engine:
        scene = engine.preset("Amazing Box")          # or engine.open("file.m3p")
        scene.set(zoom=0.3, iterations=12)
        scene.render(width=1280, file="box.png")

## JavaScript

    import { Engine } from "./js/mb3d.mjs";

    const engine = await Engine.start();
    const scene = await engine.preset("Amazing Box");  // or engine.open("file.m3p")
    await scene.set({ zoom: 0.3, iterations: 12 });
    await scene.render({ width: 1280, file: "box.png" });
    engine.close();

## C

    mb3d_scene *scene = mb3d_preset("Amazing Box");
    mb3d_scene_set(scene, "zoom = 0.3\niterations = 12");
    mb3d_scene_resize(scene, 1280, 960);
    mb3d_picture *picture = mb3d_render(scene, NULL, NULL);
    mb3d_picture_save_png(picture, "box.png");

## Demos

    python demos/explorer/server.py       (or: node demos/explorer/server.mjs)

then open http://127.0.0.1:8765: turn and zoom a fractal in the browser,
open parameter files, save pictures. [demos/](demos) has more.

## Licence

Everything here is under the MIT licence ([LICENSE](LICENSE)), except
[ffi/](ffi): the C library is built from the engine and, like it, is under
the LGPL 2.1 ([ffi/LICENSE](ffi/LICENSE)).

The engine itself (the program `mb3d`) is LGPL 2.1 whichever part is used: a
program of any licence may start it or load the library; changes to the
engine are published under the LGPL.

## Tests

    cd python && python -m unittest discover -s tests
    cd js && node --test
