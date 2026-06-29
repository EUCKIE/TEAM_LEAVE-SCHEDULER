from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    team = Column(String, index=True)

    leave_requests = relationship("LeaveRequest", back_populates="employee")


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), index=True)
    start_date = Column(Date, index=True)
    end_date = Column(Date, index=True)
    status = Column(String, default="pending", index=True)  # pending | approved | rejected

    employee = relationship("Employee", back_populates="leave_requests")


class PublicHoliday(Base):
    __tablename__ = "public_holidays"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True)
    name = Column(String, index=True)
