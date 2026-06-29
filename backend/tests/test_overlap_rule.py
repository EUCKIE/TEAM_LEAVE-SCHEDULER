import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Employee, LeaveRequest, PublicHoliday
from business_rules import has_overlapping_approved_leave


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
def sample_employees(test_db):
    """Create sample employees for testing."""
    employees = [
        Employee(id=1, name="Alice", team="Engineering"),
        Employee(id=2, name="Bob", team="Engineering"),
        Employee(id=3, name="Carol", team="Operations"),
    ]
    for emp in employees:
        test_db.add(emp)
    test_db.commit()
    return employees


class TestOverlapRule:
    def test_no_overlap_with_approved_leave(self, test_db, sample_employees):
        """Should allow leave request when no approved leave exists for the employee."""
        # Create an approved leave for different employee
        leave = LeaveRequest(
            id=1,
            employee_id=2,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 5),
            status="approved",
        )
        test_db.add(leave)
        test_db.commit()

        # Check employee 1 can request overlapping dates
        result = has_overlapping_approved_leave(
            1, date(2026, 7, 1), date(2026, 7, 10), test_db
        )
        assert result is False

    def test_overlapping_approved_request_rejected(self, test_db, sample_employees):
        """Should detect overlap when approved leave overlaps."""
        # Create an approved leave
        leave = LeaveRequest(
            id=1,
            employee_id=1,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 5),
            status="approved",
        )
        test_db.add(leave)
        test_db.commit()

        # Try to request overlapping dates
        result = has_overlapping_approved_leave(
            1, date(2026, 7, 3), date(2026, 7, 10), test_db
        )
        assert result is True

    def test_pending_leave_does_not_block(self, test_db, sample_employees):
        """Should allow leave request when only pending leave exists."""
        # Create a pending leave
        leave = LeaveRequest(
            id=1,
            employee_id=1,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 5),
            status="pending",
        )
        test_db.add(leave)
        test_db.commit()

        # Should allow requesting overlapping dates
        result = has_overlapping_approved_leave(
            1, date(2026, 7, 3), date(2026, 7, 10), test_db
        )
        assert result is False

    def test_rejected_leave_does_not_block(self, test_db, sample_employees):
        """Should allow leave request when only rejected leave exists."""
        # Create a rejected leave
        leave = LeaveRequest(
            id=1,
            employee_id=1,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 5),
            status="rejected",
        )
        test_db.add(leave)
        test_db.commit()

        # Should allow requesting overlapping dates
        result = has_overlapping_approved_leave(
            1, date(2026, 7, 3), date(2026, 7, 10), test_db
        )
        assert result is False

    def test_exact_date_match_overlaps(self, test_db, sample_employees):
        """Should detect overlap when dates match exactly."""
        leave = LeaveRequest(
            id=1,
            employee_id=1,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 5),
            status="approved",
        )
        test_db.add(leave)
        test_db.commit()

        result = has_overlapping_approved_leave(
            1, date(2026, 7, 1), date(2026, 7, 5), test_db
        )
        assert result is True

    def test_partial_overlap_start(self, test_db, sample_employees):
        """Should detect overlap when new request starts before approved leave ends."""
        leave = LeaveRequest(
            id=1,
            employee_id=1,
            start_date=date(2026, 7, 5),
            end_date=date(2026, 7, 10),
            status="approved",
        )
        test_db.add(leave)
        test_db.commit()

        result = has_overlapping_approved_leave(
            1, date(2026, 7, 1), date(2026, 7, 7), test_db
        )
        assert result is True

    def test_partial_overlap_end(self, test_db, sample_employees):
        """Should detect overlap when new request ends after approved leave starts."""
        leave = LeaveRequest(
            id=1,
            employee_id=1,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 5),
            status="approved",
        )
        test_db.add(leave)
        test_db.commit()

        result = has_overlapping_approved_leave(
            1, date(2026, 7, 3), date(2026, 7, 10), test_db
        )
        assert result is True

    def test_no_overlap_before(self, test_db, sample_employees):
        """Should allow leave request that ends before approved leave starts."""
        leave = LeaveRequest(
            id=1,
            employee_id=1,
            start_date=date(2026, 7, 10),
            end_date=date(2026, 7, 15),
            status="approved",
        )
        test_db.add(leave)
        test_db.commit()

        result = has_overlapping_approved_leave(
            1, date(2026, 7, 1), date(2026, 7, 5), test_db
        )
        assert result is False

    def test_no_overlap_after(self, test_db, sample_employees):
        """Should allow leave request that starts after approved leave ends."""
        leave = LeaveRequest(
            id=1,
            employee_id=1,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 5),
            status="approved",
        )
        test_db.add(leave)
        test_db.commit()

        result = has_overlapping_approved_leave(
            1, date(2026, 7, 10), date(2026, 7, 15), test_db
        )
        assert result is False

    def test_multiple_approved_leaves_one_overlaps(self, test_db, sample_employees):
        """Should detect overlap when one of multiple approved leaves overlaps."""
        leave1 = LeaveRequest(
            id=1,
            employee_id=1,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 5),
            status="approved",
        )
        leave2 = LeaveRequest(
            id=2,
            employee_id=1,
            start_date=date(2026, 7, 20),
            end_date=date(2026, 7, 25),
            status="approved",
        )
        test_db.add(leave1)
        test_db.add(leave2)
        test_db.commit()

        result = has_overlapping_approved_leave(
            1, date(2026, 7, 3), date(2026, 7, 7), test_db
        )
        assert result is True
    ...

def test_adjacent_dates_not_overlap():
    # end = Mon, new start = Tue → should pass
    ...

def test_pending_request_does_not_block_new_submission():
    # pending does not count as overlap
    ...