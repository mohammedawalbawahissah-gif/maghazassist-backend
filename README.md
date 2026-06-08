# MAGHAZ Assist — Backend

Django REST Framework backend for the MAGHAZ Assist Integrated Management System.

## Stack
- Python 3.12 / Django 5.0 / Django REST Framework
- PostgreSQL
- Celery + Redis (background tasks & notifications)
- JWT Authentication (SimpleJWT)

## Apps
| App | Purpose |
|---|---|
| `core` | Organisation, User, RBAC, shared models |
| `authentication` | JWT login/logout, password management |
| `hospitality` | Rooms, reservations, guests, housekeeping |
| `real_estate` | Properties, tenants, leases, rent |
| `construction` | Projects, tasks, procurement, contractors |
| `hr` | Employees, payroll, attendance, performance |
| `finance` | Ledger, invoices, payments, budgets |
| `maintenance` | Requests, assignments, asset service |
| `transport` | Fleet, drivers, trips, dispatch |
| `notifications` | Multi-channel: in-app, email, SMS, push, WhatsApp |
| `documents` | File storage, versioning, approvals |
| `audit` | Immutable system-wide event log |
| `reporting` | Executive dashboards and analytics |

## Quick Start (Windows PowerShell)

```powershell
# 1. Clone and enter the directory
cd maghazassist-backend

# 2. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and configure environment
copy .env.example .env
# Edit .env with your DB credentials

# 5. Run migrations
python manage.py migrate

# 6. Seed development data (creates org + all 15 role users)
python manage.py setup_dev

# 7. Start the dev server
python manage.py runserver

# 8. In a separate terminal, start Celery worker
celery -A config worker --loglevel=info -P solo
```

## API Base URL
```
http://localhost:8000/api/v1/
```

## Key Endpoints
| Endpoint | Description |
|---|---|
| `POST /api/v1/auth/login/` | Obtain JWT access + refresh tokens |
| `POST /api/v1/auth/logout/` | Blacklist refresh token |
| `POST /api/v1/auth/token/refresh/` | Refresh access token |
| `GET /api/v1/core/users/me/` | Current user profile |
| `GET /api/v1/notifications/` | User notifications |
| `GET /api/v1/audit/logs/` | Audit log (admin only) |

## Dev Seed Users
All passwords: `Test1234!`

| Email | Role |
|---|---|
| admin@maghazassist.com | System Administrator |
| executive@maghazassist.com | Executive |
| hotel@maghazassist.com | Hotel Manager |
| frontdesk@maghazassist.com | Front Desk |
| property@maghazassist.com | Property Manager |
| construction@maghazassist.com | Construction PM |
| hr@maghazassist.com | HR Manager |
| finance@maghazassist.com | Finance Officer |
| dispatch@maghazassist.com | Transport Dispatcher |
| driver@maghazassist.com | Internal Driver |
| 3pdriver@maghazassist.com | Third-Party Driver |
| tenant@maghazassist.com | Tenant (Portal) |
| guest@maghazassist.com | Guest (Portal) |

## Django Settings
Set `DJANGO_SETTINGS_MODULE` to:
- `config.settings.development` (default)
- `config.settings.production`
