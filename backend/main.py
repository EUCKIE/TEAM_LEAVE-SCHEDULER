from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from database import get_db, engine, Base
from models import Employee, LeaveRequest, PublicHoliday
from schemas import (
    LeaveRequestCreate,
    LeaveRequestResponse,
    DecisionBody,
    EmployeeResponse,
    PublicHolidayResponse,
)
from business_rules import validate_leave_request, exceeds_thirty_percent

# Initialize tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Team Leave Scheduler")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/leave-requests", status_code=201, response_model=LeaveRequestResponse)
def submit_leave_request(body: LeaveRequestCreate, db=Depends(get_db)):
    """
    Submit a new leave request.
    Validates against business rules and inserts as pending.
    """
    # Validate the request
    is_valid, reason = validate_leave_request(body.employee_id, body.start_date, body.end_date, db)
    if not is_valid:
        raise HTTPException(status_code=400, detail=reason)

    # Create pending leave request
    leave_request = LeaveRequest(
        employee_id=body.employee_id,
        start_date=body.start_date,
        end_date=body.end_date,
        status="pending",
    )
    db.add(leave_request)
    db.commit()
    db.refresh(leave_request)

    return leave_request


@app.patch("/leave-requests/{request_id}/decision", response_model=LeaveRequestResponse)
def decide_leave_request(request_id: int, body: DecisionBody, db=Depends(get_db)):
    """
    Approve or reject a leave request.
    If approving, re-validates the 30% rule (state may have changed).
    """
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if body.decision not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Decision must be 'approved' or 'rejected'")

    # If approving, re-run the 30% check
    if body.decision == "approved":
        employee = db.query(Employee).filter(Employee.id == leave_request.employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        # Re-validate per working day
        from business_rules import working_days_in_range
        holidays_obj = db.query(PublicHoliday).all()
        holidays = [h.date for h in holidays_obj]
        working_days = working_days_in_range(leave_request.start_date, leave_request.end_date, holidays)

        for day in working_days:
            if exceeds_thirty_percent(employee.team, day, db):
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot approve: would exceed 30% team absence on {day.strftime('%Y-%m-%d')}",
                )

    leave_request.status = body.decision
    db.commit()
    db.refresh(leave_request)

    return leave_request


@app.get("/leave-requests", response_model=list[LeaveRequestResponse])
def list_leave_requests(db=Depends(get_db)):
    """
    List approved and pending leave requests for the next 30 days.
    """
    today = datetime.now().date()
    thirty_days_later = today + timedelta(days=30)

    requests = (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.status.in_(["approved", "pending"]),
            LeaveRequest.start_date <= thirty_days_later,
            LeaveRequest.end_date >= today,
        )
        .order_by(LeaveRequest.start_date)
        .all()
    )

    return requests


@app.get("/employees", response_model=list[EmployeeResponse])
def list_employees(db=Depends(get_db)):
    """
    List all employees.
    """
    employees = db.query(Employee).order_by(Employee.id).all()
    return employees


@app.get("/public-holidays", response_model=list[PublicHolidayResponse])
def list_public_holidays(db=Depends(get_db)):
    """
    List all public holidays.
    """
    holidays = db.query(PublicHoliday).order_by(PublicHoliday.date).all()
    return holidays
