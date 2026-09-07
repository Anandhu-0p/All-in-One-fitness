# All-in-One Fitness

A Django fitness and wellness platform for members, trainers, experts, and administrators.

## Features

- Role-based dashboards for administrators, trainers, experts, and users
- User profiles, health records, progress measurements, attendance, events, payments, alerts, feedback, notifications, and private chat
- Trainer workout plans and member assignments
- Expert diet plans, meals, videos, and wellness tips
- Bootstrap 5 responsive templates
- REST endpoints for notifications, events, progress, payments, workouts, diets, attendance, chat messages, videos, tips, and dashboard summaries

## Requirements

- Python 3.11 or newer
- MySQL 8 for production, or SQLite for local development
- Node.js is not required for the current frontend

## Local setup

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Environment variables

The project loads `.env` from the repository root. See `.env.example`.

- `DJANGO_SECRET_KEY`: required long random production secret
- `DEBUG`: use `True` only for local development
- `ALLOWED_HOSTS`: comma-separated hostnames
- `DB_USER`: leave empty for SQLite; set it to use MySQL
- `DB_NAME`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: MySQL connection values
- `EMAIL_BACKEND`: console backend is suitable for local password-reset testing
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`
- `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`
- `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD`

For production, use a real email backend and never commit `.env`.

## Database and migrations

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations
```

For MySQL, create the database first, then set the `DB_*` variables in `.env` and run `migrate`.

## Demo accounts

Run `python manage.py seed_demo_data` to create or refresh the demo accounts.

| Role | Email | Username | Password |
| --- | --- | --- | --- |
| Administrator | admin@example.com | admin | Fitness@123 |
| Trainer | trainer@example.com | trainer | Fitness@123 |
| Expert | expert@example.com | expert | Fitness@123 |
| User | user@example.com | user | Fitness@123 |

Login accepts either username or email. Demo passwords must be changed before deployment.

To reset seeded demo data:

```powershell
python manage.py seed_demo_data --reset
```

## Tests and checks

```powershell
python manage.py check
python manage.py check --deploy
python manage.py test
```

Run one area while developing:

```powershell
python manage.py test accounts.tests.TrainerWorkflowTests
```

The test suite includes registration, login, role access, profile and upload validation, trainer workflows, expert content, events, payments, chat, notifications, and dashboards.

## Password reset

Password reset routes are available at `/reset-password/`. With the default console email backend, reset messages are printed in the terminal. Configure SMTP environment variables for real delivery.

## Deployment example: Render

1. Create a managed MySQL database and a Render web service.
2. Set the production environment variables in the Render dashboard.
3. Install dependencies with `pip install -r requirements.txt`.
4. Run migrations as a release command: `python manage.py migrate`.
5. Collect static files: `python manage.py collectstatic --noinput`.
6. Start the service with:

```text
python -m gunicorn all_in_one_fitness.wsgi:application
```

7. Set `DEBUG=False`, use a generated `DJANGO_SECRET_KEY`, configure `ALLOWED_HOSTS`, enable HTTPS security variables, and configure SMTP.
8. Run `python manage.py seed_demo_data` only for a non-production demo environment.

Serve uploaded media from durable object storage in production rather than the local filesystem.

## Security checklist

- Use a long random `DJANGO_SECRET_KEY`.
- Set `DEBUG=False`.
- Restrict `ALLOWED_HOSTS` to the deployed domains.
- Enable HTTPS, secure cookies, HSTS, and SSL redirect behind the production proxy.
- Use a real email provider and keep credentials in environment variables.
- Review admin and object-level permissions before launch.
- Restrict upload size, extension, MIME type, and file content.
- Back up MySQL and protect health data.
- Change or remove all demo passwords.
- Run `python manage.py check --deploy` before release.

Fitness and nutrition content is educational and does not replace professional medical advice.

## User acceptance checklist

- [ ] A new user can register, log in with username or email, log out, and reset a password.
- [ ] Each role reaches only its own dashboard and protected pages.
- [ ] A user can update profile and health data and view only their own private records.
- [ ] A trainer can manage assigned batches, plans, attendance, health records, and progress.
- [ ] An expert can manage only their own diet plans, videos, and wellness tips.
- [ ] An administrator can manage users, staff, batches, events, plans, payments, alerts, feedback, and logs.
- [ ] Duplicate batch membership and event registration are rejected.
- [ ] Notifications appear after assignments and payment alerts.
- [ ] Chat messages and allowed attachments work for authorized participants only.
- [ ] Payments, reports, charts, pagination, search, and filters render correctly.
- [ ] Forms reject invalid files, invalid dates, invalid emails, and invalid amounts.
- [ ] The application works at desktop, tablet, and mobile widths.
- [ ] Production checks, migrations, static files, email, backups, and HTTPS have been verified.
