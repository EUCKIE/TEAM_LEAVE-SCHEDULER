from datetime import date, timedelta
from math import ceil
from models import Employee, LeaveRequest, PublicHoliday


def working_days_in_range(start: date, end: date, holidays: list[date]) -> list[date]:
    """Returns dates that are Mon–Fri and not public holidays."""
    working_days = []
    current = start
    holidays_set = set(holidays)
    
    while current <= end:
        # Check if weekday (0=Monday, 6=Sunday)
        if current.weekday() < 5 and current not in holidays_set:
            working_days.append(current)
        current += timedelta(days=1)
    
    return working_days


def count_team_on_leave(team: str, day: date, db) -> int:
    """Count approved leaves overlapping this day for this team."""
    approved_leaves = db.query(LeaveRequest).filter(
        LeaveRequest.status == "approved",
        LeaveRequest.start_date <= day,
        LeaveRequest.end_date >= day,
    ).all()
    
    # Count only those from employees in the specified team
    count = 0
    for leave in approved_leaves:
        employee = db.query(Employee).filter(Employee.id == leave.employee_id).first()
        if employee and employee.team == team:
            count += 1
    
    return count


def team_size(team: str, db) -> int:
    """Total headcount for the team."""
    return db.query(Employee).filter(Employee.team == team).count()


def exceeds_thirty_percent(team: str, day: date, db) -> bool:
    """
    My interpretation: ceil(team_size * 0.30).
    Applied per-day across the requested range.
    """
    total = team_size(team, db)
    on_leave = count_team_on_leave(team, day, db)
    
    max_allowed = ceil(total * 0.30)
    return on_leave >= max_allowed


def has_overlapping_approved_leave(employee_id: int, start: date, end: date, db) -> bool:
    """
    Overlap = any existing APPROVED request where ranges intersect.
    Pending requests do NOT block submission.
    """
    overlapping = db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == employee_id,
        LeaveRequest.status == "approved",
        LeaveRequest.start_date <= end,
        LeaveRequest.end_date >= start,
    ).first()
    
    return overlapping is not None


def validate_leave_request(employee_id, start, end, db) -> tuple[bool, str]:
    """Master validator — returns (is_valid, reason_if_not)."""
    # Check if employee exists
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        return False, "Employee not found"
    
    # Check date validity
    if start > end:
        return False, "Start date cannot be after end date"
    
    # Check for overlapping approved leave
    if has_overlapping_approved_leave(employee_id, start, end, db):
        return False, "Employee has overlapping approved leave"
    
    # Get all public holidays
    holidays_obj = db.query(PublicHoliday).all()
    holidays = [h.date for h in holidays_obj]
    
    # Get working days in the range
    working_days = working_days_in_range(start, end, holidays)
    
    # Check if any day exceeds 30% team threshold
    for day in working_days:
        if exceeds_thirty_percent(employee.team, day, db):
            return False, f"Cannot exceed 30% team absence on {day.strftime('%Y-%m-%d')}"
    
    return True, ""