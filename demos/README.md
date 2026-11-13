# Demos: mb3d in a web page

A web page cannot run the engine itself: it asks a small server, and the
server asks `mb3d` through the Python or JavaScript module. Each demo has
both servers; they do the same. They listen on this computer only
(127.0.0.1).

Set `MB3D` to the program first (see the main README).

## minimal: one picture

    python demos/minimal/server.py        or        node demos/minimal/server.mjs

http://127.0.0.1:8766 — a page with an `<img>` whose address is
`/fractal.png?formula=...&zoom=...`; the server (30 lines) renders it. The
place to start reading.

## explorer: turn, zoom, open, save

    python demos/explorer/server.py       or        node demos/explorer/server.mjs

http://127.0.0.1:8765 — drag the picture to turn the fractal, the wheel
zooms; sliders for the view and the iterations; opens `.m3p` files; saves a
large picture with a progress bar, and the parameters. A quick small picture
follows the hand, a sharp one comes when it rests; a picture that is no
longer wanted is cancelled. The page shows the same steps as Python and
JavaScript code.

What the page asks its server:

| request | answer |
|---|---|
| `GET /api/info` | the engine's version and the formula names |
| `POST /api/open` `{preset}` or `{name, data}` (Base64) or `{text}` | the scene: size, formulas, view angles, text |
| `POST /api/render` `{width, changes, progress, seq}` | a PNG (409 when a newer request, one with a higher `seq`, cancelled it) |
| `GET /api/progress` | stage, done, total of the picture being calculated |
| `GET /api/m3p` | the scene as a parameter file |

These servers are for one person at one computer: one scene, no accounts,
no limits. A public web site would need its own scenes per visitor and
limits on picture sizes.
