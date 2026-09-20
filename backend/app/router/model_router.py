from typing import Dict, Any, Optional
from pydantic import BaseModel

class RoutingDecision(BaseModel):
    task_type: str
    selected_model: str
    modality: str # "text", "vision", "code", "embedding"
    reason: str
    hardware_target: str = "local_gpu_cpu"

class ModelRouter:
    def __init__(self, default_text_model: str = "gemma4:latest", default_vision_model: str = "gemma4:latest"):
        self.default_text_model = default_text_model
        self.default_vision_model = default_vision_model

    def route(self, task_type: str, has_images: bool = False, is_code_task: bool = False) -> RoutingDecision:
        if has_images:
            return RoutingDecision(
                task_type=task_type,
                selected_model=self.default_vision_model,
                modality="vision",
                reason="Task requires multimodal visual input analysis."
            )
        elif is_code_task:
            return RoutingDecision(
                task_type=task_type,
                selected_model=self.default_text_model,
                modality="code",
                reason="Task involves Python data analysis script generation/execution."
            )
        else:
            return RoutingDecision(
                task_type=task_type,
                selected_model=self.default_text_model,
                modality="text",
                reason="Standard text reasoning and knowledge query."
            )
