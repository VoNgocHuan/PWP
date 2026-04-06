# PWP SPRING 2026
# PROJECT NAME
# Group information
* Student 1. Niklas Raesalmi, nraesalm22@student.oulu.fi
* Student 2. Huan Vo, hvo22@student.oulu.fi
* Student 3. Niranjan Sreegith, nsreegit22@student.oulu.fi
* Student 4. MD. Nur-E Ferdaus, mferdaus25@student.oulu.fi


__Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint, instructions on how to setup and run the client, instructions on how to setup and run the axiliary service and instructions on how to deploy the api in a production environment__

## Tech stack 

- Python 
- Flask
- Flask-RESTful
- Flask-SQLAlchemy
- SQLAlchemy
- jsonschema

Testing:
- pytest
- pytest-cov
- pylint
- SQLAlchemy
- Werkzeug

All Python dependencies are encoded in:
- `requirements.txt`
- `pyproject.toml`

## Database

Database used: SQLite
SQLite version: 3.50.4 

DB located in:
- `instance/development.db`

## Instructions
### Installing deps (pick one of 2):
### a/ install from requirement:
pip install -r requirements.txt

### b/ plan for change from requirement.txt to pyproject/toml:
###    Delete requirements.txt (just for there to be no conflicts)
Run pip install -e .

### run the app 
You can start the app by pasting this command in the venv:
flask --app=ticketing --debug run

### populate db
The populated DB exists in the /instace folder as 'developments.db' in addition to the sql dump.

### How to run tests

Run tests and coverage:
pytest --cov=ticketing --cov-report=term-missing --cov-report=html

Coverage HTML report will be generated in 'htmlcov/'.

Also linting the code can be done using this command:
pylint ticketing --disable=no-member,import-outside-toplevel,no-self-use