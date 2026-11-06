"""Regression tests for review-only take suggestions."""
import unittest

from mtcapcut.take_review import WordToken, suggest_take_cleanup


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


if __name__ == "__main__":
    unittest.main()
