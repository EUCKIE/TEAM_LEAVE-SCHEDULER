import pytest
from datetime import date
from math import ceil
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Employee, LeaveRequest, PublicHoliday
from business_rules import exceeds_thirty_percent, team_size, count_team_on_leave


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def engineering_team(test_db):
    """Create a 5-person Engineering team."""
    employees = [
        Employee(id=1, name="Alice", team="Engineering"),
        Employee(id=2, name="Bob", team="Engineering"),
        Employee(id=3, name="Carol", team="Engineering"),
        Employee(id=4, name="David", team="Engineering"),
        Employee(id=5, name="Eve", team="Engineering"),
    ]
    for emp in employees:
        test_db.add(emp)
    test_db.commit()
    return employees


@pytest.fixture
def operations_team(test_db):
    """Create a 10-person Operations team."""
    employees = []
    for i in range(1, 11):
        emp = Employee(id=i + 100, name=f"OpsEmployee{i}", team="Operations")
        employees.append(emp)
        test_db.add(emp)
    test_db.commit()
    return employees


class TestThirtyPercentRule:
    def test_team_size_calculation(self, test_db, engineering_team):
        """Should correctly count team size."""
        size = team_size("Engineering", test_db)
        assert size == 5

    def test_team_size_independent_teams(self, test_db, engineering_team, operations_team):
        """Should count each team separately."""
        eng_size = team_size("Engineering", test_db)
        ops_size = team_size("Operations", test_db)
        assert eng_size == 5
        assert ops_size == 10

    def test_five_person_team_allows_one_on_leave(self, test_db, engineering_team):
        """5-person team: ceil(5 * 0.30) = 2, so 1 on leave is OK."""
        leave = LeaveRequest(
            id=1,
            employee_id=1,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 5),
            status="approved",
        )
        test_db.add(leave)
        test_db.commit()

        # One person on leave should be fine
        result = exceeds_thirty_percent("Engineering", date(2026, 7, 2), test_db)
        assert result is False

    def test_five_person_team_allows_two_on_leave(self, test_db, engineering_team):
        """5-person team: ceil(5 * 0.30) = 2, so 2 on leave hits threshold."""
        leave1 = LeaveRequest(
            id=1,
            employee_id=1,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 5),
            status="approved",
        )
        leave2 = LeaveRequest(
            id=2,
            employee_id=2,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 5),
            status="approved",
        )
        test_db.add(leave1)
        test_db.add(leave2)
        test_db.commit()

        # Two people on leave should hit the 30% threshold
        result = exceeds_thirty_percent("Engineering", date(2026, 7, 2), test_db)
        assert result is True

    def test_count_team_on_leave(self, test_db, engineering_team):
        """Should correctly count team members on leave for a given day."""
        leave1 = LeaveRequest(
            id=1,
            employee_id=1,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 5),
            status="approved",
        )
        leave2 = LeaveRequest(
            id=2,
            employee_id=2,
            start_date=date(2026, 7, 3),
            end_date=date(2026, 7, 7),
            status="approved",
        )
        test_db.add(leave1)
        test_db.add(leave2)
        test_db.commit()

        # July 2: only employee 1 is on leave
        count = count_team_on_leave("Engineering", date(2026, 7, 2), test_db)
        assert count == 1

        # July 4: both employees are on leave
        count = count_team_on_leave("Engineering", date(2026, 7, 4), test_db)
        assert count == 2

        # July 6: only employee 2 is on leave
        count = count_team_on_leave("Engineering", date(2026, 7, 6), test_db)
        assert count == 1

    def test_pending_leaves_not_counted(self, test_db, engineering_team):
        """Pending leaves should not count towards the 30% threshold."""
        leave1 = LeaveRequest(
            id=1,
            employee_id=1,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 5),
            status="approved",
        )
        leave2 = LeaveRequest(
            id=2,
            employee_id=2,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 5),
            status="pending",
        )
        test_db.add(leave1)
        test_db.add(leave2)
        test_db.commit()

        # Only 1 approved leave, so below threshold
        result = exceeds_thirty_percent("Engineering", date(2026, 7, 2), test_db)
        assert result is False

    def test_rejected_leaves_not_counted(self, test_db, engineering_team):
        """Rejected leaves should not count towards the 30% threshold."""
        leave = LeaveRequest(
            id=1,
            employee_id=1,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 5),
            status="rejected",
        )
        test_db.add(leave)
        test_db.commit()

        result = exceeds_thirty_percent("Engineering", date(2026, 7, 2), test_db)
        assert result is False

    def test_ten_person_team_allows_three_on_leave(self, test_db, operations_team):
        """10-person team: ceil(10 * 0.30) = 3, so 3 on leave hits threshold."""
        for i in range(1, 4):
            leave = LeaveRequest(
                id=i,
                employee_id=100 + i,
                start_date=date(2026, 7, 1),
                end_date=date(2026, 7, 5),
                status="approved",
            )
            test_db.add(leave)
        test_db.commit()

        # 3 people on leave should hit the 30% threshold for 10-person team
        result = exceeds_thirty_percent("Operations", date(2026, 7, 2), test_db)
        assert result is True

    def test_ten_person_team_allows_two_on_leave(self, test_db, operations_team):
        """10-person team: ceil(10 * 0.30) = 3, so 2 on leave is OK."""
        for i in range(1, 3):
            leave = LeaveRequest(
                id=i,
                employee_id=100 + i,
                start_date=date(2026, 7, 1),
                end_date=date(2026, 7, 5),
                status="approved",
            )
            test_db.add(leave)
        test_db.commit()

        # 2 people on leave should be fine for 10-person team
        result = exceeds_thirty_percent("Operations", date(2026, 7, 2), test_db)
        assert result is False

    def test_different_days_different_counts(self, test_db, engineering_team):
        """Different days should have different absence counts based on leave periods."""
        leave1 = LeaveRequest(
            id=1,
            employee_id=1,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 3),
            status="approved",
        )
        leave2 = LeaveRequest(
            id=2,
            employee_id=2,
            start_date=date(2026, 7, 3),
            end_date=date(2026, 7, 5),
            status="approved",
        )
        test_db.add(leave1)
        test_db.add(leave2)
        test_db.commit()

        # July 2: only employee 1 on leave (count=1, OK)
        assert exceeds_thirty_percent("Engineering", date(2026, 7, 2), test_db) is False

        # July 3: both on leave (count=2, threshold reached)
        assert exceeds_thirty_percent("Engineering", date(2026, 7, 3), test_db) is True

        # July 4: only employee 2 on leave (count=1, OK)
        assert exceeds_thirty_percent("Engineering", date(2026, 7, 4), test_db) is False

    def test_day_outside_leave_range(self, test_db, engineering_team):
        """Should not count absence for days outside the leave period."""
        leave = LeaveRequest(
            id=1,
            employee_id=1,
            start_date=date(2026, 7, 5),
            end_date=date(2026, 7, 10),
            status="approved",
        )
        test_db.add(leave)
        test_db.commit()

        # July 4 is before the leave starts
        count = count_team_on_leave("Engineering", date(2026, 7, 4), test_db)
        assert count == 0

        # July 11 is after the leave ends
        count = count_team_on_leave("Engineering", date(2026, 7, 11), test_db)
        assert count == 0

    def test_teams_independent(self, test_db, engineering_team, operations_team):
        """Approvals in one team should not affect another team's capacity."""
        # Fill Engineering team to 30% threshold
        for i in range(1, 3):
            leave = LeaveRequest(
                id=i,
                employee_id=i,
                start_date=date(2026, 7, 1),
                end_date=date(2026, 7, 5),
                status="approved",
            )
            test_db.add(leave)
        test_db.commit()

        # Engineering is at 30%
        assert exceeds_thirty_percent("Engineering", date(2026, 7, 2), test_db) is True

        # Operations should have no issues
        assert exceeds_thirty_percent("Operations", date(2026, 7, 2), test_db) is False
    # ceil(5 * 0.30) = 2, so 1 approved should pass
    ...

def test_five_person_team_blocks_at_two():
    # ceil(5 * 0.30) = 2, so adding a 2nd should fail
    ...

def test_rule_applied_per_day_not_whole_range():
    # Mon ok, Tue already at cap → multi-day request rejected
    ...