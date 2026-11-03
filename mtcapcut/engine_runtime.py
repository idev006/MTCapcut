"""UI-neutral asynchronous execution and event bridge for engines."""

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from queue import Empty, Queue
from threading import Event, Lock
from typing import Any, Callable
from uuid import uuid4


class EngineCancelled(RuntimeError):
    """Raised when an engine cooperatively observes cancellation."""


@dataclass(frozen=True)
class EngineEvent:
    job_id: str
    engine: str
    kind: str
    sequence: int
    occurred_at: str
    message: str = ""
    progress: float | None = None
    payload: dict[str, Any] = field(default_factory=dict)


class EngineContext:
    def __init__(self, job_id: str, engine: str, events: Queue, cancelled: Event,
                 on_event: Callable[[EngineEvent], None] | None):
        self.job_id = job_id
        self.engine = engine
        self._events = events
        self._cancelled = cancelled
        self._on_event = on_event
        self._sequence = 0
        self._lock = Lock()

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled.is_set()

    def raise_if_cancelled(self) -> None:
        if self.is_cancelled:
            raise EngineCancelled(f"engine job cancelled: {self.job_id}")

    def emit(self, kind: str, *, message: str = "", progress: float | None = None,
             payload: dict[str, Any] | None = None) -> EngineEvent:
        if progress is not None and not 0 <= progress <= 1:
            raise ValueError("progress must be between 0 and 1")
        with self._lock:
            self._sequence += 1
            event = EngineEvent(self.job_id, self.engine, kind, self._sequence,
                                datetime.now(timezone.utc).isoformat(), message,
                                progress, payload or {})
        self._events.put(event)
        if self._on_event is not None:
            self._on_event(event)
        return event


class JobHandle:
    def __init__(self, job_id: str, events: Queue, cancelled: Event):
        self.job_id = job_id
        self._events = events
        self._cancelled = cancelled
        self._future: Future | None = None

    def _bind(self, future: Future) -> None:
        self._future = future

    def cancel(self) -> None:
        self._cancelled.set()

    def done(self) -> bool:
        return self._future is not None and self._future.done()

    def result(self, timeout: float | None = None):
        if self._future is None:
            raise RuntimeError("job has not started")
        return self._future.result(timeout=timeout)

    def add_done_callback(self, callback: Callable[[Future], None]) -> None:
        if self._future is None:
            raise RuntimeError("job has not started")
        self._future.add_done_callback(callback)

    def drain_events(self, limit: int | None = None) -> tuple[EngineEvent, ...]:
        items = []
        while limit is None or len(items) < limit:
            try:
                items.append(self._events.get_nowait())
            except Empty:
                break
        return tuple(items)


class EngineRunner:
    def __init__(self, max_workers: int = 2):
        if max_workers < 1:
            raise ValueError("max_workers must be positive")
        self._executor = ThreadPoolExecutor(max_workers=max_workers,
                                            thread_name_prefix="mtcapcut-engine")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.shutdown()

    def shutdown(self, wait: bool = True) -> None:
        self._executor.shutdown(wait=wait, cancel_futures=False)

    def submit(self, engine: str, operation: Callable[[EngineContext], object], *,
               on_event: Callable[[EngineEvent], None] | None = None) -> JobHandle:
        if not engine.strip():
            raise ValueError("engine name is required")
        job_id = str(uuid4())
        events: Queue = Queue()
        cancelled = Event()
        context = EngineContext(job_id, engine, events, cancelled, on_event)
        handle = JobHandle(job_id, events, cancelled)

        def run():
            context.emit("started")
            try:
                context.raise_if_cancelled()
                result = operation(context)
                context.raise_if_cancelled()
                context.emit("completed", progress=1.0)
                return result
            except EngineCancelled:
                context.emit("cancelled")
                raise
            except Exception as error:
                context.emit("failed", message=str(error),
                             payload={"error_type": type(error).__name__})
                raise

        handle._bind(self._executor.submit(run))
        return handle
