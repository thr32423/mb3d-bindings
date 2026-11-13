// mb3d from JavaScript (Node.js): 3D fractals of Mandelbulb3D, calculated
// by mb3d-rs.
//
//     import { Engine } from "mb3d";
//     const engine = await Engine.start();
//     const scene = await engine.preset("Amazing Box");
//     await scene.set({ zoom: 0.3, iterations: 12 });
//     await scene.render({ width: 1280, file: "box.png" });
//     engine.close();
//
// The engine is a Node.js add-on (mb3d.node), loaded into this program:
// nothing is started and nothing else is installed.  An installed package
// carries the add-on and the formula and map folders; otherwise it is looked
// for in the `addon` option, the environment variable MB3D_NODE, then in
// this repository's node/target/release.  A picture is calculated on one of
// Node's worker threads.  EXPERIMENTAL.

import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const PROTOCOL = 1;

export class Mb3dError extends Error {}

const value = (v) => (Array.isArray(v) ? v.map(value).join(", ") : String(v));
const here = dirname(fileURLToPath(import.meta.url));
const built = { win32: "mb3d_node.dll", darwin: "libmb3d_node.dylib" }[process.platform] || "libmb3d_node.so";
const addons = new Map();

/** The path of the add-on, or an error that says where it was looked for. */
export function findAddon(addon) {
  for (const candidate of [addon, process.env.MB3D_NODE]) {
    if (!candidate) continue;
    if (existsSync(candidate)) return resolve(candidate);
    throw new Mb3dError(`${candidate}: no such add-on`);
  }
  for (const candidate of [join(here, "mb3d.node"), join(here, "..", "node", "target", "release", built)]) if (existsSync(candidate)) return candidate;
  throw new Mb3dError("the add-on mb3d.node was not found: install the package for this system, pass { addon } or set the environment variable MB3D_NODE");
}

// The add-on, loaded once, with the formula and map folders that came with the package.
function load(path) {
  let addon = addons.get(path);
  if (!addon) {
    const module = { exports: {} };
    try {
      process.dlopen(module, path); // (require() wants the name to end in .node)
    } catch (e) {
      throw new Mb3dError(`${path}: ${e.message}`);
    }
    addon = module.exports;
    const data = join(here, "data");
    for (const [folder, add] of [["M3Formulas", addon.addFormulaFolder], ["EM_JIT_M3Formulas", addon.addFormulaFolder], ["M3Maps", addon.addMapFolder]])
      if (existsSync(join(data, folder))) add(join(data, folder));
    addons.set(path, addon);
  }
  return addon;
}

export class Engine {
  /**
   * Starts the engine: { cpu, formulas, maps, addon }.
   * cpu: calculate on the processor only (otherwise the graphics card helps
   * where there is one).  formulas, maps: further folders with formula files
   * (.m3f) and map pictures.  addon: the path of mb3d.node.
   */
  static async start(options = {}) {
    const engine = new Engine(options);
    const hello = await engine.ask({ op: "hello" });
    engine.version = hello.version;
    engine.gpu = hello.gpu;
    if (hello.protocol !== PROTOCOL) {
      engine.close();
      throw new Mb3dError(`mb3d ${hello.version} speaks protocol ${hello.protocol}, this module protocol ${PROTOCOL}`);
    }
    await engine.ask({ op: "gpu", on: !options.cpu });
    return engine;
  }

  constructor({ addon, formulas, maps } = {}) {
    this.addon = load(findAddon(addon));
    if (formulas) this.addon.addFormulaFolder(resolve(formulas));
    if (maps) this.addon.addMapFolder(resolve(maps));
    this.session = new this.addon.Session();
  }

  /** Sends a request of `mb3d serve` (mb3d-rs: docs/API.md) and gives its answer. */
  async ask(request, progress) {
    if (!this.session) throw new Mb3dError("the engine is closed");
    const event = progress
      ? (line) => {
          const e = JSON.parse(line);
          if (e.event === "progress") progress(e.stage, e.done, e.total);
        }
      : undefined;
    let answer;
    try {
      answer = JSON.parse(await this.session.request(JSON.stringify(request), event));
    } catch (e) {
      throw new Mb3dError(e.message);
    }
    if (!answer.ok) throw new Mb3dError(answer.error || "unknown error");
    return answer;
  }

  /** Ends the engine: its scenes are forgotten. */
  close() {
    if (!this.session) return;
    this.session = null;
    this.addon.finish(); // (waits for the graphics card's compiles)
  }

  /** Stops the pictures asked for so far: their render rejects with "cancelled". */
  cancel() {
    if (this.session) this.session.cancel();
  }

