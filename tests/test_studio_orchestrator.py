from pathlib import Path
import json
import tempfile
import unittest

from mtcapcut.ai_provider import ChatResponse
from mtcapcut.config import AIProviderSettings, Config
from mtcapcut.map import UnderstandingMap
from mtcapcut.studio_orchestrator import AutonomousStudioOrchestrator


class ScriptedProvider:
    def __init__(self, invalid_asset=False, invalid_text=False, wrong_media_evidence=False,
                 unknown_evidence=False, visual_gap=False, long_text=False,
                 candidate_duration=1_000_000, brief_duration=(1_000_000, 1_000_000),
                 revised_duration=None):
        self.invalid_asset = invalid_asset
        self.invalid_text = invalid_text
        self.wrong_media_evidence = wrong_media_evidence
        self.unknown_evidence = unknown_evidence
        self.visual_gap = visual_gap
        self.long_text = long_text
        self.candidate_duration = candidate_duration
        self.brief_duration = brief_duration
        self.revised_duration = revised_duration
        self.requests = []
        self.settings = AIProviderSettings("local", "local_openai", "http://127.0.0.1:1/v1", "model", enabled=True)

    def complete(self, request):
        self.requests.append(request)
        system = request.messages[0].content
        payload = json.loads(request.messages[1].content)
        observations = payload.get("studio_input", {}).get("observations", [])
        if not observations:
            observations = payload.get("authority_observations", [])
        brief_evidence = next((item["observation_id"] for item in observations
                               if item.get("modality") == "text"), None)
        picture_evidence = next((item["observation_id"] for item in observations
                                 if item.get("asset_id") == "picture-1"), None)
        if "Brief Interpreter" in system:
            value = {"schema_version":"1","duration_min_us":self.brief_duration[0],
                     "duration_max_us":self.brief_duration[1],
                     "width":16,"height":9,"delivery_scope":"private_preview","audience":"test",
                     "tone":[],"story_beats":[],"required_messages":[],"required_asset_roles":[],
                     "required_asset_names":[],"forbidden_asset_names":[],"evidence":[brief_evidence]}
        elif "candidate-validator repair" in system:
            value = payload["invalid_candidate"]
            if not self.invalid_asset:
                value["segments"][1]["text"] = "บริการประชาชน"
            if self.revised_duration is not None:
                value["segments"][0]["duration_us"] = self.revised_duration
        elif "Clip Director" in system:
            recommendations = payload["validated_recommendations"]
            objections = [item["finding_id"] for row in recommendations for item in row["objections"]]
            value = {"creative_direction":"clear","premise":"service","audience_effect":"understanding",
                     "story_beats":["opening","proof"],
                     "accepted_recommendation_ids":[row["recommendation_id"] for row in recommendations],
                     "unresolved_objections":objections,"confidence":0.7,"risks":["fixture risk"]}
        elif "Lead Editor" in system:
            value = {"authorship":"autonomous_studio","width":1280,"height":720,"fps":30,
                     "segments":[{"segment_id":"s1","kind":"picture",
                        "start_us":250_000 if self.visual_gap else 0,"duration_us":self.candidate_duration,
                        "track":"main","asset_id":"missing" if self.invalid_asset else "picture-1",
                        "source_start_us":0,"rationale":"opening",
                        "evidence":["hallucinated-id" if self.unknown_evidence else
                                    (brief_evidence if self.wrong_media_evidence else picture_evidence)]},
                        {"segment_id":"t1","kind":"text","start_us":0,
                        "duration_us":2_000_000 if self.long_text else 500_000,
                        "track":"titles","text":"ข้อความแต่ง" if self.invalid_text else "บริการประชาชน","rationale":"brief message",
                        "evidence":[brief_evidence]}]}
        else:
            role = payload["output_schema"]["role"]
            value = {"role":role,"recommendation":f"{role} recommendation","confidence":0.7,
                     "evidence":[brief_evidence],"risks":["fixture risk"],
                     "alternatives":["fixture alternative"],"objections":[]}
        return ChatResponse("id", "model", json.dumps(value))


