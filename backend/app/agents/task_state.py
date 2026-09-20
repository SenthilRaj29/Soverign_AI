import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class TraceStep(BaseModel):
    step_number: int
    component: str
    action: str
    status: str # "RUNNING", "COMPLETED", "FAILED"
    details: str
    timestamp: float = Field(default_factory=time.time)
    duration_ms: Optional[float] = 0.0

class TaskState(BaseModel):
    task_id: str
    user_id: str
    objective: str
    status: str = "PENDING" # PENDING, PLANNING, RUNNING, WAITING_FOR_APPROVAL, COMPLETED, FAILED
    plan: List[str] = []
    current_step_index: int = 0
    trace: List[TraceStep] = []
    documents: List[str] = []
    sources: List[Dict[str, Any]] = []
    tool_calls: List[Dict[str, Any]] = []
    artifacts: List[str] = []
    error: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None

class TaskStateManager:
    def __init__(self):
        self._tasks: Dict[str, TaskState] = {}

    def create_task(self, task_id: str, user_id: str, objective: str) -> TaskState:
        state = TaskState(task_id=task_id, user_id=user_id, objective=objective)
        self._tasks[task_id] = state
        return state

    def get_task(self, task_id: str) -> Optional[TaskState]:
        return self._tasks.get(task_id)

    def update_task_status(self, task_id: str, status: str):
        if task_id in self._tasks:
            self._tasks[task_id].status = status
            if status in ["COMPLETED", "FAILED"]:
                self._tasks[task_id].completed_at = time.time()

    def add_trace_step(self, task_id: str, component: str, action: str, details: str, duration_ms: float = 0.0) -> TraceStep:
        if task_id in self._tasks:
            step_num = len(self._tasks[task_id].trace) + 1
            step = TraceStep(
                step_number=step_num,
                component=component,
                action=action,
                status="COMPLETED",
                details=details,
                duration_ms=duration_ms
            )
            self._tasks[task_id].trace.append(step)
            return step
        return None
