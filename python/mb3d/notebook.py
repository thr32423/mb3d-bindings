"""mb3d in a Jupyter notebook: sliders that turn, zoom and reshape a scene.

    import mb3d
    from mb3d.notebook import explore

    engine = mb3d.Engine()
    explore(engine.preset("Integer Power"))

Needs ipywidgets (pip install ipywidgets).
"""

import math

__all__ = ["explore"]


def explore(scene, width=560, formula_values=True):
    """Shows the scene with sliders: the view, the iterations and (with
    `formula_values`) each formula's own values.  Returns the widget; the
    scene itself is changed, so scene.render(...) afterwards gives the
    picture as set."""
    import ipywidgets as w

    picture = w.Image(format="png")
    status = w.Label()
    style = {"description_width": "150px"}
    layout = w.Layout(width="460px")

    def show():
        try:
            p = scene.render(width=width)
            picture.value = p.png
            status.value = f"{p.width} × {p.height} in {p.seconds} s — {p.device}"
        except Exception as e:  # the engine's sentence, shown instead of a traceback per slider move
            status.value = str(e)

    def slider(description, value, low, high, step, change, whole=False):
        kind = w.IntSlider if whole else w.FloatSlider
        s = kind(description=description, value=min(max(value, low), high), min=low, max=high, step=step,
                 continuous_update=True, style=style, layout=layout)

        def moved(event):
            try:
                change(event["new"])
            except Exception as e:
                status.value = str(e)
                return
            show()

        s.observe(moved, names="value")
        return s

    rotation = list(scene.rotation or (0.0, 0.0, 0.0))

    def turn(axis):
        def change(v):
            rotation[axis] = v
            scene.set(rotation=tuple(rotation))
        return change

    zoom = float(scene.get("zoom") or 1)
    controls = [
        slider("Turn X", rotation[0], -180, 180, 1, turn(0)),
        slider("Turn Y", rotation[1], -180, 180, 1, turn(1)),
        slider("Turn Z", rotation[2], -180, 180, 1, turn(2)),
        slider("Zoom (log2)", math.log2(zoom), math.log2(zoom) - 4, math.log2(zoom) + 6, 0.05, lambda v: scene.set(zoom=2 ** v)),
        slider("Iterations", int(scene.get("iterations") or 12), 1, 60, 1, lambda v: scene.set(iterations=v), whole=True),
    ]
    if formula_values:
        several = len(scene.formula_values) > 1
        for n, f in enumerate(scene.formula_values, 1):
            for key, value in list(f.get("settings", {}).items())[:6]:
                span = max(abs(value), 1.0) * 2
                controls.append(slider(f"{n}. {key}" if several else key, value, value - span, value + span, span / 200,
                                       (lambda slot, key: lambda v: scene.set_formula(slot, {key: v}))(f["slot"], key)))
    show()
    return w.HBox([w.VBox([picture, status]), w.VBox(controls)])
