from pathlib import Path
import unittest

from mtcapcut.editorial import (
    Chapter, EditSegment, EditorialRevision, ElementPlacement, Scene,
    scene_range, select_edit_scope, to_timeline_plan, validate_revision,
)


def long_form_revision() -> EditorialRevision:
    segments = (
        EditSegment("seg-041", "scene-04", 710_000_000, 728_000_000, "bridge-in"),
        EditSegment("seg-042", "scene-04", 728_000_000, 754_000_000, "speaker claim"),
        EditSegment("seg-043", "scene-04", 754_000_000, 767_000_000, "supporting B-roll"),
        EditSegment("seg-044", "scene-04", 767_000_000, 785_000_000, "outcome"),
        EditSegment("seg-045", "scene-04", 785_000_000, 800_000_000, "bridge-out"),
    )
    elements = (
        ElementPlacement("video-42", "video", "main", 710_000_000, 800_000_000,
                         tuple(item.segment_id for item in segments), "av-video", Path("clip.mp4")),
        ElementPlacement("music-bed", "audio", "music", 710_000_000, 800_000_000,
                         tuple(item.segment_id for item in segments), "av-music", Path("music.mp3")),
        ElementPlacement("caption-1", "caption", "captions", 730_000_000, 760_000_000,
                         ("seg-042", "seg-043"), text="รายงานผลการดำเนินงาน"),
    )
    return EditorialRevision(
        "rev-18", "rev-17",
        (Chapter("chapter-04", "ผลดำเนินงาน", ("scene-04",)),),
        (Scene("scene-04", "chapter-04", "อธิบายผล", tuple(item.segment_id for item in segments)),),
        segments, elements,
    )


class EditorialModelTests(unittest.TestCase):
    def test_hierarchy_and_cross_segment_elements_are_valid(self):
        revision = long_form_revision()
        self.assertEqual(validate_revision(revision), [])
        self.assertEqual(scene_range(revision, "scene-04"), (710_000_000, 800_000_000))

    def test_minute_12_to_13_selects_stable_ids_and_crossing_elements(self):
        scope = select_edit_scope(long_form_revision(), 720_000_000, 780_000_000, context_us=10_000_000)
        self.assertEqual(scope.editable_segment_ids, ("seg-041", "seg-042", "seg-043", "seg-044"))
        self.assertEqual(scope.context_segment_ids, ("seg-041", "seg-042", "seg-043", "seg-044", "seg-045"))
        self.assertEqual(set(scope.affected_element_ids), {"video-42", "music-bed", "caption-1"})

    def test_orphans_and_non_overlapping_links_are_rejected(self):
        revision = long_form_revision()
        bad = EditorialRevision(revision.revision_id, revision.parent_revision_id,
            revision.chapters, revision.scenes, revision.segments,
            revision.elements + (ElementPlacement("bad", "text", "titles", 0, 1_000_000,
                                                   ("missing",), text="bad"),))
        errors = validate_revision(bad)
        self.assertTrue(any("missing segment" in error for error in errors))

    def test_mapping_preserves_element_and_edit_segment_ids(self):
        plan = to_timeline_plan(long_form_revision(), 1080, 1920, 30)
        caption = next(item for item in plan.segments if item.element_id == "caption-1")
        self.assertEqual(caption.kind, "text")
        self.assertEqual(caption.edit_segment_ids, ("seg-042", "seg-043"))


if __name__ == "__main__":
    unittest.main()
