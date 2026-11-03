"""Small CLI for the first usable Asset Understanding Map slice."""

import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
import sys

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
    assets = commands.add_parser("assets", help="List registered assets and current hashes")
    assets.add_argument("project_id")
    timeline = commands.add_parser("timeline", help="Show observations for one asset")
    timeline.add_argument("project_id")
    timeline.add_argument("asset_id")
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
        elif args.command == "assets":
            print(json.dumps(understanding.list_assets(), ensure_ascii=False, indent=2))
        elif args.command == "timeline":
            print(json.dumps(understanding.current_asset_timeline(args.asset_id), ensure_ascii=False, indent=2))
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
        else:
            output = create_draft(load_plan(args.plan), args.output_root, args.draft_name)
            print(json.dumps({"draft": str(output), "compatibility": "unverified-in-capcut"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
