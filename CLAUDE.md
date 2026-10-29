# trip-signup
Flask app where students register interest in a study abroad trip.

## Commands
- Env: Pipenv. Prefix every Python tool with `pipenv run`; never use bare pip.
- Run: pipenv run flask run --debug   (open http://127.0.0.1:5000)
- Test: pipenv run pytest -q

## Rules
- Add or update a test for every change. Run the tests before saying it's done.
- Database: SQLite in signups.db via the built-in sqlite3 module. No ORM.
- SQL: parameterized queries only (?), never f-strings or string concatenation.
- Never print or log applicant emails.
- Plain HTML templates and CSS. No JavaScript frameworks.
- Add packages with pipenv install (test tools: --dev). Ask before adding one.

## Secrets and data
- ADMIN_PASSWORD comes from .env, which pipenv run loads. Never hard-code it.
- Never commit .env or signups.db. Do commit Pipfile and Pipfile.lock.
- Tests use a temporary database, never signups.db.
