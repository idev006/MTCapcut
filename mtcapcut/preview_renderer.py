"""Deterministic FFmpeg preview renderer for provider-neutral Timeline Plans.

This is a review renderer, not a replacement for the editable CapCut draft.
It never overwrites an existing export and never mixes source-video audio.
"""

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Callable

from .timeline import Segment, TimelinePlan, validate_plan


@dataclass(frozen=True)
class RenderResult:
    output: Path
    title_artifact: Path
    duration_us: int
    visual_count: int
    audio_count: int
    text_count: int


def _seconds(value_us: int) -> str:
    return f"{value_us / 1_000_000:.6f}"


def _ass_time(value_us: int) -> str:
    centiseconds = max(0, value_us // 10_000)
    hours, remainder = divmod(centiseconds, 360_000)
    minutes, remainder = divmod(remainder, 6_000)
    seconds, fraction = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{seconds:02d}.{fraction:02d}"


def _ass_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("\n", "\\N")


def _filter_path(path: Path) -> str:
    value = path.resolve().as_posix().replace(":", r"\:").replace("'", r"\'")
    return f"'{value}'"


class PreviewRenderEngine:
    producer_version = "1"

    def __init__(self, ffmpeg: Path,
                 runner: Callable[..., subprocess.CompletedProcess] = subprocess.run):
        self.ffmpeg = ffmpeg.resolve()
        self.runner = runner

    def render(self, plan: TimelinePlan, output: Path) -> RenderResult:
        errors = validate_plan(plan)
        if errors:
            raise ValueError("; ".join(errors))
        if not self.ffmpeg.is_file():
            raise FileNotFoundError(self.ffmpeg)
        output = output.resolve()
        if output.suffix.lower() != ".mp4":
            raise ValueError("preview output must use the .mp4 extension")
        if output.exists():
            raise FileExistsError(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        titles = output.with_suffix(".titles.ass")
        if titles.exists():
            raise FileExistsError(titles)

        visuals = sorted((item for item in plan.segments if item.kind in {"video", "picture"}),
                         key=lambda item: item.start_us)
        audio = sorted((item for item in plan.segments if item.kind == "audio"),
                       key=lambda item: item.start_us)
        text = sorted((item for item in plan.segments if item.kind == "text"),
                      key=lambda item: item.start_us)
        self._validate_review_scope(plan, visuals, audio)
        for item in (*visuals, *audio):
            if item.source_path is None or not item.source_path.is_file():
                raise FileNotFoundError(item.source_path)

        titles.write_text(self._ass_document(plan, text), encoding="utf-8-sig")
        command = self._command(plan, visuals, audio, titles, output)
        try:
            completed = self.runner(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
        except Exception:
            titles.unlink(missing_ok=True)
            raise
        if completed.returncode != 0:
            titles.unlink(missing_ok=True)
            detail = (completed.stderr or completed.stdout or "ffmpeg failed")[-3000:]
            raise RuntimeError(detail)
        if not output.is_file() or output.stat().st_size < 1:
            raise RuntimeError("ffmpeg reported success but no preview was created")
        return RenderResult(output, titles, plan.duration_us, len(visuals), len(audio), len(text))

    @staticmethod
    def _validate_review_scope(plan: TimelinePlan, visuals: list[Segment], audio: list[Segment]) -> None:
        if not visuals:
            raise ValueError("preview requires a main visual track")
        if len({item.track for item in visuals}) != 1:
            raise ValueError("preview renderer currently supports one visual track")
        cursor = 0
        for item in visuals:
            if item.start_us != cursor:
                raise ValueError("main visual track must be gapless and start at zero")
            cursor += item.duration_us
        if cursor != plan.duration_us:
            raise ValueError("main visual track must cover the complete preview")
        if len(audio) != 1:
            raise ValueError("preview renderer requires exactly one music track")
        if audio[0].start_us + audio[0].duration_us > plan.duration_us:
            raise ValueError("music exceeds preview duration")

    def _command(self, plan: TimelinePlan, visuals: list[Segment], audio: list[Segment],
                 titles: Path, output: Path) -> list[str]:
        command = [str(self.ffmpeg), "-hide_banner", "-loglevel", "warning", "-nostdin", "-y"]
        for item in visuals:
            if item.kind == "picture":
                command.extend(["-loop", "1", "-t", _seconds(item.duration_us), "-i", str(item.source_path)])
            else:
                command.extend(["-ss", _seconds(item.source_start_us), "-t", _seconds(item.duration_us),
                                "-i", str(item.source_path)])
        music = audio[0]
        command.extend(["-ss", _seconds(music.source_start_us), "-t", _seconds(music.duration_us),
                        "-i", str(music.source_path)])

        filters: list[str] = []
        for index, item in enumerate(visuals):
            common = (
                f"scale={plan.width}:{plan.height}:force_original_aspect_ratio=increase,"
                f"crop={plan.width}:{plan.height},setsar=1,fps={plan.fps},"
                "eq=contrast=1.035:saturation=1.06:brightness=-0.005,format=yuv420p"
            )
            if item.kind == "picture":
                direction = "iw/2-(iw/zoom/2)" if index % 2 == 0 else "iw-iw/zoom"
                motion = (
                    f"zoompan=z='min(zoom+0.00035,1.075)':x='{direction}':"
                    f"y='ih/2-(ih/zoom/2)':d=1:s={plan.width}x{plan.height}:fps={plan.fps},"
                )
                filters.append(f"[{index}:v]{common},{motion}trim=duration={_seconds(item.duration_us)},setpts=PTS-STARTPTS[v{index}]")
            else:
                filters.append(f"[{index}:v]{common},trim=duration={_seconds(item.duration_us)},setpts=PTS-STARTPTS[v{index}]")
        joined = "".join(f"[v{index}]" for index in range(len(visuals)))
        filters.append(f"{joined}concat=n={len(visuals)}:v=1:a=0[sequence]")
        subtitle_filter = f"subtitles=filename={_filter_path(titles)}:fontsdir={_filter_path(Path('C:/Windows/Fonts'))}"
        fade_out = max(0.0, plan.duration_us / 1_000_000 - 0.65)
        filters.append(
            f"[sequence]vignette=PI/7:eval=frame,"
            f"drawbox=x=0:y=0:w=iw:h={max(24, plan.height // 24)}:color=black@0.96:t=fill,"
            f"drawbox=x=0:y=ih-{max(24, plan.height // 24)}:w=iw:h={max(24, plan.height // 24)}:color=black@0.96:t=fill,"
            f"{subtitle_filter},fade=t=in:st=0:d=0.25,"
            f"fade=t=out:st={fade_out:.3f}:d=0.65[vout]"
        )
        audio_index = len(visuals)
        delay_ms = audio[0].start_us // 1000
        audio_duration = plan.duration_us / 1_000_000
        fade_audio = max(0.0, audio_duration - 1.0)
        filters.append(
            f"[{audio_index}:a]atrim=duration={_seconds(audio[0].duration_us)},asetpts=PTS-STARTPTS,"
            f"adelay={delay_ms}:all=1,apad=pad_dur={audio_duration:.6f},atrim=duration={audio_duration:.6f},"
            f"loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=in:st=0:d=0.45,"
            f"afade=t=out:st={fade_audio:.3f}:d=1.0[aout]"
        )
        command.extend([
            "-filter_complex", ";".join(filters), "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
            "-metadata", "comment=PRIVATE REVIEW - rendered by MTCapcut PreviewRenderEngine v1",
            "-t", _seconds(plan.duration_us), str(output),
        ])
        return command

    @staticmethod
    def _ass_document(plan: TimelinePlan, text: list[Segment]) -> str:
        font_size = max(28, round(plan.height * 0.052))
        margin = max(36, round(plan.height * 0.065))
        lines = [
            "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {plan.width}",
            f"PlayResY: {plan.height}", "ScaledBorderAndShadow: yes", "WrapStyle: 2", "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
            "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding",
            f"Style: Hero,Tahoma,{round(font_size * 1.42)},&H00FFFFFF,&H000000FF,&H00121418,&H96000000,-1,0,0,0,100,100,1,0,1,4,2,5,{margin},{margin},{margin},1",
            f"Style: Role,Tahoma,{round(font_size * 0.78)},&H0033CCFF,&H000000FF,&H00121418,&H96000000,-1,0,0,0,100,100,1,0,1,3,1,5,{margin},{margin},{margin},1",
            f"Style: Statement,Tahoma,{font_size},&H00FFFFFF,&H000000FF,&H00121418,&H96000000,-1,0,0,0,100,100,1,0,1,3,2,1,{margin * 2},{margin},{margin * 2},1",
            f"Style: Preview,Tahoma,{max(18, font_size // 3)},&H80FFFFFF,&H000000FF,&H40000000,&H00000000,0,0,0,0,100,100,1,0,1,1,0,9,{margin},{margin},{margin // 2},1",
            "", "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        ]
        for index, item in enumerate(text):
            start = _ass_time(item.start_us)
            end = _ass_time(item.start_us + item.duration_us)
            if index == 0:
                style = "Hero"
                effect = r"{\fscx88\fscy88\t(0,420,\fscx100\fscy100)\fad(160,260)}"
            elif index == 1:
                style = "Role"
                effect = r"{\fscx94\fscy94\t(0,360,\fscx100\fscy100)\fad(180,280)}"
            else:
                style = "Statement"
                effect = r"{\fscx92\fscy92\t(0,320,\fscx100\fscy100)\fad(150,240)}"
                bar_x = margin + 8
                bar_y = plan.height - margin * 3
                lines.append(
                    f"Dialogue: 0,{start},{end},Statement,,0,0,0,,"
                    f"{{\\an7\\pos({bar_x},{bar_y})\\p1\\c&H0033CCFF&\\bord0\\shad0\\fad(150,240)}}"
                    "m 0 0 l 10 0 l 10 90 l 0 90"
                )
            lines.append(f"Dialogue: 1,{start},{end},{style},,0,0,0,,{effect}{_ass_text(item.text or '')}")
        lines.append(
            f"Dialogue: 2,0:00:00.00,{_ass_time(plan.duration_us)},Preview,,0,0,0,,PRIVATE PREVIEW • MTCAPCUT ENGINE"
        )
        return "\n".join(lines) + "\n"