class StudioOrchestratorTests(unittest.TestCase):
    def _mapping(self, root):
        mapping = UnderstandingMap(root / "map.sqlite3")
        mapping.add_asset({"asset_id":"picture-1","path":str(root / "picture.jpg"),"kind":"picture",
            "role":"event_photo","source":"user","rights_status":"owned","content_hash":"p",
            "size_bytes":1,"technical":{}})
        mapping.add_asset({"asset_id":"brief-1","path":str(root / "brief.txt"),"kind":"text",
            "role":"brief","source":"user","rights_status":"owned","content_hash":"b",
            "size_bytes":1,"technical":{}})
        mapping.add_observations("picture-1", [{"modality":"vision","text":"a service event",
            "confidence":0.8,"producer":"eye","producer_version":"1"}])
        mapping.add_observations("brief-1", [{"modality":"text","text":"บริการประชาชน",
            "producer":"brief-reader","producer_version":"1"}])
        return mapping

    def test_complete_autonomous_run_writes_plan_and_ledger(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "picture.jpg").touch()
            (root / "brief.txt").touch()
            with self._mapping(root) as mapping:
                result = AutonomousStudioOrchestrator(
                    Config(root, root / "ffprobe.exe", root), mapping, ScriptedProvider(),
                ).run(root / "candidate.json")
                self.assertEqual(result.recommendation_count, 6)
                document = json.loads(result.output.read_text(encoding="utf-8"))
                self.assertEqual(document["authorship"], "autonomous_studio")
                self.assertEqual(mapping.get_studio_run(result.run_id)["status"], "candidate_ready")

    def test_output_write_failure_keeps_studio_run_failed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "picture.jpg").touch()
            (root / "brief.txt").touch()
            (root / "not-a-directory").write_text("occupied", encoding="utf-8")
            with self._mapping(root) as mapping:
                orchestrator = AutonomousStudioOrchestrator(
                    Config(root, root / "ffprobe.exe", root), mapping, ScriptedProvider())
                with self.assertRaises((FileExistsError, NotADirectoryError)):
                    orchestrator.run(root / "not-a-directory" / "candidate.json")
                status = mapping.connection.execute(
                    "SELECT status FROM studio_runs ORDER BY created_at DESC LIMIT 1").fetchone()[0]
                self.assertEqual(status, "failed")

    def test_invalid_asset_fails_run_and_writes_no_plan(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "picture.jpg").touch()
            (root / "brief.txt").touch()
            with self._mapping(root) as mapping:
                orchestrator = AutonomousStudioOrchestrator(
                    Config(root, root / "ffprobe.exe", root), mapping, ScriptedProvider(invalid_asset=True),
                )
                with self.assertRaises(ValueError):
                    orchestrator.run(root / "candidate.json")
                status = mapping.connection.execute("SELECT status FROM studio_runs").fetchone()[0]
                self.assertEqual(status, "failed")
                self.assertFalse((root / "candidate.json").exists())

    def test_unsupported_text_is_removed_by_fact_gate_not_rewritten(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "picture.jpg").touch()
            (root / "brief.txt").touch()
            with self._mapping(root) as mapping:
                result = AutonomousStudioOrchestrator(
                    Config(root, root / "ffprobe.exe", root), mapping,
                    ScriptedProvider(invalid_text=True),
                ).run(root / "candidate.json")
                candidate = json.loads(result.output.read_text(encoding="utf-8"))
                self.assertEqual(len(candidate["segments"]), 1)
                self.assertEqual(candidate["rejected_segments"][0]["text"], "ข้อความแต่ง")
                self.assertIn("not verbatim", candidate["rejected_segments"][0]["rejection_reason"])

    def test_multiline_text_is_supported_when_every_line_is_verbatim(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "picture.jpg").touch()
            (root / "brief.txt").touch()
            provider = ScriptedProvider()
            original_complete = provider.complete
            def multiline(request):
                response = original_complete(request)
                if "Lead Editor" in request.messages[0].content:
                    value = json.loads(response.text)
                    value["segments"][1]["text"] = "บริการ\nประชาชน"
                    return ChatResponse("id", "model", json.dumps(value, ensure_ascii=False))
                return response
            provider.complete = multiline
            with self._mapping(root) as mapping:
                # Replace authority text so both individual lines are verbatim-supported.
                mapping.add_observations("brief-1", [{"modality":"text","text":"บริการ ประชาชน",
                    "producer":"brief-reader","producer_version":"1"}])
                result = AutonomousStudioOrchestrator(
                    Config(root, root / "ffprobe.exe", root), mapping, provider,
                ).run(root / "candidate.json")
                candidate = json.loads(result.output.read_text(encoding="utf-8"))
                self.assertEqual(candidate["segments"][1]["text"], "บริการ\nประชาชน")

    def test_temporal_binder_attaches_same_asset_evidence_transparently(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "picture.jpg").touch()
            (root / "brief.txt").touch()
            with self._mapping(root) as mapping:
                result = AutonomousStudioOrchestrator(
                    Config(root, root / "ffprobe.exe", root), mapping,
                    ScriptedProvider(wrong_media_evidence=True),
                ).run(root / "candidate.json")
                visual = json.loads(result.output.read_text(encoding="utf-8"))["segments"][0]
                self.assertEqual(len(visual["evidence_auto_attached"]), 1)
                self.assertIn(visual["evidence_auto_attached"][0], visual["evidence"])

    def test_unknown_evidence_is_rejected_and_rebound_transparently(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "picture.jpg").touch()
            (root / "brief.txt").touch()
            with self._mapping(root) as mapping:
                result = AutonomousStudioOrchestrator(
                    Config(root, root / "ffprobe.exe", root), mapping,
                    ScriptedProvider(unknown_evidence=True),
                ).run(root / "candidate.json")
                visual = json.loads(result.output.read_text(encoding="utf-8"))["segments"][0]
                self.assertEqual(visual["evidence_rejected_unknown"], ["hallucinated-id"])
                self.assertEqual(len(visual["evidence_auto_attached"]), 1)

    def test_main_visual_timing_is_packed_with_provider_time_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "picture.jpg").touch()
            (root / "brief.txt").touch()
            with self._mapping(root) as mapping:
                result = AutonomousStudioOrchestrator(
                    Config(root, root / "ffprobe.exe", root), mapping,
                    ScriptedProvider(visual_gap=True),
                ).run(root / "candidate.json")
                visual = json.loads(result.output.read_text(encoding="utf-8"))["segments"][0]
                self.assertEqual(visual["start_us"], 0)
                self.assertEqual(visual["start_us_provider"], 250_000)
                self.assertTrue(visual["timing_auto_normalized"])

    def test_nonvisual_segment_is_trimmed_to_main_visual_duration(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "picture.jpg").touch()
            (root / "brief.txt").touch()
            with self._mapping(root) as mapping:
                result = AutonomousStudioOrchestrator(
                    Config(root, root / "ffprobe.exe", root), mapping,
                    ScriptedProvider(long_text=True),
                ).run(root / "candidate.json")
                title = json.loads(result.output.read_text(encoding="utf-8"))["segments"][1]
                self.assertEqual(title["duration_us"], 1_000_000)
                self.assertEqual(title["duration_us_provider"], 2_000_000)

    def test_brief_noncompliance_is_revised_by_lead_editor_engine(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "picture.jpg").touch()
            (root / "brief.txt").touch()
            provider = ScriptedProvider(candidate_duration=45_000_000,
                                        brief_duration=(30_000_000, 35_000_000),
                                        revised_duration=32_000_000)
            with self._mapping(root) as mapping:
                result = AutonomousStudioOrchestrator(
                    Config(root, root / "ffprobe.exe", root), mapping, provider,
                ).run(root / "candidate.json")
                candidate = json.loads(result.output.read_text(encoding="utf-8"))
                self.assertEqual(candidate["segments"][0]["duration_us"], 32_000_000)
                self.assertEqual(candidate["brief_compliance"]["status"], "pass")
                self.assertFalse(candidate["gates"]["publication_eligible"])
                self.assertEqual(len(mapping.get_studio_run(result.run_id)["brief_interpretations"]), 1)
                repair_requests = [request for request in provider.requests
                                   if "candidate-validator repair" in request.messages[0].content]
                repair_payload = json.loads(repair_requests[0].messages[1].content)
                self.assertEqual(repair_payload["cited_evidence_and_assets"]["project_brief"]
                                 ["duration_max_us"], 35_000_000)

    def test_exhausted_brief_revisions_are_rejected_without_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "picture.jpg").touch()
            (root / "brief.txt").touch()
            provider = ScriptedProvider(candidate_duration=45_000_000,
                                        brief_duration=(30_000_000, 35_000_000))
            with self._mapping(root) as mapping:
                result = AutonomousStudioOrchestrator(
                    Config(root, root / "ffprobe.exe", root), mapping, provider,
                ).run(root / "candidate.json")
                self.assertEqual(result.status, "candidate_rejected")
                self.assertEqual(mapping.get_studio_run(result.run_id)["status"], "candidate_rejected")
                self.assertFalse(result.output.exists())


if __name__ == "__main__":
    unittest.main()
