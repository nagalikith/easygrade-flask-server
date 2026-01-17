# easygrade-flask-server

FastAPI backend for EasyGrade. It powers assignment creation, submission intake, answer extraction, and section/user management. The service supports code submissions and PDF/image submissions, extracts per-question answers into local storage, and exposes aggregated views for instructors.

## Why This Repo Helps
- Automates grading workflows by standardizing submissions and saving extracted answers.
- Centralizes assignment, section, and user operations for course management.
- Makes it easy to review all students' answers to a specific question through an API endpoint.
- Supports OCR hooks for handwritten answers via a vision model integration.

## Tech Stack
- FastAPI + Starlette (routing, sessions, templates)
- SQLAlchemy + PostgreSQL (data layer)
- OpenCV + PyMuPDF (image/PDF processing)
- PyJWT (token auth)
- Requests (vision OCR HTTP integration)

## Quick Start
Create required directories:
```
mkdir assignments submissions
```

Create a `.env` file (see `.env.example`) and fill in:
- `DB_INFO` (JSON)
- `AWS_CRED` + `AWS_BUCKET`
- `JWT_SECRET_KEY`
- `VISION_OCR_*` (optional, for handwritten OCR)

Run the app:
```
uvicorn app.main:app --reload --host 0.0.0.0 --port 5050
```

## Project Layout
- `app/main.py` is the FastAPI entry point.
- `app/routers/` contains API and template routes.
- `app/core/` holds settings, auth helpers, and template utilities.
- `app/py_lib/` contains shared libs (DB, file ops, models).

## OCR Workflow (Handwritten)
- Submissions are cropped into per-answer images.
- Each crop is sent to a vision OCR endpoint (Qwen or another model).
- OCR text and confidence are stored alongside the answer metadata.

## API
See `app/routers/` for current endpoints. The legacy list below may not be exhaustive after the FastAPI migration.

### /api/v1.0/assignments

This endpoint returns all assignments in the database. The endpoint takes the following optional query parameters:

* `user_id` - The id of the user to filter by
* `course_id` - The id of the course to filter by

### /api/v1.0/assignments/<int:assignment_id>

This endpoint returns a single assignment with the given id.

### /api/v1.0/assignments/<int:assignment_id>/submissions

This endpoint returns all submissions for a given assignment. The endpoint takes the following optional query parameters:

* `user_id` - The id of the user to filter by

### /api/v1.0/assignments/<int:assignment_id>/submissions/<int:submission_id>

This endpoint returns a single submission for a given assignment.

### /api/v1.0/assignments/<int:assignment_id>/submissions/<int:submission_id>/results

This endpoint returns the result for a given submission.

### /api/v1.0/courses

This endpoint returns all courses in the database. The endpoint takes the following optional query parameters:

* `user_id` - The id of the user to filter by

### /api/v1.0/courses/<int:course_id>

This endpoint returns a single course with the given id.

### /api/v1.0/courses/<int:course_id>/assignments

This endpoint returns all assignments for a given course.

### /api/v1.0/courses/<int:course_id>/users

This endpoint returns all users for a given course.

### /api/v1.0/users

This endpoint returns all users in the database. The endpoint takes the following optional query parameters:

* `course_id` - The id of the course to filter by

### /api/v1.0/users/<int:user_id>

This endpoint returns a single user with the given id.

### /api/v1.0/users/<int:user_id>/courses

This endpoint returns all courses for a given user.

### /api/v1.0/users/<int:user_id>/assignments

This endpoint returns all assignments for a given user
