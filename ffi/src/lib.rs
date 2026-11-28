//! mb3d-rs as a C library (`libmb3d`): the functions of `include/mb3d.h`.
//! They are the engine repository's own C functions (its capi/ folder,
//! crate mb3d-capi), which the iPad app is built from too: nothing is
//! written here, so the two cannot drift apart.  `include/mb3d.h` is that
//! crate's header, copied by tools/pin_engine.sh with every engine release.

pub use mb3d_capi::*;
