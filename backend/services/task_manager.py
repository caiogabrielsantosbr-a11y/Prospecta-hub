"""
Background Task Manager — orchestrates long-running extraction tasks.
Each task runs as an asyncio coroutine and broadcasts progress via WebSocket.
"""
import asyncio
import uuid
from datetime import datetime
from typing import Optional, Callable, Awaitable

from database.db import async_session
from database.models import TaskRecord


class TaskInfo:
    """In-memory representation of a running task."""

    def __init__(self, task_id: str, module: str, config: dict):
        self.id = task_id
        self.module = module
        self.config = config
        self.status = "running"
        self.progress = 0.0
        self.stats = {"queue": 0, "done": 0, "leads": 0, "errors": 0}
        self.logs: list[dict] = []
        self._cancel_event = asyncio.Event()
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # not paused initially
        self._asyncio_task: Optional[asyncio.Task] = None

    def add_log(self, message: str, level: str = "info"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.logs.append({"time": ts, "message": message, "level": level})
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]

    def to_dict(self):
        return {
            "id": self.id,
            "module": self.module,
            "status": self.status,
            "progress": self.progress,
            "stats": self.stats,
            "logs": self.logs[-20:],
            "config": self.config,
        }

    async def wait_if_paused(self):
        """Block until unpaused or cancelled."""
        await self._pause_event.wait()

    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()


class TaskManager:
    """Singleton that manages all background tasks."""

    def __init__(self):
        self.tasks: dict[str, TaskInfo] = {}
        self._broadcast_fn: Optional[Callable] = None

    def set_broadcast(self, fn: Callable):
        """Set the WebSocket broadcast function."""
        self._broadcast_fn = fn

    async def broadcast(self, task: TaskInfo):
        """Send task update to all connected clients."""
        if self._broadcast_fn:
            await self._broadcast_fn("task_update", task.to_dict())

    async def broadcast_all(self):
        """Send all tasks to clients (e.g. on connect)."""
        if self._broadcast_fn:
            data = [t.to_dict() for t in self.tasks.values()]
            await self._broadcast_fn("tasks_snapshot", data)

    async def create_task(
        self,
        module: str,
        config: dict,
        worker: Callable[["TaskInfo", "TaskManager"], Awaitable[None]],
    ) -> str:
        """Create and start a new background task."""
        task_id = str(uuid.uuid4())[:8]
        info = TaskInfo(task_id, module, config)
        self.tasks[task_id] = info

        # Persist to DB
        async with async_session() as session:
            record = TaskRecord(
                id=task_id, module=module, status="running", config=config
            )
            session.add(record)
            await session.commit()

        # Start the async worker
        info._asyncio_task = asyncio.create_task(self._run_worker(info, worker))
        info.add_log(f"Tarefa iniciada: {module}", "success")
        await self.broadcast(info)
        return task_id

    async def _run_worker(
        self,
        info: TaskInfo,
        worker: Callable[["TaskInfo", "TaskManager"], Awaitable[None]],
    ):
        try:
            await worker(info, self)
            if info.status == "running":
                info.status = "completed"
                info.progress = 100.0
                info.add_log("Tarefa finalizada!", "success")
        except asyncio.CancelledError:
            info.status = "stopped"
            info.add_log("Tarefa cancelada.", "warning")
        except Exception as e:
            info.status = "failed"
            info.add_log(f"Erro fatal: {str(e)}", "error")
        finally:
            await self._persist_status(info)
            await self.broadcast(info)

    async def pause(self, task_id: str):
        info = self.tasks.get(task_id)
        if info and info.status == "running":
            info.status = "paused"
            info._pause_event.clear()
            info.add_log("Pausado.", "warning")
            await self._persist_status(info)
            await self.broadcast(info)

    async def resume(self, task_id: str):
        info = self.tasks.get(task_id)
        if info and info.status == "paused":
            info.status = "running"
            info._pause_event.set()
            info.add_log("Retomado.", "info")
            await self._persist_status(info)
            await self.broadcast(info)

    async def stop(self, task_id: str):
        info = self.tasks.get(task_id)
        if info and info.status in ("running", "paused"):
            info._cancel_event.set()
            info._pause_event.set()  # unblock if paused
            info.status = "stopped"
            if info._asyncio_task:
                info._asyncio_task.cancel()
            info.add_log("Parado pelo usuário.", "warning")
            await self._persist_status(info)
            await self.broadcast(info)

    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> list[dict]:
        return [t.to_dict() for t in self.tasks.values()]

    def get_active_tasks(self) -> list[dict]:
        return [
            t.to_dict()
            for t in self.tasks.values()
            if t.status in ("running", "paused")
        ]

    async def _persist_status(self, info: TaskInfo):
        try:
            async with async_session() as session:
                record = await session.get(TaskRecord, info.id)
                if record:
                    record.status = info.status
                    record.stats = info.stats
                    record.progress = info.progress
                    record.updated_at = datetime.utcnow()
                    await session.commit()
        except Exception:
            pass


# Global singleton
task_manager = TaskManager()
