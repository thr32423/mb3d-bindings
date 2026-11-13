# mb3d for developers: install, reference, examples

3D fractals of Mandelbulb3D from your own program, in Python, JavaScript
(Node.js), C or Rust. The engine of
[mb3d-rs](https://github.com/thr32423/mb3d-rs) is inside each package: no
other program is installed or started. EXPERIMENTAL: names may still change.

Packages exist for Linux x64, Windows x64 and macOS (Apple silicon, Intel),
on the [releases page](https://github.com/thr32423/mb3d-bindings/releases/latest).
The examples below use version 0.2.0.

## The idea, the same in every language

1. Open a **scene**: a formula by name (`"Amazing Box"`; it comes with a
   camera that shows it) or a Mandelbulb3D parameter file (`.m3p`, `.m3i`,
   text parameters).
2. Change it: **global settings** as `key = value` (`zoom`, `rotation`,
   `iterations`, colours, fog, ...; the scene's text shows all of them), and
   each **formula's own values** by name (`Scale`, ...).
3. **Render**: a PNG file, or the pixels and the depth in memory.

The graphics card helps where there is one; otherwise the processor
calculates the same picture.

## Python (3.9 or later)

    pip install mb3d --find-links https://github.com/thr32423/mb3d-bindings/releases/expanded_assets/v0.2.0

```python
import mb3d

with mb3d.Engine() as engine:
    scene = engine.preset("Amazing Box")              # or engine.open("file.m3p")
    scene.set(zoom=0.3, iterations=12, rotation=(25, -40, 0))
    scene.set_formula(0, {"Scale": 2.4})              # a formula's own values
    picture = scene.render(width=1280, file="box.png",
                           progress=lambda stage, done, total: print(stage or "calculating", done, total, end="\r"))
    print(picture.width, picture.height, picture.seconds, picture.device)

    p = scene.render(width=320, pixels=True, depth=True)   # raw pixels for numpy, Pillow
    print(len(p.rgb), len(p.depth))
    scene.save("box.m3p")
```

| | |
|---|---|
| `mb3d.Engine(cpu=False, formulas=None, maps=None)` | the engine; `cpu=True`: without the graphics card; `formulas`, `maps`: further folders. `close()` or `with` ends it |
| `engine.preset(name)`, `open(file)`, `from_text(text)`, `from_bytes(data, name)` | a scene |
| `engine.formulas()`, `formula_settings(name)`, `guide()` | all formula names; a formula's values and defaults; what the scene keys do |
| `engine.cancel()` | stops the render that is running (call it from another thread) |
| `scene.set("key = value")`, `set(zoom=2)`, `resize(width=, height=)` | change global settings, the picture size |
| `scene.formula_values`, `set_formula(slot, {"Scale": 2.2})` | each formula's own values; changing them |
| `scene.text()`, `get(key)`, `width`, `height`, `rotation`, `notes` | reading the scene |
| `scene.copy()`, `save(file)`, `close()` | |
| `scene.render(width=, height=, file=, depth_file=, depth=, pixels=, progress=)` | a picture |
| `picture.png`, `depth_png`, `rgb`, `depth`, `width`, `height`, `seconds`, `device`, `save(file)` | `rgb`: 3 bytes a pixel; `depth`: 2 bytes a pixel, 65535 nearest |

Errors are `mb3d.Mb3dError`. In a Jupyter notebook a picture shows itself;
`mb3d.notebook.explore(scene)` gives sliders. More: [python/](python).

## JavaScript (Node.js 18 or later)

Download the package of your system, then install the file (`-linux-x64`,
`-windows-x64`, `-macos-arm64` or `-macos-x64`):

    curl -LO https://github.com/thr32423/mb3d-bindings/releases/download/v0.2.0/mb3d-0.2.0-linux-x64.tgz
    npm install ./mb3d-0.2.0-linux-x64.tgz

```js
import { Engine } from "mb3d";

const engine = await Engine.start();
const scene = await engine.preset("Amazing Box");      // or engine.open("file.m3p")
await scene.set({ zoom: 0.3, iterations: 12, rotation: [25, -40, 0] });
await scene.setFormula(0, { Scale: 2.4 });             // a formula's own values
const picture = await scene.render({ width: 1280, file: "box.png",
                                     progress: (stage, done, total) => process.stdout.write(`${stage || "calculating"} ${done}/${total}\r`) });
console.log(picture.width, picture.height, picture.seconds, picture.device);

const p = await scene.render({ width: 320, pixels: true, depth: true });   // raw pixels (Buffers)
console.log(p.rgb.length, p.depth.length);
await scene.save("box.m3p");
engine.close();
```

| | |
|---|---|
| `Engine.start({ cpu, formulas, maps })` | the engine; `close()` ends it |
| `engine.preset(name)`, `open(file)`, `fromText(text)`, `fromBytes(buffer, name)` | a scene |
| `engine.formulas()`, `formulaSettings(name)`, `guide()` | all formula names; a formula's values and defaults; what the scene keys do |
| `engine.cancel()` | stops the renders asked for so far |
| `scene.set("key = value")`, `set({ zoom: 2 })`, `resize({ width, height })` | change global settings, the picture size |
| `scene.formulas[i].settings`, `setFormula(slot, { Scale: 2.2 })` | each formula's own values; changing them |
| `scene.text()`, `get(key)`, `width`, `height`, `rotation`, `notes` | reading the scene |
| `scene.copy()`, `save(file)`, `close()` | |
| `scene.render({ width, height, file, depthFile, depth, pixels, progress })` | `{ width, height, seconds, device, png, depthPng, rgb, depth }` |

Every call returns a promise; a picture is calculated on a worker thread, so
the program stays responsive. Errors are `Mb3dError`. More: [js/](js).

## C (and C++, C#, anything that loads a C library)

Unpack `libmb3d-0.2.0-SYSTEM.tar.gz` of the releases page: the library
(`libmb3d.so`, `libmb3d.dylib`, or `mb3d.dll` with `mb3d.dll.lib`), `mb3d.h`
and the formula and map folders.

```c
#include <stdio.h>
#include "mb3d.h"

int main(void) {
    mb3d_add_formula_folder("M3Formulas");   /* the folders that came with the library */
    mb3d_add_formula_folder("EM_JIT_M3Formulas");
    mb3d_add_map_folder("M3Maps");
    mb3d_use_gpu(1);                          /* the library starts on the processor only */

    mb3d_scene *scene = mb3d_preset("Amazing Box");       /* or mb3d_open("file.m3p") */
    if (!scene) { fprintf(stderr, "%s\n", mb3d_last_error()); return 1; }
    mb3d_scene_set(scene, "zoom = 0.3\niterations = 12");
    mb3d_scene_set_formula(scene, 0, "Scale", 2.4);
    mb3d_scene_resize(scene, 1280, 960);

    mb3d_picture *picture = mb3d_render(scene, NULL, NULL);
    if (!picture) { fprintf(stderr, "%s\n", mb3d_last_error()); return 1; }
    mb3d_picture_save_png(picture, "box.png");
    const uint8_t *rgb = mb3d_picture_rgb(picture);        /* width * height * 3 bytes */
    printf("%u x %u, first pixel %u %u %u\n", mb3d_picture_width(picture), mb3d_picture_height(picture), rgb[0], rgb[1], rgb[2]);

    mb3d_picture_free(picture);
    mb3d_scene_free(scene);
    mb3d_finish();                            /* when the graphics card was used */
    return 0;
}
```

    cc box.c -I. -L. -lmb3d -o box
    LD_LIBRARY_PATH=. ./box

| | |
|---|---|
| `mb3d_preset`, `mb3d_open`, `mb3d_open_text`, `mb3d_open_bytes`, `mb3d_scene_copy`, `mb3d_scene_free` | scenes |
| `mb3d_scene_set`, `mb3d_scene_set_formula`, `mb3d_scene_resize` | changes |
| `mb3d_scene_text`, `mb3d_scene_size`, `mb3d_scene_rotation` | reading the scene |
| `mb3d_render(scene, progress, user)` | a picture; `progress` may be NULL, returning non-zero from it stops the render |
| `mb3d_picture_rgb`, `_depth`, `_width`, `_height`, `_seconds`, `_save_png`, `mb3d_picture_free` | the result |
| `mb3d_use_gpu`, `mb3d_finish`, `mb3d_add_formula_folder`, `mb3d_add_map_folder` | set-up |
| `mb3d_last_error` | why the last call on this thread failed (a failed call returns NULL or -1) |
| `mb3d_session_new`, `_request`, `_cancel`, `_free` | the JSON requests of `mb3d serve`, answered inside the program: for wrappers in further languages |

[ffi/include/mb3d.h](ffi/include/mb3d.h) describes every function. A scene
is used by one thread at a time. More: [ffi/](ffi).

## Rust

The engine is the crate `mb3d` of mb3d-rs, taken without its desktop
application. It is not on crates.io; in `Cargo.toml`:

```toml
[dependencies]
mb3d = { git = "https://github.com/thr32423/mb3d-rs", tag = "v0.3.10", default-features = false, features = ["gpu", "jit"] }
```

```rust
use mb3d::api::{self, Fractal, RenderOptions};

fn main() -> Result<(), String> {
    api::use_gpu(true); // a library starts on the processor only
    let mut scene = Fractal::preset("Amazing Box")?; // or Fractal::open(Path::new("file.m3p"))
    scene.set("zoom = 0.3\niterations = 12")?;
    scene.resize(1280, 960);
    let picture = scene.render(&RenderOptions::default())?;
    std::fs::write("box.png", picture.png()).map_err(|e| e.to_string())?;
    println!("{} x {} in {:.2} s on {}", picture.width, picture.height, picture.seconds, picture.device);
    api::finish(); // when the graphics card was used
    Ok(())
}
```

| | |
|---|---|
| `Fractal::preset`, `open`, `from_text`, `from_bytes`, `clone()` | scenes |
| `set`, `set_formula(slot, &[("Scale", 2.2)], None)`, `resize` | changes |
| `text`, `size`, `rotation`, `formula_list`, `notes`, `m3p` | reading the scene; the scene as a parameter file |
| `render(&RenderOptions { progress, cancel })` | a `Picture`: `rgb`, `depth`, `width`, `height`, `seconds`, `device`, `png()`, `depth_png()` |
| `api::formula_names`, `formula_settings` | the formulas |
| `api::use_gpu`, `finish`, `add_formula_folder`, `add_map_folder` | set-up |

Formulas that are files (most of Mandelbulb3D's) and maps are found once
their folders are named with `add_formula_folder` / `add_map_folder`; the C
package above has the folders. `cargo doc --open` shows the rest;
[docs/API.md](https://github.com/thr32423/mb3d-rs/blob/master/docs/API.md)
is the engine's own description.

## Other languages

Load `libmb3d` and use its session functions (JSON requests in, JSON
answers out), or start the program `mb3d serve` of mb3d-rs and exchange the
same JSON as lines; docs/API.md lists the requests.

## Useful to know

* `engine.guide()` (Python, JavaScript) returns a text that says which scene
  keys do what; `scene.text()` shows a scene's current keys and values.
* `render` with a `width` only changes that picture; the scene keeps its
  size. `resize` changes the scene.
* Depth comes with every picture: 65535 is nearest, 0 the background.
* Try it without installing: the
  [notebook on mybinder.org](https://mybinder.org/v2/gh/thr32423/mb3d-bindings/main?urlpath=lab%2Ftree%2Fnotebook%2Fmb3d.ipynb).
* Licence: the Python and JavaScript modules are MIT; the engine inside the
  packages is LGPL 2.1 (a program of any licence may load it).
