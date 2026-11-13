# mb3d for Python

3D fractals of Mandelbulb3D from Python, calculated by the engine of
[mb3d-rs](https://github.com/thr32423/mb3d-rs), which is inside the package.
EXPERIMENTAL.

    import mb3d

    with mb3d.Engine() as engine:
        scene = engine.open("cathedral.m3p")       # .m3p, .m3i, text parameters
        scene.set(zoom=1.4, rotation=(20, -35, 0))
        picture = scene.render(width=1920, file="cathedral.png",
                               progress=lambda stage, done, total: print(stage, done, total))
        print(picture.seconds, picture.device)

    pip install mb3d --find-links https://github.com/thr32423/mb3d-bindings/releases/expanded_assets/v0.2.0

The package holds the engine as a library (`libmb3d`, built from mb3d-rs)
with its formulas and maps, loaded into your program: nothing is started,
no other packages, no network. From this repository instead: build
[../ffi](../ffi), or name a library with `Engine(library=...)` or the
environment variable `LIBMB3D`.

| | |
|---|---|
| `Engine(cpu=False, formulas=None, maps=None, library=None)` | the engine (`cpu`: without the graphics card; `formulas`, `maps`: further folders); `close()` or `with` ends it |
| `engine.open(file)`, `from_text(text)`, `from_bytes(data, name)`, `preset(formula)` | a `Scene` |
| `engine.formulas()`, `formula_settings(name)`, `guide()` | formula names, a formula's settings, what the scene keys do |
| `engine.cancel()` | stops the picture being calculated (from another thread) |
| `scene.width`, `height`, `formulas`, `rotation`, `notes` | what the scene is |
| `scene.text()`, `get(key)` | the scene as `key = value` lines, one value |
| `scene.set("key = value")`, `set(zoom=2)`, `resize(width=, height=)` | changes |
| `scene.formula_values`, `set_formula(slot, {"Scale": 2.2})` | each formula's own values, and changing them |
| `scene.copy()`, `save(file)`, `close()` | |
| `scene.render(width=, height=, file=, depth_file=, depth=, pixels=, progress=)` | a `Picture` |
| `picture.png`, `depth_png`, `rgb`, `depth`, `width`, `height`, `seconds`, `device`, `save(file)` | the result |

Pixels as numbers, for numpy, Pillow, OpenCV, matplotlib, PyTorch:

    p = scene.render(width=640, pixels=True, depth=True)
    image = numpy.frombuffer(p.rgb, numpy.uint8).reshape(p.height, p.width, 3)
    depth = numpy.frombuffer(p.depth, "<u2").reshape(p.height, p.width)

`image` is rows × columns × red, green, blue (0 to 255). `depth` is 65535 at
the nearest point and 0 where there is no fractal, so `depth > 0` is the
fractal's outline, ready for cutting it out, fog or laying it over another
picture. Both arrays are read-only: `.copy()` them to change them.

In a Jupyter notebook a picture shows itself, and
`mb3d.notebook.explore(scene)` gives sliders (needs ipywidgets).

Errors are `mb3d.Mb3dError` with the engine's sentence.
