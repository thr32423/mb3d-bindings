# The Node.js add-on

`mb3d.node`: the engine of mb3d-rs for Node.js, under the module
[../js](../js), which is what programs import. It answers the requests of
`mb3d serve` (mb3d-rs: docs/API.md) inside the program, each on one of
Node's worker threads.

    cargo build --release        # target/release/libmb3d_node.so (.dylib, mb3d_node.dll)

The JavaScript module finds it there; a package carries it as `mb3d.node`.
Licence: LGPL 2.1, like the engine ([../ffi/LICENSE](../ffi/LICENSE)).
