import unittest

from mtcapcut.sequence_planner import plan_sequence_jobs


class SequencePlannerTests(unittest.TestCase):
    def test_twenty_minutes_has_bounded_stable_jobs_and_exact_runtime(self):
        jobs = plan_sequence_jobs(20 * 60 * 1_000_000,
                                  ("opening", "service", "resolution"))
        self.assertEqual(len(jobs), 40)
        self.assertEqual(jobs, plan_sequence_jobs(20 * 60 * 1_000_000,
                                                  ("opening", "service", "resolution")))
        self.assertEqual(jobs[0].sequence_id, "seq0001")
        self.assertEqual(jobs[-1].sequence_id, "seq0040")
        self.assertTrue(all(0 < job.duration_us <= 30_000_000 for job in jobs))
        self.assertEqual(jobs[-1].start_us + jobs[-1].duration_us, 20 * 60 * 1_000_000)
        self.assertTrue(all(left.start_us + left.duration_us == right.start_us
                            for left, right in zip(jobs, jobs[1:])))
        self.assertEqual({job.story_beat for job in jobs}, {"opening", "service", "resolution"})

    def test_three_minute_eight_beat_plan_keeps_eight_bounded_sequences(self):
        jobs = plan_sequence_jobs(180_000_000, tuple(f"beat-{i}" for i in range(8)))
        self.assertEqual(len(jobs), 8)
        self.assertEqual(jobs[-1].story_beat, "beat-7")
        self.assertEqual(sum(job.duration_us for job in jobs), 180_000_000)

    def test_missing_beats_or_invalid_target_fails(self):
        with self.assertRaises(ValueError):
            plan_sequence_jobs(120_000_000, ())
        with self.assertRaises(ValueError):
            plan_sequence_jobs(0, ("opening",))


if __name__ == "__main__":
    unittest.main()
