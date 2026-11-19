#!/usr/bin/env python3
"""Cut short clips out of a long video with ffmpeg.

Single clip:
    python3 scripts/clip.py input.mp4 --start 00:01:30 --end 00:02:15 --out clips/intro.mp4

Many clips from a plan file (JSON list of {name, start, end}):
    python3 scripts/clip.py input.mp4 --plan examples/clips.json --out-dir clips/

Times can be seconds (90, 90.5) or timestamps (1:30, 00:01:30.250).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


def parse_time(value: str | float | int) -> float:
    """Turn '90', '1:30', or '00:01:30.5' into seconds."""
    if isinstance(value, (int, float)):
        seconds = float(value)
    else:
        text = str(value).strip()
        if not re.fullmatch(r"\d+(:\d{1,2}){0,2}(\.\d+)?", text):
            raise ValueError(f"Bad time {value!r}. Use seconds or HH:MM:SS(.ms).")
        seconds = 0.0
        for part in text.split(":"):
            seconds = seconds * 60 + float(part)
    if seconds < 0:
        raise ValueError(f"Time can't be negative: {value!r}")
    return seconds


def video_duration(path: Path) -> float | None:
    """Length of the video in seconds, or None if ffprobe can't tell."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return float(out)
    except (subprocess.CalledProcessError, ValueError):
        return None


def build_command(src: Path, dst: Path, start: float, end: float,
                  fast: bool, vertical: bool) -> list[str]:
    duration = end - start
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    if fast:
        # Stream copy: very quick, but cuts snap to the nearest keyframe.
        cmd += ["-ss", f"{start:.3f}", "-i", str(src), "-t", f"{duration:.3f}",
                "-c", "copy", "-avoid_negative_ts", "make_zero"]
    else:
        # Re-encode: frame-accurate cuts.
        cmd += ["-ss", f"{start:.3f}", "-i", str(src), "-t", f"{duration:.3f}"]
        if vertical:
            # Center-crop to 9:16 and scale to 1080x1920 for Shorts/Reels/TikTok.
            cmd += ["-vf", "crop='min(iw,ih*9/16)':'min(ih,iw*16/9)',scale=1080:1920,setsar=1"]
        cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart"]
    cmd.append(str(dst))
    return cmd


def cut(src: Path, dst: Path, start, end, *, fast=False, vertical=False,
        total: float | None = None) -> None:
    s, e = parse_time(start), parse_time(end)
    if e <= s:
        raise ValueError(f"End ({end}) must be after start ({start}).")
    if total is not None and s >= total:
        raise ValueError(f"Start {start} is past the end of the video ({total:.1f}s).")
    if total is not None and e > total:
        print(f"  note: end {end} is past the video end, clipping to {total:.1f}s", file=sys.stderr)
        e = total
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(build_command(src, dst, s, e, fast, vertical), check=True)
    print(f"  wrote {dst} ({e - s:.1f}s)")


def safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_") or "clip"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Cut clips from a long video with ffmpeg.")
    p.add_argument("input", type=Path, help="Path to the long source video")
    p.add_argument("--start", help="Clip start (seconds or HH:MM:SS)")
    p.add_argument("--end", help="Clip end (seconds or HH:MM:SS)")
    p.add_argument("--out", type=Path, help="Output file for a single clip")
    p.add_argument("--plan", type=Path, help="JSON file listing clips: [{name, start, end}]")
    p.add_argument("--out-dir", type=Path, default=Path("clips"), help="Folder for --plan output (default: clips/)")
    p.add_argument("--fast", action="store_true", help="Stream copy instead of re-encoding (fast, keyframe-accurate only)")
    p.add_argument("--vertical", action="store_true", help="Center-crop to 9:16 (1080x1920) for short-form platforms")
    args = p.parse_args(argv)

    if shutil.which("ffmpeg") is None:
        p.error("ffmpeg isn't installed or isn't on PATH.")
    if not args.input.is_file():
        p.error(f"Input video not found: {args.input}")
    if args.fast and args.vertical:
        p.error("--vertical needs re-encoding, so it can't be combined with --fast.")

    total = video_duration(args.input)
    opts = dict(fast=args.fast, vertical=args.vertical, total=total)

    try:
        if args.plan:
            clips = json.loads(args.plan.read_text())
            if not isinstance(clips, list) or not clips:
                p.error("Plan file must be a non-empty JSON list.")
            print(f"Cutting {len(clips)} clip(s) from {args.input}")
            for i, clip in enumerate(clips, 1):
                name = safe_name(clip.get("name") or f"clip_{i:02d}")
                cut(args.input, args.out_dir / f"{i:02d}_{name}.mp4",
                    clip["start"], clip["end"], **opts)
        else:
            if not (args.start and args.end and args.out):
                p.error("Give --start, --end and --out, or use --plan.")
            cut(args.input, args.out, args.start, args.end, **opts)
    except (ValueError, KeyError) as err:
        p.error(str(err))
    except subprocess.CalledProcessError as err:
        print(f"ffmpeg failed (exit {err.returncode}).", file=sys.stderr)
        return err.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
