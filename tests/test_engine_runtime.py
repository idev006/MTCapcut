from threading import Event
import unittest

from mtcapcut.engine_runtime import EngineCancelled, EngineRunner


class EngineRuntimeTests(unittest.TestCase):
    def test_submit_is_non_blocking_and_events_can_be_polled(self):
        entered = Event()
        release = Event()

        def operation(context):
            entered.set()
            context.emit("progress", message="working", progress=0.5)
            release.wait(timeout=2)
            return {"value": 42}

        with EngineRunner(max_workers=1) as runner:
            handle = runner.submit("fixture-engine", operation)
            self.assertTrue(entered.wait(timeout=1))
            self.assertFalse(handle.done())
            release.set()
            self.assertEqual(handle.result(timeout=2), {"value": 42})
            events = handle.drain_events()
            self.assertEqual([event.kind for event in events], ["started", "progress", "completed"])
            self.assertEqual([event.sequence for event in events], [1, 2, 3])

    def test_cooperative_cancellation_and_callback(self):
        entered = Event()
        continue_work = Event()
        received = []

        def operation(context):
            entered.set()
            continue_work.wait(timeout=2)
            context.raise_if_cancelled()
            return "unreachable"

        with EngineRunner(max_workers=1) as runner:
            handle = runner.submit("fixture-engine", operation, on_event=received.append)
            self.assertTrue(entered.wait(timeout=1))
            handle.cancel()
            continue_work.set()
            with self.assertRaises(EngineCancelled):
                handle.result(timeout=2)
            self.assertEqual(received[-1].kind, "cancelled")


if __name__ == "__main__":
    unittest.main()