  /** Calculate on the graphics card (the default) or the processor. */
  async useGpu(on) {
    await this.ask({ op: "gpu", on: !!on });
  }

  /** A parameter file: .m3p, .m3i, MB3D text parameters, a scene text. */
  async open(file) {
    return new Scene(this, await this.ask({ op: "open", file: resolve(file) }));
  }

  /** A scene text (scene.text()) or MB3D text parameters. */
  async fromText(text) {
    return new Scene(this, await this.ask({ op: "open", text }));
  }

  /** The contents of a parameter file (a Buffer); `name` tells its kind. */
  async fromBytes(data, name = "scene.m3p") {
    return new Scene(this, await this.ask({ op: "open", data: Buffer.from(data).toString("base64"), name }));
  }

  /** A formula by name, with a camera that shows it. */
  async preset(formula) {
    return new Scene(this, await this.ask({ op: "open", preset: formula }));
  }

  /** The names of all formulas. */
  async formulas() {
    return (await this.ask({ op: "formulas" })).names;
  }

  /** A formula's settings and their default values. */
  async formulaSettings(name) {
    return (await this.ask({ op: "formulas", name })).settings;
  }

  /** Which scene keys do what, as text. */
  async guide() {
    return (await this.ask({ op: "guide" })).text;
  }
}

export class Scene {
  constructor(engine, about) {
    this.engine = engine;
    this.id = about.scene;
    this.about(about);
  }

  about(about) {
    this.width = about.width;
    this.height = about.height;
    this.formulas = about.formulas;
    this.rotation = about.rotation;
    this.notes = about.notes;
    return this;
  }

  ask(op, members = {}, progress) {
    return this.engine.ask({ ...members, op, scene: this.id }, progress);
  }

  /** The scene as `key = value` lines. */
  async text() {
    return (await this.ask("text")).text;
  }

  /** The value of a global key, as text (undefined without such a line). */
  async get(key) {
    for (const line of (await this.text()).split("\n")) {
      if (line.startsWith("[")) break;
      const i = line.indexOf("=");
      if (i > 0 && line.slice(0, i).trim() === key) return line.slice(i + 1).trim();
    }
    return undefined;
  }

  /** Changes global keys: `key = value` lines, or { zoom: 1.2, rotation: [10, 20, 0] }. */
  async set(changes) {
    const lines = typeof changes === "string" ? changes : Object.entries(changes).map(([k, v]) => `${k} = ${value(v)}`).join("\n");
    return this.about(await this.ask("set", { changes: lines }));
  }

  /** Changes a formula's own values: setFormula(0, { Scale: 2.2 }); `slot` as scene.formulas tells it. */
  async setFormula(slot, values = {}, iterations) {
    const m = { slot, settings: values };
    if (iterations !== undefined) m.iterations = iterations;
    return this.about(await this.ask("formula", m));
  }

  /** Another picture size: { width, height }; one follows the proportions. */
  async resize(size) {
    return this.about(await this.ask("resize", size));
  }

  /** A second scene with the same settings. */
  async copy() {
    return new Scene(this.engine, await this.ask("copy"));
  }

  /** Writes a .m3p (a .m3s or .txt name: the scene text). */
  async save(file) {
    await this.ask("save", { file: resolve(file) });
  }

  /** Forgets the scene in the engine. */
  async close() {
    await this.ask("close");
  }

  /**
   * Calculates the picture: { width, height, file, depthFile, depth, pixels, progress }.
   * width, height: for this picture only (one follows the proportions).
   * file, depthFile: PNG files to write.  pixels: raw pixels (rgb) instead of a PNG.
   * depth: the depth too.  progress: (stage, done, total) while it runs.
   * Gives { width, height, seconds, device, png | rgb, depthPng | depth } (Buffers).
   */
  async render({ width, height, file, depthFile, depth, pixels, progress } = {}) {
    const m = {};
    if (width) m.width = width;
    if (height) m.height = height;
    if (file) m.file = resolve(file);
    if (depthFile) m.depth_file = resolve(depthFile);
    if (pixels) m.format = "rgb";
    else if (depth && file) m.format = "png";
    if (depth) m.depth = true;
    if (progress) m.progress = true;
    const a = await this.ask("render", m, progress);
    const d = (k) => (k in a ? Buffer.from(a[k], "base64") : undefined);
    return { width: a.width, height: a.height, seconds: a.seconds, device: a.device, file: a.file, depthFile: a.depth_file, png: d("png"), depthPng: d("depth_png"), rgb: d("rgb"), depth: d("depth") };
  }
}
