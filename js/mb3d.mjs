// mb3d from JavaScript (Node.js): 3D fractals of Mandelbulb3D, calculated
// by mb3d-rs.
//
//     import { Engine } from "./mb3d.mjs";
//     const engine = await Engine.start();
//     const scene = await engine.preset("Amazing Box");
//     await scene.set({ zoom: 0.3, iterations: 12 });
//     await scene.render({ width: 1280, file: "box.png" });
//     engine.close();
//
// The engine is the program `mb3d` (mb3d-rs), started as `mb3d serve` and
// kept running: this module only talks to it.  It is looked for in the
// `program` option, the environment variable MB3D, then on the PATH.
// No packages needed.  EXPERIMENTAL, like `mb3d serve`.

import { spawn } from "node:child_process";
import { createInterface } from "node:readline";
import { resolve } from "node:path";

export const PROTOCOL = 1;

export class Mb3dError extends Error {}

const value = (v) => (Array.isArray(v) ? v.map(value).join(", ") : String(v));

export class Engine {
  /** Starts the engine: { program, cpu, formulas, maps }. */
  static async start(options = {}) {
    const engine = new Engine(options);
    const hello = await engine.ask({ op: "hello" });
    engine.version = hello.version;
    engine.gpu = hello.gpu;
    if (hello.protocol !== PROTOCOL) {
      engine.close();
      throw new Mb3dError(`mb3d ${hello.version} speaks protocol ${hello.protocol}, this module protocol ${PROTOCOL}`);
    }
    return engine;
  }

  constructor({ program, cpu, formulas, maps } = {}) {
    const args = ["serve"];
    if (cpu) args.push("--cpu");
    if (formulas) args.push("--formulas", formulas);
    if (maps) args.push("--maps", maps);
    this.waiting = new Map();
    this.next = 0;
    this.ended = null;
    this.proc = spawn(program || process.env.MB3D || "mb3d", args, { stdio: ["pipe", "pipe", "ignore"] });
    const end = (why) => {
      this.ended = this.ended || why;
      for (const w of this.waiting.values()) w.reject(new Mb3dError(this.ended));
      this.waiting.clear();
    };
    this.proc.on("error", (e) =>
      end(e.code === "ENOENT" ? "the program mb3d was not found: pass { program }, set the environment variable MB3D, or put it on the PATH" : String(e)),
    );
    this.proc.on("exit", () => end("the engine has ended"));
    this.proc.stdin.on("error", () => {});
    createInterface({ input: this.proc.stdout }).on("line", (line) => {
      const answer = JSON.parse(line);
      const w = this.waiting.get(answer.id);
      if (!w) return; // the answer to a cancel
      if (answer.event === "progress") {
        if (w.progress) w.progress(answer.stage, answer.done, answer.total);
        return;
      }
      this.waiting.delete(answer.id);
      if (answer.ok) w.resolve(answer);
      else w.reject(new Mb3dError(answer.error || "unknown error"));
    });
  }

  /** Sends a request of `mb3d serve` and gives its answer. */
  ask(request, progress) {
    return new Promise((resolve, reject) => {
      if (this.ended) return reject(new Mb3dError(this.ended));
      const id = ++this.next;
      this.waiting.set(id, { resolve, reject, progress });
      this.proc.stdin.write(JSON.stringify({ ...request, id }) + "\n");
    });
  }

  /** Ends the engine. */
  close() {
    this.proc.stdin.end();
  }

  /** Stops the pictures asked for so far: their render rejects with "cancelled". */
  cancel() {
    if (!this.ended) this.proc.stdin.write('{"op":"cancel","id":"cancel"}\n');
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
