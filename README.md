# Dead-Man-Switch-API

## Overview
The **Dead Man’s Switch API** is a Django-based application that allows users to schedule secure messages or actions (like sending an email or triggering a webhook) if they fail to check in within a defined time frame. It's perfect for digital legacy, emergency protocols, or personal security.

This app uses:
- **Django 5.x**
- **Django REST Framework**
- **Celery + Redis** for scheduled checks
- **Token Authentication** for secure access

---

## Features

- User Registration & Login  
- Token-based Authentication  
- Create and manage switches with inactivity timers  
- Trigger email/webhook actions when inactive  
- Manual check-ins to reset the timer  
- Status summaries  
- Celery task for hourly/daily checks  

---

## Installation

Clone the repository:

```bash
git https://github.com/Just-Mike4/Dead-Man-Switch-API.git
cd Dead-Man-Switch-API
```

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Apply the database migrations:

```bash
python manage.py migrate
```

Run the development server:

```bash
python manage.py runserver
```

Set up Redis and Celery:

```bash
# Start Redis
redis-server

# In another terminal, start Celery worker
celery -A dms.celery_app worker --loglevel=info
celery -A dms.celery_app beat --loglevel=info
```

---

## API Endpoints  
> **Note:** All endpoints require authentication via Token unless otherwise stated.

### User Registration
**URL:** `/api/register/`  
**Method:** `POST`  
**Request Body:**
```json
{
  "username": "john",
  "email": "john@example.com",
  "password": "securepassword123"
}
```
**Response:**
```json
{
  "username": "john",
  "email": "john@example.com",
  "token": "d65b24fe38a0456a8c..."
}
```

---

### User Login  
**URL:** `/api/login/`  
**Method:** `POST`  
**Request Body:**
```json
{
  "username": "john",
  "password": "securepassword123"
}
```
**Response:**
```json
{
  "token": "d65b24fe38a0456a8c..."
}
```

---

### Create a Dead Man’s Switch  
**URL:** `/api/switches/`  
**Method:** `POST`  
**Request Body:**
```json
{
  "title": "My Secret Note",
  "message": "If you're reading this, it's too late.",
  "inactivity_duration_days": 3,
  "action_type": "email",
  "action_target": "emergency@example.com"
}
```
**Response:**
```json
{
  "title": "My Secret Note",
  "status": "active",
  "last_checkin": null,
  "next_trigger_date": "2025-04-25T00:00:00Z"
}
```

---

### List Switches  
**URL:** `/api/switches/`  
**Method:** `GET`  
**Response:**
```json
[
  {
    "id": 1,
    "title": "My Secret Note",
    "status": "active",
    "last_checkin": "2025-04-20T00:00:00Z",
    "next_trigger_date": "2025-04-25T00:00:00Z"
  }
]
```

---

### Retrieve a Switch  
**URL:** `/api/switches/{id}/`  
**Method:** `GET`

---

### Update a Switch  
**URL:** `/api/switches/{id}/`  
**Method:** `PATCH`

---

### Delete a Switch  
**URL:** `/api/switches/{id}/`  
**Method:** `DELETE`

---

### Check-In to Reset Timer  
**URL:** `/api/switches/{id}/checkin/`  
**Method:** `POST`  
**Response:**
```json
{
  "message": "Check-in successful. Next trigger reset."
}
```

---

### List Available Actions  
**URL:** `/api/actions/`  
**Method:** `GET`  
**Response:**
```json
[
  {
    "type": "email",
    "description": "Send an email to a specified address"
  },
  {
    "type": "webhook",
    "description": "Trigger a webhook URL"
  }
]
```

---

### Test a Webhook  
**URL:** `/api/webhook-test/`  
**Method:** `POST`  
**Request Body:**
```json
{
  "url": "https://webhook.site/example",
  "payload": {
    "test": "true"
  }
}
```

---

### Switch Stats Summary  
**URL:** `/api/my-status/`  
**Method:** `GET`  
**Response:**
```json
{
  "active_switches": 2,
  "triggered_switches": 1,
  "last_checkin": "2025-04-20T14:05:23Z"
}
```

---

## Scheduled Trigger Logic (via Celery)
A periodic background task runs every hour/day to:

- Check switches whose `last_checkin + inactivity_duration_days < now`
- Trigger their assigned action
- Mark the switch as `triggered`

---

## Permissions
- Users can only view/edit their own switches.
- Triggered switches become locked from updates.
- Auth required for all switch-related actions.

---
