// node --test   (in js/; MB3D=/path/to/mb3d)
import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, stat, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { Engine, Mb3dError } from "./mb3d.mjs";

const engine = await Engine.start({ cpu: true });
test.after(() => engine.close());

test("a preset changes and renders", async () => {
  const s = await engine.preset("Integer Power");
  await s.set({ iterations: 8, rotation: [-40, 30, 10] });
  assert.equal(await s.get("iterations"), "8");
  assert.ok(Math.abs(s.rotation[0] + 40) < 1e-4);
  await assert.rejects(s.set("no_such_key = 1"), Mb3dError);
  const p = await s.render({ width: 96, progress: () => {} });
  assert.deepEqual([p.width, p.height], [96, 72]);
  assert.equal(p.png.subarray(1, 4).toString(), "PNG");
  assert.equal(s.width, 800, "the scene keeps its own size");
});

test("pixels, depth and files", async () => {
  const s = await (await engine.preset("Amazing Box")).resize({ width: 64 });
  const p = await s.render({ pixels: true, depth: true });
  assert.equal(p.rgb.length, p.width * p.height * 3);
  assert.equal(p.depth.length, p.width * p.height * 2);
  const dir = await mkdtemp(join(tmpdir(), "mb3d-js-"));
  try {
    const q = await s.render({ file: join(dir, "a.png") });
    assert.equal(q.png, undefined);
    assert.ok((await stat(join(dir, "a.png"))).size > 100);
    await s.save(join(dir, "a.m3p"));
    const again = await engine.open(join(dir, "a.m3p"));
    assert.equal(again.width, s.width);
    const bytes = await engine.fromBytes(await readFile(join(dir, "a.m3p")));
    assert.deepEqual(bytes.formulas, s.formulas);
  } finally {
    await rm(dir, { recursive: true });
  }
  assert.equal(await (await engine.fromText(await s.text())).text(), await s.text());
});

test("formulas and copies", async () => {
  assert.ok((await engine.formulas()).includes("Amazing Box"));
  assert.ok(Object.keys(await engine.formulaSettings("Amazing Box")).length > 0);
  const box = await engine.preset("Amazing Box");
  const slot = box.formulas[0].slot;
  assert.equal(box.formulas[0].settings.Scale, 2);
  await box.setFormula(slot, { Scale: 2.5 }, 2);
  assert.deepEqual([box.formulas[0].settings.Scale, box.formulas[0].iterations], [2.5, 2]);
  await assert.rejects(box.setFormula(slot, { "No such value": 1 }), Mb3dError);
  const a = await engine.preset("Integer Power");
  const b = await (await a.copy()).set({ zoom: 2 });
  assert.notEqual(await a.get("zoom"), await b.get("zoom"));
  await a.close();
  await assert.rejects(a.text(), Mb3dError);
});

test("a render is cancelled", async () => {
  const s = await engine.preset("Integer Power");
  let asked = false;
  const big = s.render({ width: 4000, progress: () => { if (!asked) { asked = true; engine.cancel(); } } });
  await assert.rejects(big, /cancelled/);
  assert.equal((await s.render({ width: 64 })).width, 64, "the engine goes on after a cancel");
});

test("a missing program is named", async () => {
  await assert.rejects(Engine.start({ program: "/no/such/mb3d" }), /not found/);
});
