# capstone-1-project

## How to setup dev env?
- Make sure you are in the respective directories before running the commands

#### Backend
- `uv sync` to install dependencies for the backend
  - Make sure you create a venv first.
- Copy the `.env.template` file to `.env` and fill in the required values
- Run the command `fastapi dev backend/main.py` from the repo's root directory to run the dev webserver
- Run the celery worker using this command: `celery -A backend.celery_app worker --loglevel=info`

#### Frontend
- `npm install` to install dependencies for the frontend