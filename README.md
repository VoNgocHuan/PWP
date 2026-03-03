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
- jsonschema

Testing:
- pytest
- pytest-cov
- pylint

All Python dependencies are encoded in:
- `requirements.txt`

## Database

Database used: SQLite
SQLite version: 3.50.4 

DB located in:
- `instance/development.db`

## Instructions
### Installing deps:
pip install -r requirements.txt

You can start the app by pasting this command in the venv:
flask --app=ticketing --debug run

The populated DB exists in the /instace folder as 'developments.db' in addition to the sql dump.

