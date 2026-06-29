import csv
import json
import os
from datetime import datetime
from database import engine, SessionLocal, Base
from models import Employee, LeaveRequest, PublicHoliday


def seed_database():
    """
    Seed the database with employees and public holidays.
    Only inserts data if tables are empty (idempotent).
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Check if tables are empty
        employee_count = db.query(Employee).count()
        holiday_count = db.query(PublicHoliday).count()

        if employee_count == 0 and holiday_count == 0:
            # Load and insert employees from CSV
            employees_csv_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "data", "employees.csv"
            )
            with open(employees_csv_path, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    employee = Employee(
                        id=int(row["id"]), name=row["name"], team=row["team"]
                    )
                    db.add(employee)

            db.commit()
            print(f"✓ Seeded {employee_count + db.query(Employee).count()} employees")

            # Load and insert public holidays from JSON
            holidays_json_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "data", "public_holidays.json"
            )
            with open(holidays_json_path, "r") as f:
                holidays = json.load(f)
                for holiday in holidays:
                    public_holiday = PublicHoliday(
                        date=datetime.strptime(holiday["date"], "%Y-%m-%d").date(),
                        name=holiday["name"],
                    )
                    db.add(public_holiday)

            db.commit()
            print(f"✓ Seeded {len(holidays)} public holidays")
        else:
            print("✓ Database already seeded. Skipping...")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
