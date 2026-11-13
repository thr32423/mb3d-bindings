# libmb3d: mb3d-rs as a C library

For programs that want the engine inside their own process and the pixels
in their own memory: C, C++, C#, Python (ctypes), game engines.
[include/mb3d.h](include/mb3d.h) describes every function. EXPERIMENTAL.

    cargo build --release        # target/release/libmb3d.so (.dylib, mb3d.dll)

It builds the engine from mb3d-rs's release tag named in Cargo.toml.

    cc examples/render.c -Iinclude -Ltarget/release -lmb3d -o render
    LD_LIBRARY_PATH=target/release ./render [file.m3p]

    python examples/render.py [file.m3p]

Notes:

* The library starts on the processor; `mb3d_use_gpu(1)` switches the
  graphics card on. A program that did calls `mb3d_finish()` before it ends.
* The progress function is called from the engine's threads, one call at a
  time; returning non-zero stops the calculation.
* A scene is used by one thread at a time.
* Licence: LGPL 2.1, like the engine. A program of any licence may load
  the library; changes to the library itself are published under the LGPL.

This folder holds the repository's only `unsafe` code: a C interface cannot
be written without it.
