---
name: lyric-video-pv
description: This skill should be used when the user wants to create an artistic Chinese text/kinetic-typography music video (文字视频PV / 文字PV) from an audio file and timed lyrics. It covers the full pipeline from lyric timing, per-section typographic design, audio-driven animation, frame rendering, and final MP4 encoding.
agent_created: true
---

# 文字视频 PV 制作

## Overview

Turn a song and its timed lyrics into a cinematic Chinese text PV. The pipeline uses Python + Pillow for frame-by-frame rendering and FFmpeg for encoding. It is suitable for emotionally charged songs where typography itself is the visual language.

## When to Use

- User provides an audio file and a lyrics timestamp file.
- User asks for 文字PV, 文字视频, lyric video, kinetic typography, or music video with Chinese lyrics.
- Desired aesthetic is documentary / ink-judgment / official-document style (文书风 / 判词风).

## Workflow

1. **Confirm creative direction**
   - Ask the user to choose a visual style (e.g., 墨判文书风, 故障风, 极简白底).
   - Confirm aspect ratio and resolution (default 16:9 1920×1080).
   - Ask whether lyrics are authoritative; transcribed timestamps often contain errors.

2. **Prepare assets**
   - Audio file: keep as source, extract envelope via FFmpeg PCM decode.
   - Lyrics: parse `(index, text, start, end)` tuples. Keep punctuation because it drives line splitting.
   - Fonts: use a strong serif for body (e.g., Noto Serif SC) and a calligraphy/kai face for annotations/seals (e.g., simkai).

3. **Design the typographic system**
   - Divide the song into sections and assign each a distinct layout paradigm:
     - **序 / accusation**: left-aligned prose, red vertical line, slide-in from left.
     - **怒 / heavy**: centered oversized type, red-block keyword, red back-flash, scale slam.
     - **间奏 / interlude**: grid list (e.g., 4×4 crime counts with circled numbers).
     - **冥 / vertical**: top-to-bottom columns, right-to-left reveal, like a stone inscription.
     - **判 / verdict**: full-frame red border, corner marks, seal stamp, slash line.
   - Use no more than one paradigm per section; the contrast between sections is the design.

4. **Render pipeline**
   - Pre-render each line/row as an RGBA layer once, then animate position/scale/alpha.
   - Build a static background and reusable overlays (grain, vignette, watermarks, radial lines, seal).
   - Extract audio envelope: `ffmpeg -i audio.mp3 -f s16le -ac 1 -ar 16000 -` → RMS per frame + low-pass.
   - Compute onset punch from envelope derivative to drive scale pops and flashes.
   - Render frames with Pillow and pipe rawvideo to FFmpeg (`-f rawvideo -pix_fmt rgb24`) with x264 + AAC.

5. **Encode and deliver**
   - Master: CRF 18–24 for local review.
   - Share version: CRF 26, AAC 192k, `+faststart` for web playback.
   - Copy the share version to the user's requested location.

## Key Design Rules

- **One idea per section**: never reuse the same layout for the whole song.
- **Keyword hierarchy**: in each line, highlight 1 longest keyword with a red block, others in red text, body in muted paper color.
- **Avoid clipping**: size each section so its settled scale fits inside the frame with safe margins; allow only brief entrance overshoot.
- **Audio sync**: scale, glow, and flash should pulse with the music, not run on arbitrary timers.
- **码率控制**: full-screen animated grain destroys compression; keep grain alpha low (<0.15) or update it sparsely.

## Common Pitfalls

- Whisper transcripts are not lyrics; always ask the user to confirm the text before rendering.
- `np.percentile` on audio envelope is poisoned by a single NaN; use `np.nan_to_num` and clamp indices.
- Do not run Chinese/quoted content through inline `python -c`; write a `.py` file and execute it.
- If the sandbox safe-delete hook fails closed, temp files cannot be removed; just leave them.
- Heavy-mode long lines will clip unless you compute `fit_scale = (W - 2*margin) / max_row_width`.

## Resources

- `references/workflow.md` — full step-by-step checklist and parameter cheatsheet.
- `scripts/example_renderer.py` — minimal stub renderer for a new PV project.
