// The explorer's back end in JavaScript.   node server.mjs   then open http://127.0.0.1:8765
//
// The page (index.html) asks this small web server, which asks the mb3d
// engine through the JavaScript module.  It listens on this computer only.

import { createServer } from "node:http";
import { readFile, mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { Engine } from "../../js/mb3d.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const engine = await Engine.start();
let scene = await engine.preset("Amazing Box");
let progress = { stage: "", done: 0, total: 0 };
let latest = 0; // the newest picture the page asked for (its `seq`)

const about = async (s) => ({ width: s.width, height: s.height, formulas: s.formulas.map((f) => [f.name, f.iterations]), rotation: s.rotation, notes: s.notes, text: await s.text() });

function send(res, body, kind = "application/json", status = 200, headers = {}) {
  if (!Buffer.isBuffer(body)) body = Buffer.from(JSON.stringify(body));
  res.writeHead(status, { "Content-Type": kind, "Content-Length": body.length, ...headers });
  res.end(body);
}

async function read(req) {
  const parts = [];
  for await (const p of req) parts.push(p);
  return JSON.parse(Buffer.concat(parts).toString() || "{}");
}

const server = createServer(async (req, res) => {
  try {
    if (req.method === "GET" && req.url.split("?")[0] === "/") {
      send(res, await readFile(join(here, "index.html")), "text/html; charset=utf-8");
    } else if (req.method === "GET" && req.url === "/api/info") {
      send(res, { version: engine.version, formulas: await engine.formulas() });
    } else if (req.method === "GET" && req.url === "/api/progress") {
      send(res, progress);
    } else if (req.method === "GET" && req.url === "/api/m3p") {
      const dir = await mkdtemp(join(tmpdir(), "mb3d-"));
      try {
        await scene.save(join(dir, "scene.m3p"));
        send(res, await readFile(join(dir, "scene.m3p")), "application/octet-stream");
      } finally {
        await rm(dir, { recursive: true });
      }
    } else if (req.method === "POST" && req.url === "/api/open") {
      const body = await read(req);
      const next = "preset" in body ? await engine.preset(body.preset) : "text" in body ? await engine.fromText(body.text) : await engine.fromBytes(Buffer.from(body.data, "base64"), body.name);
      const old = scene;
      scene = next;
      latest = 0;
      await old.close();
      send(res, await about(next));
    } else if (req.method === "POST" && req.url === "/api/render") {
      const body = await read(req);
      // the page counts its requests: one that arrives after a newer one
      // shows no picture
      const seq = body.seq ?? latest + 1;
      if (seq < latest) throw new Error("cancelled");
      latest = seq;
      engine.cancel(); // a picture still on its way is not wanted any more
      if (body.changes) await scene.set(body.changes);
      const report = (stage, done, total) => (progress = { stage, done, total });
      const p = await scene.render({ width: body.width, progress: body.progress ? report : undefined });
      send(res, p.png, "image/png", 200, { "X-Width": p.width, "X-Height": p.height, "X-Seconds": p.seconds, "X-Device": p.device });
    } else {
      send(res, { error: "not found" }, "application/json", 404);
    }
  } catch (e) {
    send(res, { error: e.message }, "application/json", e.message === "cancelled" ? 409 : 400);
  }
});

const port = Number(process.argv[2]) || 8765;
server.listen(port, "127.0.0.1", () => console.log(`mb3d ${engine.version}: open http://127.0.0.1:${port}`));
process.on("SIGINT", () => { engine.close(); process.exit(0); });
