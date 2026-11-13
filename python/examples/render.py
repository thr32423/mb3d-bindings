"""A picture and a turntable of eight views.   python render.py [file.m3p]"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import mb3d

with mb3d.Engine() as engine:
    scene = engine.open(sys.argv[1]) if len(sys.argv) > 1 else engine.preset("Amazing Box")
    print("formulas:", scene.formulas)

    def progress(stage, done, total):
        print(f"\r{stage or 'calculating'} {100 * done // max(total, 1)} %   ", end="", file=sys.stderr)

    picture = scene.render(width=1280, file="picture.png", progress=progress)
    print(f"\npicture.png: {picture.width} x {picture.height} in {picture.seconds} s on {picture.device}")

    x, y, z = scene.rotation or (0, 0, 0)
    for i in range(8):
        scene.set(rotation=(x, y + 45 * i, z))
        scene.render(width=480, file=f"turn{i}.png")
    print("turn0.png ... turn7.png")
