# Go-Green Shuttle Service 🚐🌱

A complete Flask portfolio project for managing local shuttle rides. Passengers can create accounts and request rides, users can apply to become drivers, administrators approve driver applications, and approved drivers can accept and complete trips.

## What the project demonstrates

- Passenger registration, login and session authentication
- Ride requests with passenger count, fare estimate and payment preference
- Ride lifecycle: `requested → accepted → in_progress → completed`
- Driver applications with admin approval/decline workflow
- Approved-driver dashboard with available and assigned trips
- Passenger ride history and cancellation
- Admin dashboard using real database statistics
- Customer block/unblock controls
- SQLite persistence, bcrypt password hashing and environment-based secrets
- Responsive, modern Flask/Jinja interface

## Tech stack

**Backend:** Python, Flask, SQLite, bcrypt  
**Frontend:** HTML, Jinja2, CSS  
**Database:** SQLite

## Quick start

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

### Admin login for local demo

By default the local development fallback is:

- Email: `admin@shuttle.com`
- Password: `admin@123`

For anything beyond a local demo, create environment variables from `.env.example` and use your own strong values. Never commit `.env`.

## End-to-end test

1. Create a passenger account and request a ride.
2. Create a second account and submit a driver application.
3. Log in as Admin and approve that driver.
4. Log in as the approved driver, open **Driver**, and accept the passenger's ride.
5. Start and then complete the ride.
6. Log back in as the passenger and confirm the completed trip appears in ride history.
7. Open Admin to see real ride, driver and completed-value statistics.

## Project structure

```text
GO-GREEN-Shuttle-Service/
├── app.py
├── database.py
├── requirements.txt
├── .env.example
├── static/
│   └── base-style.css
└── templates/
    ├── base.html
    ├── index.html
    ├── login.html
    ├── signup.html
    ├── user_dashboard.html
    ├── driver_dashboard.html
    ├── ride_request.html
    ├── admin.html
    └── pending_requests.html
```

## Notes

The fare calculation is intentionally a transparent demo formula (`R45 + R20 per passenger`) so the repository runs without paid mapping/geocoding credentials. The earlier broken Google Maps dependency has been removed from the core booking flow. Card payment is represented as a demo payment preference; no real payment processor is connected.

## Future enhancements

Possible production extensions include Google Maps/Mapbox routing, live driver location, real payment processing, notifications, CSRF protection, database migrations, automated tests and deployment with PostgreSQL.

---
Built as a practical full-stack Flask portfolio project.
