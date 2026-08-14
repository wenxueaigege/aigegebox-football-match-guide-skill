"""Standalone SVG/HTML/PNG output helpers."""

from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


def write_html(path: Path, title: str, svg: str, esc: Any) -> None:
    path.write_text(
        "<!doctype html><html lang=\"zh-CN\"><meta charset=\"utf-8\"><title>"
        + esc(title)
        + "</title><style>html,body{margin:0;background:#eee7dc}svg{display:block;width:100%;height:auto;max-width:1080px;margin:0 auto}</style>"
        + svg
        + "</html>\n",
        encoding="utf-8",
    )


def svg_dimensions(svg: str) -> tuple[int, int]:
    width_match = re.search(r'<svg[^>]+\bwidth="([0-9.]+)"', svg)
    height_match = re.search(r'<svg[^>]+\bheight="([0-9.]+)"', svg)
    if not width_match or not height_match:
        raise ValueError("SVG 母版缺少可读取的 width/height")
    return round(float(width_match.group(1))), round(float(height_match.group(1)))


def rasterizer_name() -> str:
    if shutil.which("rsvg-convert"):
        return "rsvg-convert"
    if importlib.util.find_spec("cairosvg"):
        return "cairosvg"
    return ""


def rasterizer_install_hint() -> str:
    return "macOS 推荐安装：brew install librsvg（安装后提供 rsvg-convert）"


def write_scaled_png(svg_path: Path, png_path: Path, svg: str, scale: int, rasterizer: str) -> tuple[int, int]:
    width, height = svg_dimensions(svg)
    output_width, output_height = width * scale, height * scale
    if rasterizer == "rsvg-convert":
        subprocess.run(
            [
                "rsvg-convert",
                "--width", str(output_width),
                "--height", str(output_height),
                "--output", str(png_path),
                str(svg_path),
            ],
            check=True,
        )
    elif rasterizer == "cairosvg":
        import cairosvg

        cairosvg.svg2png(
            bytestring=svg.encode("utf-8"),
            write_to=str(png_path),
            output_width=output_width,
            output_height=output_height,
        )
    else:
        raise RuntimeError(rasterizer_install_hint())
    return output_width, output_height
