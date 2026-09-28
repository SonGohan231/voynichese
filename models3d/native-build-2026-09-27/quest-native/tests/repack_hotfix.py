"""Repackage only reviewed GDScripts over the verified 0.3.0 APK.

Native libraries, Android classes, permissions and source bytes remain unchanged.
Run Android SDK zipalign -P 16 4 and apksigner afterwards, with the existing key.
The matching Godot 4.6 runtime can load source GDScript when its export remap is removed.
"""
import argparse
import hashlib
from pathlib import Path
import struct
import zipfile

BASE_SHA = "24c5db37b93f6247eaa501e93f96edfe5baf44fa3bedb6290cbd6ee79300807c"
SCRIPTS = ["workroom", "compound", "source_reader"]

def manifest_version(data):
    data = bytearray(data)
    # Both strings have the same byte length; preserve the AXML string pool offsets.
    old = "0.3.0".encode("utf-16-le")
    assert data.count(old) == 1
    data[data.index(old):data.index(old)+len(old)] = "0.3.1".encode("utf-16-le")
    cursor, patched = 8, 0
    resources = []
    while cursor < len(data):
        kind, header, size = struct.unpack_from("<HHI", data, cursor)
        assert size >= header and size > 0
        if kind == 0x0180:
            resources = list(struct.unpack_from("<" + "I" * ((size-header)//4), data, cursor+header))
        elif kind == 0x0102:
            attr_start, attr_size, count = struct.unpack_from("<HHH", data, cursor+24)
            for i in range(count):
                at = cursor + 16 + attr_start + i * attr_size
                name = struct.unpack_from("<I", data, at+4)[0]
                if name < len(resources) and resources[name] == 0x0101021b:
                    assert data[at+15] == 0x10
                    assert struct.unpack_from("<I", data, at+16)[0] == 3
                    struct.pack_into("<I", data, at+16, 4)
                    patched += 1
        cursor += size
    assert patched == 1
    return bytes(data)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base", type=Path)
    parser.add_argument("project", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with args.base.open("rb") as f:
        assert hashlib.file_digest(f, "sha256").hexdigest() == BASE_SHA
    omitted = {f"assets/scripts/{name}{extension}" for name in SCRIPTS for extension in [".gd", ".gd.remap", ".gdc"]}
    with zipfile.ZipFile(args.base) as original, zipfile.ZipFile(args.output, "w", allowZip64=True) as target:
        for info in original.infolist():
            name = info.filename
            if name in omitted: continue
            if name.startswith("META-INF/") and (name.endswith((".SF", ".RSA", ".DSA", ".EC")) or name == "META-INF/MANIFEST.MF"): continue
            data = original.read(name)
            if name == "AndroidManifest.xml": data = manifest_version(data)
            info.extra = b""  # zipalign regenerates alignment after reassembly.
            target.writestr(info, data)
        for name in SCRIPTS:
            target.write(args.project / "scripts" / f"{name}.gd", f"assets/scripts/{name}.gd", compress_type=zipfile.ZIP_DEFLATED)
    with zipfile.ZipFile(args.output) as result:
        assert result.testzip() is None
    print("Repackaged 0.3.1 (unsigned); align and sign before installation.")

if __name__ == "__main__": main()
