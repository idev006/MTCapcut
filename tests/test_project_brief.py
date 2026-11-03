import json
import unittest

from mtcapcut.ai_provider import AIProviderSettings, ChatResponse
from mtcapcut.project_brief import BriefComplianceValidator, BriefInterpreterEngine, ProjectBrief
from mtcapcut.studio_snapshot import StudioInputSnapshot


class FakeProvider:
    def __init__(self, response):
        self.response = response
        self.requests = []
        self.settings = AIProviderSettings("local", "local_openai", "http://127.0.0.1:1/v1", "model", enabled=True)

    def complete(self, request):
        self.requests.append(request)
        return ChatResponse("id", "model", self.response)


def brief():
    return ProjectBrief(
        schema_version="1", duration_min_us=30_000_000, duration_max_us=35_000_000,
        width=1920, height=1080, delivery_scope="private_preview",
        audience="ประชาชน", tone=("สุภาพ", "หนักแน่น"),
        story_beats=("รับมอบหน้าที่", "ลงพื้นที่"), required_messages=("ใส่ใจประชาชน",),
        required_asset_roles=("music",), required_asset_names=("โป้ง - หัวใจไม่เคยหยุดทำ1.mp3",),
        forbidden_asset_names=("โป้ง - ทำให้เห็น 2.mp3",), evidence=("brief-o1", "rule-o1"),
    )


class ProjectBriefTests(unittest.TestCase):
    def test_interpreter_requires_known_authority_evidence(self):
        value = brief().to_dict() | {"evidence": ["unknown"]}
        provider = FakeProvider(json.dumps(value, ensure_ascii=False))
        snapshot = StudioInputSnapshot({"assets": [], "observations": [{
            "observation_id": "brief-o1", "asset_id": "brief", "modality": "text", "text": "brief"
        }], "authority_rules": {}}, "hash")
        with self.assertRaises(ValueError):
            BriefInterpreterEngine(provider).interpret(snapshot)

    def test_45_seconds_fails_30_to_35_second_brief(self):
        candidate = {"width": 1920, "height": 1080, "segments": [
            {"kind": "picture", "track": "main", "start_us": 0, "duration_us": 45_000_000,
             "asset_id": "picture"}
        ]}
        findings = BriefComplianceValidator().validate(candidate, brief(), {})
        self.assertIn("duration_out_of_range", {item.finding_id for item in findings})

    def test_32_seconds_and_required_music_pass(self):
        candidate = {"width": 1920, "height": 1080, "segments": [
            {"kind": "picture", "track": "main", "start_us": 0, "duration_us": 32_000_000,
             "asset_id": "picture"},
            {"kind": "audio", "track": "music", "start_us": 0, "duration_us": 32_000_000,
             "asset_id": "music-ok"},
            {"kind": "text", "track": "titles", "start_us": 0, "duration_us": 2_000_000,
             "asset_id": None, "text": "ใส่ใจประชาชน"},
        ]}
        catalog = {"music-ok": {"role": "music", "path": "D:/x/โป้ง - หัวใจไม่เคยหยุดทำ1.mp3"}}
        findings = BriefComplianceValidator().validate(candidate, brief(), catalog)
        self.assertEqual(findings, ())

    def test_aspect_and_forbidden_music_are_rejected(self):
        candidate = {"width": 1080, "height": 1920, "segments": [
            {"kind": "picture", "track": "main", "start_us": 0, "duration_us": 32_000_000,
             "asset_id": "picture"},
            {"kind": "audio", "track": "music", "start_us": 0, "duration_us": 32_000_000,
             "asset_id": "bad"},
        ]}
        catalog = {"bad": {"role": "music", "path": "D:/x/โป้ง - ทำให้เห็น 2.mp3"}}
        codes = {item.finding_id for item in BriefComplianceValidator().validate(candidate, brief(), catalog)}
        self.assertEqual(codes, {"aspect_ratio_mismatch", "required_asset_missing",
                                 "forbidden_asset_used", "required_message_missing"})

    def test_private_delivery_scope_blocks_publication(self):
        self.assertFalse(brief().publication_allowed)

    def test_required_copy_allows_visual_pipe_separators_without_changing_words(self):
        candidate = {"width":1920,"height":1080,"segments":[
            {"kind":"picture","track":"main","start_us":0,"duration_us":32_000_000,"asset_id":"p"},
            {"kind":"audio","track":"music","start_us":0,"duration_us":32_000_000,"asset_id":"m"},
            {"kind":"text","track":"titles","start_us":0,"duration_us":3_000_000,
             "text":"ใส่ใจ  |  ประชาชน"},
        ]}
        custom = ProjectBrief(**{**brief().__dict__, "required_messages":("ใส่ใจ ประชาชน",)})
        catalog = {"m":{"role":"music","path":"โป้ง - หัวใจไม่เคยหยุดทำ1.mp3"}}
        self.assertEqual(BriefComplianceValidator().validate(candidate, custom, catalog), ())


if __name__ == "__main__":
    unittest.main()
