import json
import unittest

from mtcapcut.ai_provider import AIProviderSettings, ChatResponse
from mtcapcut.professional_finishing import ProfessionalFinishingEngine, ProfessionalFinishingPlan


class FakeProvider:
    def __init__(self, response):
        self.response = response
        self.settings = AIProviderSettings("local", "local_openai", "http://127.0.0.1:1/v1", "model", enabled=True)

    def complete(self, request):
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


if __name__ == "__main__":
    unittest.main()
