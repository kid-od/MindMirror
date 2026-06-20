from __future__ import annotations

from hashlib import sha1
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import quote
import binascii
import shutil
import subprocess
import struct
import zlib


DEFAULT_COVER_SIZE = (720, 1024)


def _preview_filename(filename: str) -> str:
    digest = sha1((filename or "").encode("utf-8")).hexdigest()
    return f"{digest}.png"


def preview_cache_path(filename: str, base_dir: Path) -> Path:
    return base_dir / "document_covers" / _preview_filename(filename)


def build_cover_url(filename: str, version: int | str | None) -> str:
    encoded = quote(filename, safe="")
    suffix = f"&v={version}" if version is not None else ""
    return f"/document-cover?filename={encoded}{suffix}"


def _png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    length = struct.pack(">I", len(payload))
    checksum = binascii.crc32(chunk_type + payload) & 0xFFFFFFFF
    return length + chunk_type + payload + struct.pack(">I", checksum)


def _write_png(width: int, height: int, rows: list[bytes], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    raw = b"".join(b"\x00" + row for row in rows)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    # 直接写标准 PNG 数据块，避免为了占位封面再额外依赖 Pillow。
    png = b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            _png_chunk(b"IHDR", ihdr),
            _png_chunk(b"IDAT", zlib.compress(raw, level=9)),
            _png_chunk(b"IEND", b""),
        ]
    )
    output_path.write_bytes(png)


def render_placeholder_cover(filename: str, output_path: Path, file_type: str = "Document") -> None:
    width, height = DEFAULT_COVER_SIZE
    accent_seed = sum(ord(char) for char in f"{file_type}:{filename}") % 3
    accents = [
        (31, 26, 23),
        (85, 107, 130),
        (108, 122, 98),
    ]
    accent = accents[accent_seed]
    background = (244, 239, 230)
    card = (255, 250, 244)
    block = (241, 232, 219)
    block_soft = (228, 218, 205)
    line = (216, 206, 192)

    rows: list[bytes] = []
    for y in range(height):
        row = bytearray()
        for x in range(width):
            color = background

            if 48 <= x < width - 48 and 48 <= y < height - 48:
                color = card
                if x < 51 or x >= width - 51 or y < 51 or y >= height - 51:
                    color = line

            if 92 <= x < width - 92 and 116 <= y < 196:
                color = accent
            elif 92 <= x < width - 92 and 232 <= y < 700:
                color = block
            elif 92 <= x < width - 92 and 748 <= y < 892:
                color = block_soft
            elif 92 <= x < 264 and 920 <= y < 976:
                color = accent

            row.extend(color)
        rows.append(bytes(row))

    _write_png(width, height, rows, output_path)


def render_quicklook_cover(file_path: Path, output_path: Path) -> bool:
    qlmanage = shutil.which("qlmanage")
    if not qlmanage or not file_path.exists():
        return False

    with TemporaryDirectory() as tmpdir:
        # macOS 上优先走 Quick Look，能拿到更接近真实书封的首图缩略图。
        result = subprocess.run(
            [qlmanage, "-t", "-s", "720", "-o", tmpdir, str(file_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return False

        candidates = sorted(Path(tmpdir).glob("*.png"))
        if not candidates:
            return False

        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(candidates[0]), str(output_path))
        return True


def ensure_document_cover(file_path: Path, filename: str, file_type: str, base_dir: Path) -> Path | None:
    cover_path = preview_cache_path(filename, base_dir)
    source_mtime = int(file_path.stat().st_mtime) if file_path.exists() else 0

    if cover_path.exists() and int(cover_path.stat().st_mtime) >= source_mtime:
        return cover_path

    # 真实预览拿不到时，再回退到本地生成的占位封面，确保知识库卡片始终有稳定视觉占位。
    if render_quicklook_cover(file_path, cover_path):
        return cover_path

    render_placeholder_cover(filename, cover_path, file_type=file_type)
    return cover_path if cover_path.exists() else None


def delete_document_cover(filename: str, base_dir: Path) -> None:
    cover_path = preview_cache_path(filename, base_dir)
    if cover_path.exists():
        cover_path.unlink()
