import json
import unittest

from mtcapcut.ai_provider import AIProviderSettings, ChatResponse
from mtcapcut.professional_finishing import ProfessionalFinishingEngine, ProfessionalFinishingPlan


class FakeProvider:
    def __init__(self, response):
        self.response = response
        self.requests = []
        self.settings = AIProviderSettings("local", "local_openai", "http://127.0.0.1:1/v1", "model", enabled=True)

    def complete(self, request):
        self.requests.append(request)
        return ChatResponse("id", "model", json.dumps(self.response))


def candidate():
    return {"segments":[
        {"segment_id":"v1","kind":"picture","start_us":0,"duration_us":2_000_000,
         "track":"main","rationale":"opening"},
        {"segment_id":"v2","kind":"video","start_us":2_000_000,"duration_us":2_000_000,
         "track":"main","rationale":"proof"},
        {"segment_id":"t1","kind":"text","start_us":0,"duration_us":4_000_000,
         "track":"titles","rationale":"identity"},
    ]}


class ProfessionalFinishingTests(unittest.TestCase):
    def test_pro_material_is_rejected_for_new_finishing(self):
        value = {"schema":"mtcapcut.finishing.v1","authorship":"autonomous_studio",
                 "visual_finishes":[
                    {"segment_id":"v1","transition":"Swipe_Left","transition_duration_us":400000,
                     "filter":"none","filter_intensity":0,"motion":"locked","rationale":"slide"},
                    {"segment_id":"v2","transition":"none","transition_duration_us":0,
                     "filter":"none","filter_intensity":0,"motion":"locked","rationale":"hold"}],
                 "text_finishes":[{"segment_id":"t1","intro":"none","outro":"none",
                                   "rationale":"static"}], "creative_rationale":"formal"}
        with self.assertRaisesRegex(ValueError, "CapCut Pro material"):
            ProfessionalFinishingEngine(FakeProvider(value)).design(candidate())

    def test_provider_authored_finishing_is_strict_and_covers_every_segment(self):
        value = {"schema":"mtcapcut.finishing.v1","authorship":"autonomous_studio",
                 "visual_finishes":[
                    {"segment_id":"v1","transition":"Mix","transition_duration_us":400000,
                     "filter":"Soft_Grain","filter_intensity":25,"motion":"slow_push_in",
                     "rationale":"restrained opening"},
                    {"segment_id":"v2","transition":"none","transition_duration_us":0,
                     "filter":"none","filter_intensity":0,"motion":"locked",
                     "rationale":"preserve documentary movement"}],
                 "text_finishes":[{"segment_id":"t1","intro":"Wiping_In","outro":"Wiping_Out",
                                    "rationale":"clear hierarchy"}],
                 "creative_rationale":"formal and restrained"}
        result = ProfessionalFinishingEngine(FakeProvider(value)).design(candidate())
        self.assertEqual(result.authorship, "autonomous_studio")
        self.assertEqual(result.visual_finishes[0].transition, "Mix")

    def test_unknown_segment_or_excessive_transition_fails_closed(self):
        value = {"schema":"mtcapcut.finishing.v1","authorship":"autonomous_studio",
                 "visual_finishes":[{"segment_id":"missing","transition":"Flash",
                    "transition_duration_us":900000,"filter":"none","filter_intensity":0,
                    "motion":"locked","rationale":"bad"}],"text_finishes":[],
                 "creative_rationale":"bad"}
        with self.assertRaises(ValueError):
            ProfessionalFinishingPlan.from_dict(value, candidate())

    def test_multiple_visuals_require_an_intentional_transition(self):
        value = {"schema":"mtcapcut.finishing.v1","authorship":"autonomous_studio",
                 "visual_finishes":[
                    {"segment_id":"v1","transition":"none","transition_duration_us":0,
                     "filter":"Enhance","filter_intensity":20,"motion":"locked","rationale":"clean"},
                    {"segment_id":"v2","transition":"none","transition_duration_us":0,
                     "filter":"Enhance","filter_intensity":20,"motion":"locked","rationale":"clean"}],
                 "text_finishes":[{"segment_id":"t1","intro":"none","outro":"none","rationale":"static"}],
                 "creative_rationale":"restrained"}
        with self.assertRaises(ValueError):
            ProfessionalFinishingPlan.from_dict(value, candidate())

    def test_finishing_receives_current_visual_evidence_and_story_direction(self):
        value = {"schema":"mtcapcut.finishing.v1", "authorship":"autonomous_studio",
                 "visual_finishes":[
                     {"segment_id":"v1", "transition":"Mix", "transition_duration_us":300000,
                      "filter":"none", "filter_intensity":0, "motion":"locked", "rationale":"clear still"},
                     {"segment_id":"v2", "transition":"none", "transition_duration_us":0,
                      "filter":"none", "filter_intensity":0, "motion":"locked", "rationale":"retain movement"}],
                 "text_finishes":[{"segment_id":"t1", "intro":"none", "outro":"none",
                                   "rationale":"readable"}], "creative_rationale":"serve the arc"}
        edit = candidate()
        edit["segments"][0].update({"asset_id":"photo", "evidence":["seen-photo", "other-asset"]})
        edit["segments"][1].update({"asset_id":"clip", "evidence":["seen-clip"]})
        evidence = {"seen-photo":{"asset_id":"photo", "modality":"vision", "text":"wide crowd photo"},
                    "other-asset":{"asset_id":"wrong", "modality":"vision", "text":"secret wrong asset"},
                    "seen-clip":{"asset_id":"clip", "modality":"vision", "start_us":0,
                                 "end_us":1, "text":"moving motorcade"}}
        provider = FakeProvider(value)
        ProfessionalFinishingEngine(provider).design(edit, evidence_index=evidence,
            director_synthesis={"premise":"service across communities", "audience_effect":"trust"})
        prompt = provider.requests[0].messages[1].content
        self.assertIn("wide crowd photo", prompt)
        self.assertIn("moving motorcade", prompt)
        self.assertIn("service across communities", prompt)
        self.assertNotIn("secret wrong asset", prompt)

    def test_video_finishing_excludes_visual_note_outside_selected_source_range(self):
        edit = candidate()
        edit["segments"][1].update({"asset_id":"clip", "source_start_us":10_000_000,
                                     "evidence":["outside"]})
        evidence = {"outside":{"asset_id":"clip", "modality":"vision",
                               "start_us":1_000_000, "end_us":1_000_001,
                               "text":"unrelated event"}}
        value = {"schema":"mtcapcut.finishing.v1", "authorship":"autonomous_studio",
                 "visual_finishes":[
                    {"segment_id":"v1", "transition":"Mix", "transition_duration_us":300000,
                     "filter":"none", "filter_intensity":0, "motion":"locked", "rationale":"still"},
                    {"segment_id":"v2", "transition":"none", "transition_duration_us":0,
                     "filter":"none", "filter_intensity":0, "motion":"locked", "rationale":"video"}],
                 "text_finishes":[{"segment_id":"t1", "intro":"none", "outro":"none",
                                   "rationale":"readable"}], "creative_rationale":"restrained"}
        provider = FakeProvider(value)
        ProfessionalFinishingEngine(provider).design(edit, evidence_index=evidence)
        self.assertNotIn("unrelated event", provider.requests[0].messages[1].content)

    def test_invalid_filter_intensity_repair_names_segment_and_accepts_corrected_plan(self):
        base = {"schema":"mtcapcut.finishing.v1", "authorship":"autonomous_studio",
                "visual_finishes":[
                    {"segment_id":"v1", "transition":"Mix", "transition_duration_us":300000,
                     "filter":"Soft_Grain", "filter_intensity":5, "motion":"locked", "rationale":"opening"},
                    {"segment_id":"v2", "transition":"none", "transition_duration_us":0,
                     "filter":"none", "filter_intensity":0, "motion":"locked", "rationale":"motion"}],
                "text_finishes":[{"segment_id":"t1", "intro":"none", "outro":"none",
                                  "rationale":"readable"}], "creative_rationale":"restrained"}

        class RepairProvider(FakeProvider):
            def complete(self, request):
                self.requests.append(request)
                result = json.loads(json.dumps(base))
                if len(self.requests) > 1:
                    result["visual_finishes"][0]["filter_intensity"] = 20
                return ChatResponse("id", "model", json.dumps(result))

        provider = RepairProvider(base)
        plan = ProfessionalFinishingEngine(provider).design(candidate())
        self.assertEqual(plan.visual_finishes[0].filter_intensity, 20)
        self.assertIn("segment v1", provider.requests[1].messages[1].content)


if __name__ == "__main__":
    unittest.main()
