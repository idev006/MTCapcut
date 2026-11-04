import json
import unittest

from mtcapcut.ai_provider import AIProviderSettings, ChatResponse
from mtcapcut.studio_contracts import StudioSynthesis
from mtcapcut.studio_roles import StudioRoleEngine
from mtcapcut.studio_snapshot import StudioInputSnapshot


class FakeProvider:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []
        self.settings = AIProviderSettings("local", "local_openai", "http://127.0.0.1:1/v1", "model", enabled=True)

    def complete(self, request):
        self.requests.append(request)
        return ChatResponse("id", "model", next(self.responses))


class StudioRoleTests(unittest.TestCase):
    def test_long_timeline_joins_provider_sequences_and_user_locked_media(self):
        def sequence(chunk_index):
            return {"authorship": "autonomous_studio", "width": 1920, "height": 1080,
                    "fps": 30, "segments": [
                        {"segment_id": f"shot-{index}", "kind": "video",
                         "start_us": index * 7_500_000, "duration_us": 7_500_000,
                         "track": "main", "asset_id": "clip",
                         "source_start_us": (chunk_index * 4 + index) * 7_500_000,
                         "text": None, "rationale": "observed visual", "evidence": ["visual-proof"]}
                        for index in range(4)]}
        provider = FakeProvider([json.dumps(sequence(index)) for index in range(3)])
        snapshot = StudioInputSnapshot({
            "assets": [{"asset_id": "clip", "kind": "clip", "duration_us": 90_000_000},
                       {"asset_id": "song", "kind": "audio", "duration_us": 95_000_000}],
            "observations": [{"observation_id": "visual-proof", "asset_id": "clip",
                              "modality": "vision", "text": "ceremony"},
                             {"observation_id": "music-proof", "asset_id": "song",
                              "modality": "music", "text": "music"},
                             {"observation_id": "brief-proof", "asset_id": "brief",
                              "modality": "text", "text": "Required title"}],
            "project_brief": {"duration_min_us": 90_000_000,
                              "duration_max_us": 90_000_000,
                              "story_beats": ["opening", "event", "resolution"],
                              "required_messages": ["Required title"],
                              "width": 1920, "height": 1080},
        }, "hash")
        synthesis = StudioSynthesis("direction", "premise", "effect",
                                    ("opening", "event", "resolution"), (), (), 0.5, ("risk",))
        result = StudioRoleEngine(provider).create_long_timeline(snapshot, synthesis, (), "song")
        visuals = [item for item in result["segments"] if item["track"] == "main"]
        self.assertEqual(len(provider.requests), 3)
        self.assertEqual(len(visuals), 12)
        self.assertEqual([visuals[index]["start_us"] for index in (0, 4, 8)],
                         [0, 30_000_000, 60_000_000])
        self.assertEqual(visuals[-1]["start_us"] + visuals[-1]["duration_us"], 90_000_000)
        self.assertEqual(len({item["segment_id"] for item in visuals}), 12)
        self.assertEqual([item["asset_id"] for item in result["segments"]
                          if item["kind"] == "audio"], ["song"])
        self.assertEqual([item["text"] for item in result["segments"]
                          if item["kind"] == "text"], ["Required title"])

    def test_long_timeline_rejects_repeated_source_ranges(self):
        repeated = {"authorship": "autonomous_studio", "width": 1920, "height": 1080,
                    "fps": 30, "segments": [
                        {"segment_id": f"shot-{index}", "kind": "video",
                         "start_us": index * 7_500_000, "duration_us": 7_500_000,
                         "track": "main", "asset_id": "clip", "source_start_us": 0,
                         "text": None, "rationale": "observed visual", "evidence": ["visual-proof"]}
                        for index in range(4)]}
        provider = FakeProvider([json.dumps(repeated),
                                 '{"choice_index":999,"rationale":"invalid"}'] * 5)
        snapshot = StudioInputSnapshot({
            "assets": [{"asset_id": "clip", "kind": "clip", "duration_us": 90_000_000},
                       {"asset_id": "photo", "kind": "picture", "duration_us": None},
                       {"asset_id": "song", "kind": "audio", "duration_us": 95_000_000}],
            "observations": [{"observation_id": "visual-proof", "asset_id": "clip",
                              "modality": "vision", "text": "ceremony"},
                             {"observation_id": "photo-proof", "asset_id": "photo",
                              "modality": "vision", "text": "alternate scene"},
                             {"observation_id": "music-proof", "asset_id": "song",
                              "modality": "music", "text": "music"}],
            "project_brief": {"duration_min_us": 90_000_000,
                              "duration_max_us": 90_000_000, "story_beats": ["opening"],
                              "required_messages": [], "width": 1920, "height": 1080},
        }, "hash")
        synthesis = StudioSynthesis("direction", "premise", "effect",
                                    ("opening",), (), (), 0.5, ("risk",))
        with self.assertRaisesRegex(ValueError, "provider replacement option is invalid"):
            StudioRoleEngine(provider).create_long_timeline(snapshot, synthesis, (), "song")
        self.assertEqual(len(provider.requests), 10)
        self.assertIn("repeated_segment", provider.requests[1].messages[1].content)

    def test_long_timeline_provider_selects_evidence_backed_replacement(self):
        def sequence(starts):
            return json.dumps({"authorship": "autonomous_studio", "width": 1920,
                               "height": 1080, "fps": 30, "segments": [
                {"segment_id": f"shot-{index}", "kind": "video",
                 "start_us": index * 7_500_000, "duration_us": 7_500_000,
                 "track": "main", "asset_id": "clip", "source_start_us": start,
                 "text": None, "rationale": "observed video", "evidence": ["visual-proof"]}
                for index, start in enumerate(starts)]})
        provider = FakeProvider([
            sequence([0, 1_000_000, 15_000_000, 22_500_000]),
            '{"choice_index":0,"rationale":"a distinct observed still supports this beat"}',
            sequence([30_000_000, 37_500_000, 45_000_000, 52_500_000]),
            sequence([60_000_000, 67_500_000, 75_000_000, 82_500_000]),
        ])
        snapshot = StudioInputSnapshot({
            "assets": [{"asset_id": "clip", "kind": "clip", "duration_us": 90_000_000},
                       {"asset_id": "photo", "kind": "picture", "duration_us": None},
                       {"asset_id": "song", "kind": "audio", "duration_us": 95_000_000}],
            "observations": [{"observation_id": "visual-proof", "asset_id": "clip",
                              "modality": "vision", "text": "ceremony"},
                             {"observation_id": "photo-proof", "asset_id": "photo",
                              "modality": "vision", "text": "different angle"},
                             {"observation_id": "music-proof", "asset_id": "song",
                              "modality": "music", "text": "music"}],
            "project_brief": {"duration_min_us": 90_000_000,
                              "duration_max_us": 90_000_000,
                              "story_beats": ["opening", "event", "resolution"],
                              "required_messages": [], "width": 1920, "height": 1080},
        }, "hash")
        synthesis = StudioSynthesis("direction", "premise", "effect",
                                    ("opening", "event", "resolution"), (), (), 0.5, ("risk",))
        result = StudioRoleEngine(provider).create_long_timeline(snapshot, synthesis, (), "song")
        visuals = [item for item in result["segments"] if item["track"] == "main"]
        self.assertEqual(len(provider.requests), 4)
        self.assertEqual(visuals[1]["kind"], "picture")
        self.assertEqual(visuals[1]["asset_id"], "photo")
        self.assertEqual(visuals[1]["evidence"], ["photo-proof"])

    def test_specialist_receives_no_raw_path_and_returns_validated_contract(self):
        response = json.dumps({"role":"intent_insight","recommendation":"focus on service","confidence":0.8,
            "evidence":["o1"],"risks":["limited context"],"alternatives":["chronological"],"objections":[]})
        provider = FakeProvider([response])
        snapshot = StudioInputSnapshot({"assets":[{"asset_id":"a1"}],"observations":[{
            "observation_id":"o1","asset_id":"a1","text":"brief"}]}, "hash")
        result = StudioRoleEngine(provider).recommend("intent_insight", snapshot)
        self.assertEqual(result.role, "intent_insight")
        prompt = provider.requests[0].messages[1].content
        self.assertNotIn("source_path", prompt)
        self.assertIn("untrusted project data", provider.requests[0].messages[0].content)

    def test_malformed_role_response_fails_closed(self):
        malformed = '{"role":"story_architect","recommendation":"invent","confidence":1}'
        provider = FakeProvider([malformed, malformed, malformed])
        snapshot = StudioInputSnapshot({"assets":[],"observations":[]}, "hash")
        with self.assertRaises(ValueError):
            StudioRoleEngine(provider).recommend("story_architect", snapshot)

    def test_lead_editor_gets_one_schema_repair_turn(self):
        invalid = json.dumps({"authorship":"autonomous_studio","width":1,"height":1,"fps":1,
            "segments":[{"segment_id":"s1","kind":"picture","start_us":0.0,"duration_us":1.0,
                         "track":"main","asset_id":"a1","rationale":"proof","evidence":["o1"]}]})
        valid = json.dumps({"authorship":"autonomous_studio","width":1,"height":1,"fps":1,
            "segments":[{"segment_id":"s1","kind":"picture","start_us":0,"duration_us":1,
                         "track":"main","asset_id":"a1","rationale":"proof","evidence":["o1"]}]})
        provider = FakeProvider([invalid, valid])
        snapshot = StudioInputSnapshot({"assets":[{"asset_id":"a1"}],
            "observations":[{"observation_id":"o1","asset_id":"a1","text":"proof"}]}, "hash")
        synthesis = StudioSynthesis("direction", "premise", "effect", ("beat",), (), (), 0.5, ("risk",))
        result = StudioRoleEngine(provider).create_timeline(snapshot, synthesis, ())
        self.assertIsInstance(result["segments"][0]["start_us"], int)
        self.assertEqual(len(provider.requests), 2)

    def test_duration_repair_receives_all_available_coverage(self):
        valid = json.dumps({"authorship":"autonomous_studio","width":1920,"height":1080,"fps":30,
            "segments":[{"segment_id":"s1","kind":"picture","start_us":0,"duration_us":170000000,
                         "track":"main","asset_id":"a1","source_start_us":0,"text":None,
                         "rationale":"proof","evidence":["o1"]}]})
        provider = FakeProvider([valid])
        snapshot = StudioInputSnapshot({"assets":[{"asset_id":"a1","kind":"picture"},
                                                {"asset_id":"a2","kind":"clip"}],
            "observations":[{"observation_id":"o1","asset_id":"a1","text":"proof"},
                            {"observation_id":"o2","asset_id":"a2","text":"alternate"}],
            "authority_rules":{}, "project_brief":{"duration_min_us":170000000,
                                                       "duration_max_us":190000000}}, "hash")
        synthesis = StudioSynthesis("direction", "premise", "effect", ("beat",), (), (), 0.5, ("risk",))
        result = StudioRoleEngine(provider).revise_timeline(
            snapshot, synthesis, (), {"segments":[{"asset_id":"a1","evidence":["o1"]}]},
            "duration_out_of_range",
        )
        self.assertEqual(result["segments"][0]["duration_us"], 170000000)
        payload = json.loads(provider.requests[0].messages[1].content)
        self.assertEqual(len(payload["cited_evidence_and_assets"]["assets"]), 2)


if __name__ == "__main__":
    unittest.main()
