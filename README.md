# Social network api

Social network message viewing system

## Creating a virtual environment

```
python -m venv venv
venv\scripts\activate
```

## Installing dependencies

```
pip install -r requirements.txt
pip freeze > requirements.txt
```

## Running the application
```
uvicorn app.main:app --reload
```