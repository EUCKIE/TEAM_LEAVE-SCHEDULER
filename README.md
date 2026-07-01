# Team Leave Scheduler

A lightweight leave-management application that helps teams manage leave requests while enforcing simple business rules such as overlap prevention and team absence limits.

## Overview

This project contains:
- a FastAPI backend for leave request submission, approval, and listing
- a small SQLite-backed data layer
- a simple frontend page for interacting with the app
- seed data for employees and public holidays

## Features

- Submit leave requests for an employee
- Prevent overlapping approved leave for the same employee
- Enforce a team-level absence cap of 30% on working days
- Approve or reject pending requests
- View upcoming approved and pending leave requests
- Load starter employee and holiday data from CSV/JSON files

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- Uvicorn
- HTML/CSS/JavaScript for the frontend

## Project Structure

- backend/ - API, business rules, database models, and tests
- data/ - employee CSV and holiday JSON seed data
- frontend/ - simple static interface

## Setup

1. Create and activate a virtual environment
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies
   ```powershell
   pip install -r requirements.txt
   ```

3. Seed the database
   ```powershell
   cd backend
   python seed.py
   ```

## Run the Application

Start the backend server:

```powershell
cd backend
uvicorn main:app --reload --port 8000
```

The API will be available at:
- http://127.0.0.1:8000/docs

Open the frontend page in your browser:
- frontend/index.html

## API Endpoints

The backend provides these main routes:

- POST /leave-requests - create a new leave request
- PATCH /leave-requests/{request_id}/decision - approve or reject a request
- GET /leave-requests - list upcoming approved and pending requests
- GET /employees - list employees
- GET /public-holidays - list public holidays

## Testing

Run the backend tests with:

```powershell
cd backend
pytest tests -q
```

## Notes

The leave validation logic is designed to be simple and transparent for a small team scheduling use case. It checks:
- whether the employee already has overlapping approved leave
- whether the request would exceed the 30% team absence threshold on any working day
- whether weekends and public holidays are excluded from the working-day calculation
