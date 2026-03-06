#!/usr/bin/env python3
"""
Repack an MSIX so that AppxManifest.xml, AppxBlockMap.xml, and
[Content_Types].xml are stored without compression, as required by the
MSIX/APPX specification.  Also regenerates AppxBlockMap.xml with the
correct SHA-256 hashes for the stored (uncompressed) data.

Usage: python repack_msix.py <input.msix> <output.msix>
"""
import base64
import hashlib
import struct
import sys
import zipfile
import xml.etree.ElementTree as ET

BLOCK_SIZE = 65536
BLOCK_MAP_NS = "http://schemas.microsoft.com/appx/2010/blockmap"
HASH_METHOD = "http://www.w3.org/2001/04/xmlenc#sha256"

# These files must not appear in AppxBlockMap.xml
BLOCK_MAP_EXCLUDED = frozenset(
    ["AppxBlockMap.xml", "[Content_Types].xml", "AppxSignature.p7x"]
)


def block_hashes(data: bytes) -> list[str]:
    """SHA-256 hash (base64) for each 64 KB block of raw data."""
    if not data:
        return [base64.b64encode(hashlib.sha256(b"").digest()).decode()]
    return [
        base64.b64encode(hashlib.sha256(data[i : i + BLOCK_SIZE]).digest()).decode()
        for i in range(0, len(data), BLOCK_SIZE)
    ]


def lfh_size(zip_path: str) -> int:
    """
    Size of the ZIP local file header for this entry.
    Python's zipfile writes no extra fields for small stored files,
    so LFH = 30 fixed bytes + UTF-8 filename bytes.
    """
    return 30 + len(zip_path.encode("utf-8"))


def verify_lfh_sizes(output_path: str, expected: dict[str, int]) -> None:
    """
    Scan the written ZIP and assert that every local file header size
    matches what we put into AppxBlockMap.xml.
    """
    mismatches = []
    with open(output_path, "rb") as f:
        data = f.read()
    i = 0
    while i + 30 <= len(data):
        if data[i : i + 4] != b"PK\x03\x04":
            break
        fname_len = struct.unpack_from("<H", data, i + 26)[0]
        extra_len = struct.unpack_from("<H", data, i + 28)[0]
        compress_sz = struct.unpack_from("<I", data, i + 18)[0]
        actual_lfh = 30 + fname_len + extra_len
        fname = data[i + 30 : i + 30 + fname_len].decode("utf-8")
        if fname in expected and expected[fname] != actual_lfh:
            mismatches.append(
                f"  {fname}: expected LfhSize={expected[fname]}, got {actual_lfh}"
            )
        i += actual_lfh + compress_sz
    if mismatches:
        print("WARNING: LFH size mismatches detected — BlockMap may be invalid:")
        print("\n".join(mismatches))
    else:
        print("  LFH sizes verified OK.")


def build_block_map(payload_files: list[tuple[str, bytes]]) -> bytes:
    """Build AppxBlockMap.xml for a list of (zip_path, raw_bytes) payload files."""
    ET.register_namespace("", BLOCK_MAP_NS)
    root = ET.Element(f"{{{BLOCK_MAP_NS}}}BlockMap")
    root.set("HashMethod", HASH_METHOD)

    for zip_path, data in payload_files:
        bm_path = zip_path.replace("/", "\\")
        fe = ET.SubElement(root, f"{{{BLOCK_MAP_NS}}}File")
        fe.set("Name", bm_path)
        fe.set("Size", str(len(data)))
        fe.set("LfhSize", str(lfh_size(zip_path)))
        for h in block_hashes(data):
            be = ET.SubElement(fe, f"{{{BLOCK_MAP_NS}}}Block")
            be.set("Hash", h)
            # No Size attribute for stored (uncompressed) entries

    xml_str = ET.tostring(root, encoding="unicode")
    return ('<?xml version="1.0" encoding="UTF-8"?>' + xml_str).encode("utf-8")


CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"

# Map file extensions to MIME types for payload files
EXTENSION_CONTENT_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
}

# Explicit Override entries required by AppxSip.dll
APPX_OVERRIDES = {
    "/AppxManifest.xml": "application/vnd.ms-appx.manifest+xml",
    "/AppxBlockMap.xml": "application/vnd.ms-appx.blockmap+xml",
}


def build_content_types(payload_files: list[tuple[str, bytes]]) -> bytes:
    """
    Build [Content_Types].xml using Override entries for MSIX metadata and
    Default entries for payload file extensions.  AppxSip.dll requires an
    explicit Override for AppxManifest.xml; a bare Default Extension="xml"
    is not sufficient for the modern SIP to recognise the package.
    """
    ET.register_namespace("", CONTENT_TYPES_NS)
    root = ET.Element(f"{{{CONTENT_TYPES_NS}}}Types")

    # Collect unique extensions from payload (exclude xml — handled via Override)
    seen_exts: set[str] = set()
    for zip_path, _ in payload_files:
        ext = zip_path.rsplit(".", 1)[-1].lower() if "." in zip_path else ""
        if ext and ext != "xml" and ext not in seen_exts:
            ct = EXTENSION_CONTENT_TYPES.get(ext, f"application/octet-stream")
            de = ET.SubElement(root, f"{{{CONTENT_TYPES_NS}}}Default")
            de.set("Extension", ext)
            de.set("ContentType", ct)
            seen_exts.add(ext)

    # Explicit Override entries for MSIX metadata files
    for part_name, ct in APPX_OVERRIDES.items():
        oe = ET.SubElement(root, f"{{{CONTENT_TYPES_NS}}}Override")
        oe.set("PartName", part_name)
        oe.set("ContentType", ct)

    xml_str = ET.tostring(root, encoding="unicode")
    return ('<?xml version="1.0" encoding="UTF-8" standalone="no"?>' + xml_str).encode("utf-8")


def repack(input_path: str, output_path: str) -> None:
    # ── Read all files from the input MSIX ──────────────────────────────────
    files: dict[str, bytes] = {}
    original_order: list[str] = []
    with zipfile.ZipFile(input_path, "r") as zin:
        for info in zin.infolist():
            if info.filename in ("AppxBlockMap.xml", "[Content_Types].xml"):
                continue  # regenerate below
            files[info.filename] = zin.read(info.filename)
            original_order.append(info.filename)

    # Payload files: everything except metadata written at the end
    payload_files = list(zip(original_order, [files[p] for p in original_order]))

    # ── Generate the new AppxBlockMap.xml and [Content_Types].xml ───────────
    block_map_bytes = build_block_map(payload_files)
    content_types_bytes = build_content_types(payload_files)

    # ── Write the new ZIP with ZIP_STORED for all entries ───────────────────
    # OPC/MSIX requires [Content_Types].xml to be the first entry in the ZIP.
    # signtool rejects the package with "file format not recognized" otherwise.
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_STORED) as zout:
        ct_info = zipfile.ZipInfo("[Content_Types].xml")
        ct_info.compress_type = zipfile.ZIP_STORED
        zout.writestr(ct_info, content_types_bytes)

        for zip_path, data in payload_files:
            info = zipfile.ZipInfo(zip_path)
            info.compress_type = zipfile.ZIP_STORED
            zout.writestr(info, data)

        bm_info = zipfile.ZipInfo("AppxBlockMap.xml")
        bm_info.compress_type = zipfile.ZIP_STORED
        zout.writestr(bm_info, block_map_bytes)

    # ── Verify LFH sizes match the BlockMap ─────────────────────────────────
    expected = {p: lfh_size(p) for p, _ in payload_files}
    verify_lfh_sizes(output_path, expected)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} input.msix output.msix")
        sys.exit(1)
    repack(sys.argv[1], sys.argv[2])
    print("  Repack complete.")
