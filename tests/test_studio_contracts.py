import json
import unittest

from mtcapcut.studio_contracts import parse_recommendation, parse_synthesis, parse_timeline_candidate


class StudioContractTests(unittest.TestCase):
    def test_recommendation_requires_evidence_risks_and_alternatives(self):
        valid = json.dumps({"role":"story_architect","recommendation":"Use a clear arc","confidence":0.8,
                            "evidence":["obs-1"],"risks":["context loss"],"alternatives":["chronological"],
                            "objections":[]})
        result = parse_recommendation(valid, "story_architect", {"obs-1"})
        self.assertEqual(result.evidence, ("obs-1",))
        for field in ("evidence", "risks", "alternatives"):
            bad = json.loads(valid)
            bad[field] = []
            with self.assertRaises(ValueError):
                parse_recommendation(json.dumps(bad), "story_architect", {"obs-1"})

    def test_role_is_bound_by_orchestrator_not_provider_echo(self):
        value = {"role":"wrong-role","recommendation":"Use evidence","confidence":0.5,
                 "evidence":["obs-1"],"risks":["risk"],"alternatives":["alternative"],
                 "objections":[]}
        result = parse_recommendation(json.dumps(value), "story_architect", {"obs-1"})
        self.assertEqual(result.role, "story_architect")

    def test_hallucinated_evidence_is_pruned_when_real_anchor_remains(self):
        value = {"role":"story_architect","recommendation":"Use evidence","confidence":0.5,
                 "evidence":["invented", "obs-1"],"risks":["risk"],"alternatives":["alternative"],
                 "objections":[]}
        result = parse_recommendation(json.dumps(value), "story_architect", {"obs-1"})
        self.assertEqual(result.evidence, ("obs-1",))
        value["evidence"] = ["invented"]
        with self.assertRaisesRegex(ValueError, "no known evidence"):
            parse_recommendation(json.dumps(value), "story_architect", {"obs-1"})

    def test_typed_rights_objection_blocks_publication_only(self):
        value = {"role":"fact_ethics_critic","recommendation":"Use only cleared media","confidence":0.8,
                 "evidence":["obs-1"],"risks":["rights"],"alternatives":["omit"],"objections":[{
                    "category":"rights","severity":"high","finding":"Publication permission is missing",
                    "evidence":["obs-1"],"required_action":"Obtain permission","owner_role":"rights_editor"}]}
        result = parse_recommendation(json.dumps(value), "fact_ethics_critic", {"obs-1"})
        self.assertEqual([str(item) for item in result.objections[0].blocks_scopes], ["publication"])

    def test_objection_without_real_evidence_is_not_promoted_to_a_finding(self):
        value = {"role":"fact_ethics_critic","recommendation":"Use verified media","confidence":0.8,
                 "evidence":["obs-1"],"risks":["rights"],"alternatives":["omit"],"objections":[{
                    "category":"rights","severity":"high","finding":"Unsupported claim",
                    "evidence":["invented"],"required_action":"Verify","owner_role":"rights_editor"}]}
        result = parse_recommendation(json.dumps(value), "fact_ethics_critic", {"obs-1"})
        self.assertEqual(result.objections, ())

    def test_no_objection_sentence_is_not_allowed_as_an_objection(self):
        value = {"role":"fact_ethics_critic","recommendation":"Proceed","confidence":0.8,
                 "evidence":["obs-1"],"risks":["limited"],"alternatives":["omit"],"objections":[{
                    "category":"creative","severity":"note","finding":"No explicit objection is present",
                    "evidence":["obs-1"],"required_action":"None","owner_role":"director"}]}
        with self.assertRaises(ValueError):
            parse_recommendation(json.dumps(value), "fact_ethics_critic", {"obs-1"})

    def test_pre_candidate_fact_precaution_is_warning_not_private_blocker(self):
        value = {"role":"fact_ethics_critic","recommendation":"Verify claims","confidence":0.8,
                 "evidence":["obs-1"],"risks":["facts"],"alternatives":["omit"],"objections":[{
                    "category":"fact","severity":"high","finding":"All claims require verification",
                    "evidence":["obs-1"],"required_action":"Run fact gate","owner_role":"fact_editor"}]}
        result = parse_recommendation(json.dumps(value), "fact_ethics_critic", {"obs-1"})
        self.assertEqual(result.objections[0].blocks_scopes, ())

    def test_director_cannot_remove_objections_or_invent_recommendations(self):
        base = {"creative_direction":"restrained","premise":"service","audience_effect":"trust",
                "story_beats":["hook","proof","resolution"],"accepted_recommendation_ids":["r1"],
                "unresolved_objections":["rights unclear"],"confidence":0.7,"risks":["limited evidence"]}
        self.assertEqual(parse_synthesis(json.dumps(base), {"r1"}, {"rights unclear"}).premise, "service")
        base["unresolved_objections"] = []
        repaired = parse_synthesis(json.dumps(base), {"r1"}, {"rights unclear"})
        self.assertEqual(repaired.unresolved_objections, ("rights unclear",))

    def test_timeline_requires_autonomous_authorship_and_unique_segment_ids(self):
        value = {"authorship":"autonomous_studio","width":1920,"height":1080,"fps":30,
                 "segments":[{"segment_id":"s1","kind":"picture","start_us":0,"duration_us":1,
                              "track":"main","asset_id":"a1","rationale":"opening","evidence":["o1"]}]}
        self.assertEqual(parse_timeline_candidate(json.dumps(value))["authorship"], "autonomous_studio")
        value["segments"].append(dict(value["segments"][0]))
        with self.assertRaises(ValueError):
            parse_timeline_candidate(json.dumps(value))


if __name__ == "__main__":
    unittest.main()
