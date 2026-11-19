# CLAUDE.md

This repo turns long videos into short clips. Your job is usually to pick good moments from a transcript and cut them with `scripts/clip.py`.

## Layout

- `input/` holds source videos. `transcripts/` holds timestamped transcripts. `clips/` is output. All three are git-ignored; never commit video files.
- `scripts/clip.py` is the cutter. It only needs Python 3 and ffmpeg.
- `examples/clips.json` shows the plan format.

## Workflow

1. Check ffmpeg is available: `ffmpeg -version`. If it's missing, tell the user and stop.
2. Find the source video in `input/` and its transcript in `transcripts/`. If there is no transcript, ask the user for one rather than guessing timestamps.
3. Read the transcript and pick clips. Good clips:
   - stand on their own without the surrounding context,
   - open with a hook in the first few seconds,
   - start and end on sentence boundaries, never mid-word,
   - are 20–60 seconds unless the user asks otherwise.
4. Write the plan to `clips/plan.json` as a list of `{"name", "start", "end", "why"}`. Pad each clip by about 0.5s on both sides of the spoken words.
5. Show the user the plan (name, times, length, why) and wait for their go-ahead before cutting, unless they already asked you to cut straight away.
6. Cut:
   ```bash
   python3 scripts/clip.py input/<video> --plan clips/plan.json --out-dir clips/
   ```
   Add `--vertical` for Shorts/Reels/TikTok. Use `--fast` only if the user cares more about speed than exact cut points.
7. Report the files written and their lengths. If ffmpeg fails, show its error and the command you ran.

## Rules

- Don't overwrite or delete anything in `input/`.
- Get timestamps from the transcript only. Don't invent them.
- To check a video's length: `ffprobe -v error -show_entries format=duration -of csv=p=0 <file>`.
- Quick self-test of the script with a generated video:
  ```bash
  ffmpeg -f lavfi -i testsrc=duration=20:size=1280x720:rate=30 -f lavfi -i sine=duration=20 -shortest -y /tmp/test.mp4
  python3 scripts/clip.py /tmp/test.mp4 --start 2 --end 7 --out /tmp/out.mp4
  ```
