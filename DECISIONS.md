# Project Decisions

This document records the main implementation decisions made for the Team Leave Scheduler project, along with the alternatives that were considered.

## 1. Backend choice: FastAPI with SQLite
- Decision: The service uses FastAPI for the API layer and SQLite for local persistence through SQLAlchemy.
- Why this was chosen: it keeps the project lightweight, easy to run locally, and well suited for a small scheduling application with simple data models.
- Alternatives considered:
  - Flask: simpler in some cases, but FastAPI provided clearer request validation and response models.
  - Django: powerful but heavier than needed for this scope.
  - A full database service such as PostgreSQL: unnecessary for the initial version and more complex to set up.

## 2. Leave validation rules: overlap and team-capacity limits
- Decision: A leave request is rejected if it overlaps with an already approved leave for the same employee, and if it would push a team above the 30% absence threshold on any working day.
- Why this was chosen: these rules match the business requirements and protect fairness across teams while avoiding duplicate leave periods for the same person.
- Alternatives considered:
  - Allowing overlapping leave for the same employee if the dates were not identical.
  - Checking the 30% rule only once for the entire leave range instead of per day.
  - Ignoring weekends and public holidays when calculating team capacity.

## 3. Approval workflow: pending requests are reviewed before final approval
- Decision: Leave requests are submitted as pending, then approved or rejected through a decision endpoint. Approval re-checks the 30% rule so the latest state is always enforced.
- Why this was chosen: it supports a realistic review process and prevents approvals from violating the team rule after other requests change.
- Alternatives considered:
  - Immediate auto-approval on submission.
  - Approval without re-validation, which could allow over-capacity situations.
  - A fully manual spreadsheet-based process, which would be less scalable and harder to test.
