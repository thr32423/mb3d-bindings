# mb3d for Python

3D fractals of Mandelbulb3D from Python, calculated by the program `mb3d`
([mb3d-rs](https://github.com/thr32423/mb3d-rs)). EXPERIMENTAL.

    import mb3d

    with mb3d.Engine() as engine:
        scene = engine.open("cathedral.m3p")       # .m3p, .m3i, text parameters
        scene.set(zoom=1.4, rotation=(20, -35, 0))
        picture = scene.render(width=1920, file="cathedral.png",
                               progress=lambda stage, done, total: print(stage, done, total))
        print(picture.seconds, picture.device)

The module starts `mb3d serve` and talks to it; nothing else is needed (no
packages, no network). The program is looked for in `Engine(program=...)`,
the environment variable `MB3D`, then on the PATH.

| | |
|---|---|
| `Engine(program=None, cpu=False, formulas=None, maps=None)` | starts the engine; `close()` or `with` ends it |
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

Pixels for numpy or Pillow:

    p = scene.render(width=640, pixels=True, depth=True)
    image = numpy.frombuffer(p.rgb, numpy.uint8).reshape(p.height, p.width, 3)
    depth = numpy.frombuffer(p.depth, "<u2").reshape(p.height, p.width)

In a Jupyter notebook a picture shows itself, and
`mb3d.notebook.explore(scene)` gives sliders (needs ipywidgets).

Errors are `mb3d.Mb3dError` with the engine's sentence.
