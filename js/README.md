# mb3d for Node.js

3D fractals of Mandelbulb3D from JavaScript, calculated by the program
`mb3d` ([mb3d-rs](https://github.com/thr32423/mb3d-rs)). EXPERIMENTAL.

    import { Engine } from "./mb3d.mjs";

    const engine = await Engine.start();
    const scene = await engine.open("cathedral.m3p");   // .m3p, .m3i, text parameters
    await scene.set({ zoom: 1.4, rotation: [20, -35, 0] });
    const picture = await scene.render({ width: 1920, file: "cathedral.png",
                                         progress: (stage, done, total) => console.log(stage, done, total) });
    console.log(picture.seconds, picture.device);
    engine.close();

The module starts `mb3d serve` and talks to it; no packages, no network.
The program is looked for in `Engine.start({ program })`, the environment
variable `MB3D`, then on the PATH. It runs in Node.js (a web page asks a
server that uses it: see ../demos).

| | |
|---|---|
| `Engine.start({ program, cpu, formulas, maps })` | starts the engine; `close()` ends it |
| `engine.open(file)`, `fromText(text)`, `fromBytes(buffer, name)`, `preset(formula)` | a `Scene` |
| `engine.formulas()`, `formulaSettings(name)`, `guide()` | formula names, a formula's settings, what the scene keys do |
| `engine.cancel()` | stops the pictures asked for so far |
| `scene.width`, `height`, `formulas`, `rotation`, `notes` | what the scene is |
| `scene.text()`, `get(key)` | the scene as `key = value` lines, one value |
| `scene.set("key = value")`, `set({ zoom: 2 })`, `resize({ width, height })` | changes |
| `scene.formulas[i].settings`, `setFormula(slot, { Scale: 2.2 })` | each formula's own values, and changing them |
| `scene.copy()`, `save(file)`, `close()` | |
| `scene.render({ width, height, file, depthFile, depth, pixels, progress })` | `{ width, height, seconds, device, png, depthPng, rgb, depth }` (Buffers) |

All of them return promises. Errors are `Mb3dError` with the engine's
sentence.
