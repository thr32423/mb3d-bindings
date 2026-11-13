// The smallest web use: a page with one fractal picture.
//
//     node server.mjs      then open http://127.0.0.1:8766
//
// GET /fractal.png?formula=Amazing%20Box&zoom=0.3&width=640 gives a PNG.

import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { Engine } from "../../js/mb3d.mjs";

const engine = await Engine.start();

createServer(async (req, res) => {
  const url = new URL(req.url, "http://127.0.0.1");
  try {
    if (url.pathname === "/fractal.png") {
      const scene = await engine.preset(url.searchParams.get("formula") || "Amazing Box");
      await scene.set({ zoom: Number(url.searchParams.get("zoom")) || 0.17 });
      const picture = await scene.render({ width: Math.min(Number(url.searchParams.get("width")) || 640, 1920) });
      await scene.close();
      res.writeHead(200, { "Content-Type": "image/png" }).end(picture.png);
    } else {
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" }).end(await readFile(new URL("index.html", import.meta.url)));
    }
  } catch (e) {
    res.writeHead(400, { "Content-Type": "text/plain; charset=utf-8" }).end(e.message);
  }
}).listen(8766, "127.0.0.1", () => console.log("open http://127.0.0.1:8766"));
