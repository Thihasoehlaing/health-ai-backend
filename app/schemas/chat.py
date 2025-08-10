from pydantic import BaseModel, Field
from typing import Literal

class StartSessionRequest(BaseModel):
    deviceId: str = Field(..., min_length=3, max_length=120)
    channel: Literal["voice", "touch"] = "touch"

class AddMessageRequest(BaseModel):
    role: Literal["user", "assistant", "system"]
    text: str = Field(..., min_length=1, max_length=2000)
