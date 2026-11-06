"""Regression tests for review-only take suggestions."""
import unittest
from pathlib import Path
import tempfile

from mtcapcut.map import UnderstandingMap
from mtcapcut.take_review import WordToken, suggest_take_cleanup, suggest_for_asset


class TakeReviewTests(unittest.TestCase):
    def test_pause_is_candidate_not_edit(self):
        words = [WordToken("hello", 0, 300_000),
                 WordToken("world", 1_200_000, 1_500_000)]
        result = suggest_take_cleanup(words)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].kind, "possible_pause")
        self.assertEqual((result[0].start_us, result[0].end_us), (300_000, 1_200_000))
        self.assertTrue(result[0].review_required)

    def test_repeated_word_flagged_but_not_removed(self):
        words = [WordToken("ครับ", 0, 150_000),
                 WordToken("ครับ", 175_000, 300_000)]
        result = suggest_take_cleanup(words)
        self.assertEqual([item.kind for item in result], ["possible_repetition"])

    def test_low_confidence_not_flagged(self):
        words = [WordToken("yes", 0, 100_000, 0.2),
                 WordToken("yes", 100_000, 200_000)]
        self.assertEqual(suggest_take_cleanup(words), ())

    def test_unsorted_fails_closed(self):
        with self.assertRaises(ValueError):
            suggest_take_cleanup([WordToken("a", 300, 400),
                                  WordToken("b", 200, 350)])

    def test_empty_and_noisy_punctuation(self):
        self.assertEqual(suggest_take_cleanup([]), ())
        self.assertEqual(suggest_take_cleanup([
            WordToken("!", 0, 10), WordToken("?", 11, 20)]), ())

    def test_repeated_emphasis_not_automatically_removed(self):
        result = suggest_take_cleanup([
            WordToken("ไม่", 0, 200), WordToken("ไม่", 200, 400)])
        self.assertTrue(result[0].review_required)

    def test_old_asset_version_words_are_not_reused(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "voice.wav")
            with UnderstandingMap(Path(folder) / "map.sqlite3") as mapping:
                asset = {"asset_id":"voice", "path":path, "kind":"audio", "role":"speech",
                         "source":"user", "rights_status":"owned", "content_hash":"old",
                         "size_bytes":1, "technical":{}}
                mapping.add_asset(asset)
                mapping.add_observations("voice", [
                    {"modality":"speech_word", "text":"yes", "start_us":0, "end_us":100_000,
                     "confidence":0.99, "producer":"ear", "producer_version":"1"},
                    {"modality":"speech_word", "text":"yes", "start_us":110_000, "end_us":200_000,
                     "confidence":0.99, "producer":"ear", "producer_version":"1"},
                ])
                self.assertEqual(len(suggest_for_asset(mapping, "voice")), 1)
                mapping.register_bundle([{**asset, "content_hash":"new"}])
                self.assertEqual(suggest_for_asset(mapping, "voice"), ())


if __name__ == "__main__":
    unittest.main()
