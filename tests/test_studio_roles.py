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
