"""Small CLI for the first usable Asset Understanding Map slice."""

import argparse
from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from uuid import uuid4

from .assets import InputAsset, inspect_asset, inspect_bundle
from .config import load_config
from .map import UnderstandingMap
from .timeline import load_plan
from .capcut_adapter import create_draft
from .doctor import diagnose
from .shot_map_service import ShotMapService
from .preview_renderer import PreviewRenderEngine
from .ai_provider import create_provider
from .studio_orchestrator import AutonomousStudioOrchestrator
from .studio_approval import authorize_private_preview
from .professional_finishing import ProfessionalFinishingEngine, ProfessionalFinishingPlan, TextFinish
from .data_policy import DataPolicyGate
from .media_cognition import MediaCognitionEngine
from .perception import EvidenceArtifact, hash_file
from .perception import extract_audio
from .local_ear import FasterWhisperEar
from .take_review import suggest_for_asset


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="mtcapcut")
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().parent.parent / "config.toml")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Report local dependency and installation health")
    ingest = commands.add_parser("ingest", help="Inspect and register one asset")
    ingest.add_argument("project_id")
    ingest.add_argument("file", type=Path)
    ingest.add_argument("--role", required=True)
    ingest.add_argument("--rights-status", default="unknown")
    bundle = commands.add_parser("ingest-bundle", help="Inspect and register a JSON asset bundle atomically")
    bundle.add_argument("project_id")
    bundle.add_argument("manifest", type=Path)
    directory = commands.add_parser("ingest-directory", help="Inspect and register supported files in a directory")
    directory.add_argument("project_id")
    directory.add_argument("directory", type=Path)
    directory.add_argument("--role", required=True)
    directory.add_argument("--source", default="user")
    directory.add_argument("--rights-status", default="unknown")
    assets = commands.add_parser("assets", help="List registered assets and current hashes")
    assets.add_argument("project_id")
    timeline = commands.add_parser("timeline", help="Show observations for one asset")
    timeline.add_argument("project_id")
    timeline.add_argument("asset_id")
    transcribe = commands.add_parser("transcribe-asset", help="Store local word-level ASR for one audio or clip asset")
    transcribe.add_argument("project_id")
    transcribe.add_argument("asset_id")
    take_review = commands.add_parser("review-takes", help="Suggest review-only pause/repetition ranges from SSOT words")
    take_review.add_argument("project_id")
    take_review.add_argument("asset_id")
    shots = commands.add_parser("analyze-shots", help="Detect shot candidates and register sampled frames")
    shots.add_argument("project_id")
    shots.add_argument("asset_id")
    policy = commands.add_parser("set-ai-policy", help="Append an asset data classification and AI decision")
    policy.add_argument("project_id")
    policy.add_argument("asset_id")
    policy.add_argument("classification", choices=("public_source", "internal_test", "confidential", "restricted"))
    policy.add_argument("--allow-external", action="store_true")
    policy.add_argument("--actor", required=True)
    policy.add_argument("--reason", required=True)
    show_policy = commands.add_parser("show-ai-policy", help="Show the current append-only AI policy for an asset")
    show_policy.add_argument("project_id")
    show_policy.add_argument("asset_id")
    cognition = commands.add_parser(
        "cognize-pictures", help="Use the configured vision AI to understand registered pictures",
    )
    cognition.add_argument("project_id")
    cognition.add_argument("--role")
    render = commands.add_parser("render-preview", help="Render a review MP4 from a validated Timeline Plan")
    render.add_argument("project_id")
    render.add_argument("plan", type=Path)
    render.add_argument("output", type=Path)
    studio = commands.add_parser("run-studio", help="Run the autonomous evidence-grounded Studio Council")
    studio.add_argument("project_id")
    studio.add_argument("output", type=Path)
    studio.add_argument("--brief-asset", required=True)
    studio.add_argument("--restrictions-asset", required=True)
    show_studio = commands.add_parser("show-studio-run", help="Show one append-only Studio Council run")
    show_studio.add_argument("project_id")
    show_studio.add_argument("run_id")
    review_studio = commands.add_parser("review-studio-run", help="Append a human approval or rejection")
    review_studio.add_argument("project_id")
    review_studio.add_argument("run_id")
    review_studio.add_argument("decision", choices=("approve", "reject"))
    review_studio.add_argument("--scope", choices=("private_preview", "publication"), required=True)
    review_studio.add_argument("--actor", required=True)
    review_studio.add_argument("--reason", required=True)
    render_studio = commands.add_parser("render-studio-preview", help="Render an authorized autonomous candidate")
    render_studio.add_argument("project_id")
    render_studio.add_argument("candidate", type=Path)
    render_studio.add_argument("output", type=Path)
    draft = commands.add_parser("create-draft", help="Create a new pyCapCut draft under a marked sandbox")
    draft.add_argument("project_id")
    draft.add_argument("plan", type=Path)
    draft.add_argument("output_root", type=Path)
    draft.add_argument("draft_name")
    professional = commands.add_parser(
        "create-professional-draft", help="Design finishing with the Studio engine and create a pyCapCut draft",
    )
    professional.add_argument("project_id")
    professional.add_argument("candidate", type=Path)
    professional.add_argument("output_root", type=Path)
    professional.add_argument("draft_name")
    professional.add_argument("finishing_manifest", type=Path)
    args = parser.parse_args()
    config = load_config(args.config, validate_paths=args.command != "doctor")
    if args.command == "doctor":
        report = diagnose(config)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        raise SystemExit(0 if report["ok"] else 1)
    if not args.project_id or Path(args.project_id).name != args.project_id or args.project_id in {".", ".."}:
        parser.error("project_id must be a single safe directory name")
    database = config.workspace / args.project_id / "understanding.sqlite3"
    with UnderstandingMap(database) as understanding:
        if args.command == "ingest":
            asset = inspect_asset(InputAsset(args.file, args.role, rights_status=args.rights_status), config)
            result = understanding.register_bundle([asset])[0]
            if asset["kind"] == "text" and not understanding.current_asset_timeline(result["asset_id"]):
                understanding.add_observations(result["asset_id"], [{"modality": "text",
                    "text": Path(asset["path"]).read_text(encoding="utf-8-sig"),
                    "producer": "text-reader", "producer_version": "1"}])
            print(json.dumps({**result, "kind": asset["kind"], "role": asset["role"]}, ensure_ascii=False))
        elif args.command == "ingest-bundle":
            manifest = args.manifest.resolve(strict=True)
            document = json.loads(manifest.read_text(encoding="utf-8-sig"))
            if not isinstance(document, list) or not document:
                parser.error("manifest must be a nonempty JSON array")
            inputs = [InputAsset(path=(manifest.parent / row["path"]), role=row["role"],
                                 source=row.get("source", "user"),
                                 rights_status=row.get("rights_status", "unknown")) for row in document]
            inspected = inspect_bundle(inputs, config)
            results = understanding.register_bundle(inspected)
            for asset, result in zip(inspected, results):
                if asset["kind"] == "text" and not understanding.current_asset_timeline(result["asset_id"]):
                    understanding.add_observations(result["asset_id"], [{"modality": "text",
                        "text": Path(asset["path"]).read_text(encoding="utf-8-sig"),
                        "producer": "text-reader", "producer_version": "1"}])
            print(json.dumps(results, ensure_ascii=False, indent=2))
        elif args.command == "ingest-directory":
            root = args.directory.resolve(strict=True)
            if not root.is_dir():
                parser.error("directory must identify a directory")
            inputs = [InputAsset(path=item, role=args.role, source=args.source,
                                 rights_status=args.rights_status)
                      for item in sorted(root.iterdir()) if item.is_file()]
            inspected = inspect_bundle(inputs, config)
            results = understanding.register_bundle(inspected)
            print(json.dumps([{**result, "path": asset["path"], "kind": asset["kind"]}
                              for asset, result in zip(inspected, results)], ensure_ascii=False, indent=2))
        elif args.command == "assets":
            print(json.dumps(understanding.list_assets(), ensure_ascii=False, indent=2))
        elif args.command == "timeline":
            print(json.dumps(understanding.current_asset_timeline(args.asset_id), ensure_ascii=False, indent=2))
        elif args.command == "transcribe-asset":
            asset = understanding.get_asset(args.asset_id)
            if asset["kind"] not in {"audio", "clip"}:
                raise ValueError("transcribe-asset requires an audio or clip asset")
            if not config.local_ear.enabled:
                raise ValueError("local_ear.enabled must be true in central config")
            ear = FasterWhisperEar(config.local_ear)
            existing = [item for item in understanding.current_asset_timeline(args.asset_id)
                        if item["modality"] == "speech_word"]
            producer = ear.producer
            if existing and any(item["producer"] != producer for item in existing):
                raise ValueError("current asset has word evidence from another model; review before re-transcription")
            if existing:
                result = {"asset_id": args.asset_id, "status": "cache_hit",
                          "word_observation_count": len(existing)}
            else:
                raw_duration = asset["technical"].get("format", {}).get("duration")
                try:
                    duration_us = round(float(raw_duration) * 1_000_000)
                except (TypeError, ValueError) as error:
                    raise ValueError("asset duration is required for word-level transcription") from error
                if duration_us <= 0:
                    raise ValueError("asset duration must be positive")
                with TemporaryDirectory(prefix="mtcapcut-asr-") as folder:
                    artifact = extract_audio(config.ffmpeg, Path(asset["path"]),
                                             Path(folder) / "speech.wav", end_us=duration_us)
                    ids = ear.transcribe_and_store(understanding, args.asset_id, artifact)
                result = {"asset_id": args.asset_id, "status": "analyzed",
                          "observation_count": len(ids),
                          "word_observation_count": sum(item["modality"] == "speech_word"
                              for item in understanding.current_asset_timeline(args.asset_id))}
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.command == "review-takes":
            understanding.get_asset(args.asset_id)
            observations = understanding.current_asset_timeline(args.asset_id)
            suggestions = suggest_for_asset(understanding, args.asset_id)
            word_count = sum(item["modality"] == "speech_word" for item in observations)
            print(json.dumps({"asset_id": args.asset_id,
                "status": "review_ready" if word_count else "no_word_transcript",
                "word_observation_count": word_count,
                "review_required": True, "suggestions": [asdict(item) for item in suggestions]},
                ensure_ascii=False, indent=2))
        elif args.command == "analyze-shots":
            result = ShotMapService(
                config, understanding, config.workspace / args.project_id,
            ).analyze(args.asset_id)
            print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        elif args.command == "set-ai-policy":
            policy_id = understanding.set_asset_ai_policy(
                args.asset_id, args.classification, args.allow_external, args.actor, args.reason,
            )
            print(json.dumps({"policy_id": policy_id, "asset_id": args.asset_id,
                              "current": understanding.current_asset_ai_policy(args.asset_id)},
                             ensure_ascii=False, indent=2))
        elif args.command == "show-ai-policy":
            print(json.dumps({"asset_id": args.asset_id,
                              "current": understanding.current_asset_ai_policy(args.asset_id)},
                             ensure_ascii=False, indent=2))
        elif args.command == "cognize-pictures":
            if not config.ai.default_provider:
                raise ValueError("ai.default_provider is required for picture cognition")
            settings = config.ai.providers[config.ai.default_provider]
            if config.ai.vision_model:
                settings = replace(settings, model=config.ai.vision_model)
            engine = MediaCognitionEngine(
                create_provider(settings), policy_gate=DataPolicyGate(config, understanding),
                max_evidence_bytes=config.data_policy.max_evidence_bytes,
            )
            results = []
            for summary in understanding.list_assets():
                if summary["kind"] != "picture" or (args.role and summary["role"] != args.role):
                    continue
                existing = [item for item in understanding.current_asset_timeline(summary["asset_id"])
                            if item["modality"] in {"vision", "ocr"}
                            and item["producer"].startswith("media-cognition:")]
                if existing:
                    results.append({"asset_id": summary["asset_id"], "status": "cache_hit",
                                    "observation_ids": [item["observation_id"] for item in existing]})
                    continue
                path = Path(summary["path"]).resolve(strict=True)
                artifact = EvidenceArtifact("frame", 0, 0, path, hash_file(path))
                ids = engine.analyze_and_store(understanding, summary["asset_id"], artifact)
                results.append({"asset_id": summary["asset_id"], "status": "analyzed",
                                "observation_ids": ids})
            if not results:
                raise ValueError("no registered pictures matched the requested role")
            print(json.dumps(results, ensure_ascii=False, indent=2))
        elif args.command == "render-preview":
            preview_document = json.loads(args.plan.resolve(strict=True).read_text(encoding="utf-8-sig"))
            if preview_document.get("authorship") == "autonomous_studio":
                raise PermissionError("autonomous candidates must use render-studio-preview")
            result = PreviewRenderEngine(config.ffmpeg).render(load_plan(args.plan), args.output)
            print(json.dumps(asdict(result), ensure_ascii=False, indent=2, default=str))
        elif args.command == "run-studio":
            if not config.ai.default_provider:
                raise ValueError("ai.default_provider is required for run-studio")
            settings = config.ai.providers[config.ai.default_provider]
            if config.ai.studio_model:
                settings = replace(settings, model=config.ai.studio_model)
            provider = create_provider(settings)
            result = AutonomousStudioOrchestrator(
                config, understanding, provider,
                authority_asset_ids={args.brief_asset, args.restrictions_asset},
            ).run(args.output)
            print(json.dumps(asdict(result), ensure_ascii=False, indent=2, default=str))
        elif args.command == "show-studio-run":
            print(json.dumps(understanding.get_studio_run(args.run_id), ensure_ascii=False, indent=2))
        elif args.command == "review-studio-run":
            approval_id = understanding.review_studio_run(
                args.run_id, args.scope, args.decision, args.actor, args.reason,
            )
            print(json.dumps({"approval_id": approval_id, "run_id": args.run_id,
                              "scope": args.scope, "current":
                              understanding.current_studio_approval(args.run_id, args.scope)},
                             ensure_ascii=False, indent=2))
        elif args.command == "render-studio-preview":
            authorize_private_preview(understanding, args.candidate)
            result = PreviewRenderEngine(config.ffmpeg).render(load_plan(args.candidate), args.output)
            print(json.dumps(asdict(result), ensure_ascii=False, indent=2, default=str))
        elif args.command == "create-professional-draft":
            candidate = authorize_private_preview(understanding, args.candidate)
            if not config.ai.default_provider:
                raise ValueError("ai.default_provider is required for professional finishing")
            settings = config.ai.providers[config.ai.default_provider]
            if config.ai.studio_model:
                settings = replace(settings, model=config.ai.studio_model)
            finishing_engine = ProfessionalFinishingEngine(create_provider(settings))
            visual_count = sum(item["kind"] in {"picture", "video"} for item in candidate["segments"])
            if visual_count > 12:
                chunks = []
                for offset in range(0, max(item["start_us"] for item in candidate["segments"]
                                           if item["kind"] in {"picture", "video"}) + 1, 30_000_000):
                    scoped = {**candidate, "segments": [item for item in candidate["segments"]
                              if offset <= item["start_us"] < offset + 30_000_000
                              and item["kind"] in {"picture", "video"}]}
                    if scoped["segments"]:
                        chunks.append(finishing_engine.design(scoped))
                finishing = ProfessionalFinishingPlan(
                    "mtcapcut.finishing.v1", "autonomous_studio",
                    tuple(item for chunk in chunks for item in chunk.visual_finishes),
                    tuple(TextFinish(item["segment_id"], "none", "none",
                                     "CapCut 9.7 local-safe text treatment")
                          for item in candidate["segments"] if item["kind"] == "text"),
                    " | ".join(chunk.creative_rationale for chunk in chunks),
                )
            else:
                finishing = finishing_engine.design(candidate)
            manifest = args.finishing_manifest.resolve()
            if manifest.exists():
                raise FileExistsError(manifest)
            manifest.parent.mkdir(parents=True, exist_ok=True)
            staged_manifest = manifest.with_name(f".{manifest.name}.{uuid4().hex}.tmp")
            try:
                with staged_manifest.open("x", encoding="utf-8") as stream:
                    json.dump(finishing.to_dict(), stream, ensure_ascii=False, indent=2)
                    stream.flush()
                    os.fsync(stream.fileno())
                output = create_draft(load_plan(args.candidate), args.output_root, args.draft_name, finishing)
                if manifest.exists():
                    raise FileExistsError(manifest)
                staged_manifest.rename(manifest)
            finally:
                staged_manifest.unlink(missing_ok=True)
            print(json.dumps({"draft":str(output), "finishing_manifest":str(manifest),
                              "authorship":finishing.authorship,
                              "compatibility":"unverified-in-capcut"}, ensure_ascii=False, indent=2))
        else:
            output = create_draft(load_plan(args.plan), args.output_root, args.draft_name)
            print(json.dumps({"draft": str(output), "compatibility": "unverified-in-capcut"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
