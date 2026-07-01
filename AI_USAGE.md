# AI Usage Notes

This project was developed with support from AI-assisted tools during planning, implementation, and testing.

## Tools used
- CLAUDE for code generation, refactoring suggestions, and test scaffolding.
- VS Code terminal for running the project and executing tests.
- Python analysis tools for checking syntax and import issues while working on the backend.

## Two most useful prompts
1. “Help me implement leave validation rules for overlapping approved leave and the 30% team absence threshold, including tests.”
2. “Review the FastAPI backend structure and suggest a clean way to organize business rules, models, and API endpoints.”

## One correction made
- The 30% rule was corrected to be evaluated per working day rather than as a single check for the whole leave period, and the logic was adjusted to ignore weekends and public holidays.
