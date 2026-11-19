# Long video → short clips, with Claude Code

A starter workflow for turning a long video (podcast, stream, talk, interview) into short clips using Claude Code and ffmpeg.

Claude Code does the thinking (finding the moments worth clipping); a small script does the cutting.

## How it works

1. **Drop in a video.** Put the long source video in `input/` (ignored by git).
2. **Get a transcript.** Add a timestamped transcript to `transcripts/`, for example an `.srt` or `.vtt` from YouTube, your recording tool, or Whisper.
3. **Ask Claude Code to pick clips.** Claude reads the transcript and writes a clip plan: a JSON list of moments with start and end times and a one-line reason for each. See [`examples/clips.json`](examples/clips.json).
4. **Review the plan.** Edit the JSON if you want to drop, add, or nudge any clip.
5. **Cut.** Claude runs `scripts/clip.py`, which uses ffmpeg to cut each clip into `clips/`.

```
input/talk.mp4 ──► transcripts/talk.srt ──► clip plan (JSON) ──► scripts/clip.py ──► clips/*.mp4
                     (you or Whisper)        (Claude Code)          (ffmpeg)
```

## Requirements

- Python 3.9+ (standard library only)
- [ffmpeg](https://ffmpeg.org/download.html) on your PATH (`ffmpeg -version` should work)
- [Claude Code](https://claude.com/claude-code)

## Using the script directly

Cut one clip:

```bash
python3 scripts/clip.py input/talk.mp4 --start 00:12:10 --end 00:13:05 --out clips/insight.mp4
```

Cut every clip in a plan:

```bash
python3 scripts/clip.py input/talk.mp4 --plan examples/clips.json --out-dir clips/
```

Times can be seconds (`90`, `90.5`) or timestamps (`1:30`, `00:01:30.250`).

| Flag | What it does |
| --- | --- |
| `--vertical` | Center-crops to 9:16 at 1080x1920 for Shorts, Reels, and TikTok |
| `--fast` | Copies the streams without re-encoding. Much faster, but cuts snap to the nearest keyframe, so starts can be off by a second or two |

By default clips are re-encoded (H.264 + AAC), which gives frame-accurate cuts.

## Using it with Claude Code

Open this folder in Claude Code and ask something like:

> Find the 5 best 30–60 second moments in `transcripts/talk.srt` and cut them from `input/talk.mp4` as vertical clips.

`CLAUDE.md` tells Claude how to read the transcript, write the plan, and run the script.

## Plan file format

```json
[
  {"name": "hook", "start": "00:00:05", "end": "00:00:35", "why": "Strong opening question"}
]
```

`name` becomes part of the file name (`01_hook.mp4`). `why` is for you; the script ignores it.

## What's next

This is a skeleton. Natural next steps: auto-transcribe with Whisper, burn in captions, smarter reframing that follows the speaker, and a review step that previews clips before export.
