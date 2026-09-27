# Go-Green Shuttle Service 🚐🌱

A full-stack shuttle booking and ride-management web application built with Flask and PostgreSQL.

Passengers can create accounts and request rides, users can apply to become drivers, administrators can review driver applications and manage customers, and approved drivers can accept, start and complete trips.

## 🌐 Live Demo

The application is deployed on Render:

https://go-green-shuttle-service-xmxj.onrender.com/

> The hosted service may take a short time to start after a period of inactivity.

## What the project demonstrates

- Passenger registration, login and session authentication
- Ride requests with passenger count, fare estimate and payment preference
- Ride lifecycle: `requested → accepted → in_progress → completed`
- Driver applications with admin approval/decline workflow
- Approved-driver dashboard with available and assigned trips
- Passenger ride history and cancellation
- Admin dashboard with live database statistics
- Customer block/unblock controls
- PostgreSQL production database
- bcrypt password hashing
- Environment-based secrets and configuration
- Gunicorn production server
- Deployment on Render
- Responsive Flask/Jinja2 interface

## Tech stack

**Backend:** Python, Flask, bcrypt  
**Frontend:** HTML, Jinja2, CSS  
**Database:** PostgreSQL (production), SQLite-compatible local development  
**Production server:** Gunicorn  
**Deployment:** Render  
**Version control:** Git & GitHub

## Quick start

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/MlungisiMnembe/GO-GREEN-Shuttle-Service.git
cd GO-GREEN-Shuttle-Service
python -m venv .venv
```

### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create your local environment configuration from `.env.example`.

Configure your own secure values for the required environment variables. Never commit your `.env` file.

Then start the application:

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Environment configuration

The application uses environment variables for sensitive configuration.

Use `.env.example` as the template for local development.

Important:

- Never commit `.env`
- Use a strong, unique `SECRET_KEY`
- Use private administrator credentials
- Configure `DATABASE_URL` when connecting to PostgreSQL
- Production secrets are configured through the hosting environment

## Application workflow

### Passenger

1. Create an account.
2. Log in.
3. Request a shuttle ride.
4. Select passenger count and payment preference.
5. View current and previous rides.
6. Cancel eligible ride requests.
7. Track the ride through its lifecycle.

### Driver

1. Create an account.
2. Submit a driver application.
3. Wait for administrator approval.
4. Open the Driver dashboard after approval.
5. View available rides.
6. Accept a ride.
7. Start the assigned trip.
8. Complete the trip.

### Administrator

1. Log in using securely configured administrator credentials.
2. Review pending driver applications.
3. Approve or decline applications.
4. View registered customers.
5. Block or unblock customer access.
6. View approved drivers.
7. Monitor ride statistics.
8. Monitor completed ride value.

## End-to-end test

The deployed application has been tested through the complete workflow:

1. Passenger account creation and login
2. Ride request creation
3. Driver account and application
4. Administrator approval
5. Driver login and ride acceptance
6. Ride start and completion
7. Passenger ride-history verification
8. Administrator statistics verification

This confirms the core application workflow operates against the deployed PostgreSQL database.

## Project structure

```text
GO-GREEN-Shuttle-Service/
├── app.py
├── database.py
├── requirements.txt
├── .python-version
├── .env.example
├── .gitignore
├── README.md
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

## Database

The deployed application uses PostgreSQL for persistent production data.

The database layer supports the application's:

- User accounts
- Driver applications
- Ride requests
- Ride status lifecycle
- Administrative statistics
- Customer access controls

The project was originally developed with SQLite and was subsequently migrated to PostgreSQL for deployment.

## Deployment

The production application is hosted on Render.

Production stack:

```text
Browser
   ↓
Render Web Service
   ↓
Gunicorn
   ↓
Flask Application
   ↓
PostgreSQL
```

Render automatically deploys updates from the repository when changes are pushed to the configured branch.

## Security

The project includes several basic security practices:

- Passwords are hashed using bcrypt
- Application secrets are stored in environment variables
- `.env` is excluded from version control
- Production administrator credentials are not stored in the repository
- Database credentials are supplied through environment configuration
- Session-based authentication protects restricted application areas

## Notes

The fare calculation currently uses a transparent demonstration formula:

```text
R45 + R20 per passenger
```

This allows the booking workflow to operate without requiring paid mapping or geocoding services.

Card payment is currently represented as a payment preference for demonstration purposes. No real payment processor is connected.

## Future enhancements

Possible future improvements include:

- Google Maps or Mapbox routing
- Distance-based fare calculation
- Live driver location tracking
- Real online payment processing
- Email/SMS notifications
- CSRF protection
- Formal database migrations
- Automated unit and integration tests
- CI/CD testing with GitHub Actions
- Improved role-based access control
- REST API endpoints
- Mobile-friendly Progressive Web App functionality

---

Built as a practical full-stack Flask portfolio project using Python, Flask, PostgreSQL and Render.
