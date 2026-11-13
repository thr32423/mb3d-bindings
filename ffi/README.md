# libmb3d: mb3d-rs as a C library

For programs that want the engine inside their own process and the pixels
in their own memory: C, C++, C#, Python (ctypes), game engines.
[include/mb3d.h](include/mb3d.h) describes every function. EXPERIMENTAL.

The releases page has it built for Linux, Windows and macOS
(`libmb3d-0.2.0-SYSTEM.tar.gz`: the library, `mb3d.h`, the formula and map
folders, these examples). In the unpacked folder:

    cc examples/render.c -I. -L. -lmb3d -o render
    LD_LIBRARY_PATH=. ./render [file.m3p]

    LIBMB3D=./libmb3d.so python examples/render.py [file.m3p]

The formulas that are files (most of Mandelbulb3D's) and the maps are found
once the program names their folders: `mb3d_add_formula_folder("M3Formulas")`,
`mb3d_add_formula_folder("EM_JIT_M3Formulas")`, `mb3d_add_map_folder("M3Maps")`.

Building it here (needs Rust; it builds the engine from mb3d-rs's release
tag named in Cargo.toml):

    cargo build --release        # target/release/libmb3d.so (.dylib, mb3d.dll)
    cc examples/render.c -Iinclude -Ltarget/release -lmb3d -o render
    LD_LIBRARY_PATH=target/release ./render [file.m3p]

Wrappers for other languages can use the session functions at the end of
the header: the requests of `mb3d serve` (mb3d-rs: docs/API.md) as JSON,
answered inside the program. The Python module is built on them.

Notes:

* The library starts on the processor; `mb3d_use_gpu(1)` switches the
  graphics card on. A program that did calls `mb3d_finish()` before it ends.
* The progress function is called from the engine's threads, one call at a
  time; returning non-zero stops the calculation.
* A scene is used by one thread at a time.
* Licence: LGPL 2.1, like the engine. A program of any licence may load
  the library; changes to the library itself are published under the LGPL.

This folder holds the repository's only hand-written `unsafe` code: a C
interface cannot be written without it.
