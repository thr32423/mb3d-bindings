#!/usr/bin/env bash
# Pins the bindings to an engine release: tools/pin_engine.sh v0.3.15
# Changes the tag in ffi/ and node/Cargo.toml, their Cargo.lock files and
# the examples of README.md and GUIDE.md, and takes that release's header
# (the engine's capi/include/mb3d.h, which libmb3d's functions come from)
# as ffi/include/mb3d.h.
set -euo pipefail
tag=${1:?usage: tools/pin_engine.sh vX.Y.Z}
case "$tag" in v[0-9]*.[0-9]*.[0-9]*) ;; *) echo "not a version tag: $tag" >&2; exit 1;; esac
cd "$(dirname "$0")/.."
sed -i.bak -E "s#(mb3d-rs\", tag = \")v[0-9.]+(\")#\1$tag\2#" ffi/Cargo.toml node/Cargo.toml README.md GUIDE.md
rm -f ffi/Cargo.toml.bak node/Cargo.toml.bak README.md.bak GUIDE.md.bak
for crate in ffi node; do
  cargo update --manifest-path $crate/Cargo.toml -p mb3d
done
# the header of the pinned release, from cargo's copy of the engine
capi=$(cargo metadata --manifest-path ffi/Cargo.toml --format-version 1 --locked |
  python3 -c 'import json, os, sys; print(next(os.path.dirname(p["manifest_path"]) for p in json.load(sys.stdin)["packages"] if p["name"] == "mb3d-capi"))')
cp "$capi/include/mb3d.h" ffi/include/mb3d.h
