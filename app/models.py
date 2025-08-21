from typing import List, Optional

from pydantic import BaseModel, Field


class Department(BaseModel):
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    days: List[str]
    hours: str


class Provider(BaseModel):
    name: str
    certification: str
    specialty: str
    departments: List[Department] = Field(default_factory=list)


class SessionStartRequest(BaseModel):
    patient_id: str


class SessionStartResponse(BaseModel):
    thread_id: str
    patient_id: str
    patient_name: str


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    reset: bool = False
