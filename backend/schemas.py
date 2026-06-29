from pydantic import BaseModel
from datetime import date
from typing import Optional


class EmployeeBase(BaseModel):
    id: int
    name: str
    team: str


class EmployeeResponse(EmployeeBase):
    pass


class LeaveRequestCreate(BaseModel):
    employee_id: int
    start_date: date
    end_date: date


class LeaveRequestResponse(BaseModel):
    id: int
    employee_id: int
    start_date: date
    end_date: date
    status: str

    class Config:
        from_attributes = True


class DecisionBody(BaseModel):
    decision: str  # "approved" | "rejected"


class PublicHolidayResponse(BaseModel):
    id: int
    date: date
    name: str

    class Config:
        from_attributes = True
