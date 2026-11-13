# mb3d-bindings

[mb3d-rs](https://github.com/thr32423/mb3d-rs) (Mandelbulb3D's 3D fractals)
from other languages. EXPERIMENTAL: everything here may still change.

| folder | what | needs |
|---|---|---|
| [python/](python) | the module `mb3d` for Python | Python 3.9+ |
| [js/](js) | the module `mb3d` for Node.js | Node 18+ |
| [ffi/](ffi) | `libmb3d`, a C library (C, C++, C#, ...) | nothing |
| [node/](node) | the Node.js add-on under the JavaScript module | (part of its package) |
| [demos/](demos) | web pages that use the modules | one of the modules |
| [notebook/](notebook) | a Jupyter notebook: the examples in Python and JavaScript, sliders; runs online | Jupyter |

Each package holds the engine itself, built from mb3d-rs, with its formulas
and maps: the program `mb3d` is not needed and nothing is started. A picture
is calculated inside your own program.

## Installing

Packages for Linux (x64), Windows (x64) and macOS (Apple silicon and Intel)
are on the [releases page](https://github.com/thr32423/mb3d-bindings/releases/latest);
they are not on PyPI or npm yet.

**Python** (3.9 or later), any of the systems:

    pip install mb3d --find-links https://github.com/thr32423/mb3d-bindings/releases/expanded_assets/v0.2.0

**JavaScript** (Node.js 18 or later), the line of your system:

    npm install https://github.com/thr32423/mb3d-bindings/releases/download/v0.2.0/mb3d-0.2.0-linux-x64.tgz
    npm install https://github.com/thr32423/mb3d-bindings/releases/download/v0.2.0/mb3d-0.2.0-windows-x64.tgz
    npm install https://github.com/thr32423/mb3d-bindings/releases/download/v0.2.0/mb3d-0.2.0-macos-arm64.tgz
    npm install https://github.com/thr32423/mb3d-bindings/releases/download/v0.2.0/mb3d-0.2.0-macos-x64.tgz

**C**: unpack `libmb3d-0.2.0-SYSTEM.tar.gz` of the releases page: the library
(`libmb3d.so`, `libmb3d.dylib`, `mb3d.dll` with `mb3d.dll.lib`), the header
`mb3d.h` and the formula and map folders, which a program names to the
library once (`mb3d_add_formula_folder`, `mb3d_add_map_folder`).
[ffi/](ffi) tells how to build a program with it, and how to build the
library itself.

**Rust**: the engine is the crate `mb3d` of mb3d-rs, without its desktop
application; in `Cargo.toml`

    mb3d = { git = "https://github.com/thr32423/mb3d-rs", tag = "v0.3.10", default-features = false, features = ["gpu", "jit"] }

and `mb3d::api` in the code ([docs/API.md](https://github.com/thr32423/mb3d-rs/blob/master/docs/API.md)).

**Other languages**: load `libmb3d`, or start the program `mb3d serve` of
mb3d-rs and talk to it in JSON lines (the same docs/API.md).

## Try it online

[The notebook](https://mybinder.org/v2/gh/thr32423/mb3d-bindings/main?urlpath=lab%2Ftree%2Fnotebook%2Fmb3d.ipynb)
on [mybinder.org](https://mybinder.org): no account, nothing to install;
the start takes a minute or two. Choose Run > Run All Cells: the Python
and JavaScript examples below, sliders.
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

    import { Engine } from "mb3d";

    const engine = await Engine.start();
    const scene = await engine.preset("Amazing Box");  // or engine.open("file.m3p")
    await scene.set({ zoom: 0.3, iterations: 12 });
    await scene.render({ width: 1280, file: "box.png" });
    engine.close();

## C

    mb3d_add_formula_folder("M3Formulas");            /* the folders that came with the library */
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

The modules, demos and the notebook are under the MIT licence
([LICENSE](LICENSE)). The C library ([ffi/](ffi)) and the Node.js add-on
([node/](node)) are built from the engine and, like it, are under the LGPL
2.1 ([ffi/LICENSE](ffi/LICENSE)): a program of any licence may load them;
changes to the engine are published under the LGPL. The formulas and maps
in the packages come from Mandelbulb3D and its community (their credits are
in the folders).

## Building and tests

Needs [Rust](https://rustup.rs). The modules find what was built here.

    cargo build --release --manifest-path ffi/Cargo.toml       # libmb3d
    cargo build --release --manifest-path node/Cargo.toml      # the Node.js add-on
    cd python && python -m unittest discover -s tests
    cd js && node --test

`python tools/package.py --system linux-x64 --data FOLDER` packs the three
packages into `dist/` (FOLDER: an unpacked mb3d-rs release, for its formula
and map folders); the workflow in `.github/` does it for every system and a
tag `vX.Y.Z` publishes them.
