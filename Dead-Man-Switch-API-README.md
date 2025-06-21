# Dead Man's Switch (DMS) API

## Project Title
Dead Man's Switch (DMS) API

## Short Description
The Dead Man's Switch (DMS) API is a robust Django-based web application designed to automatically trigger predefined actions if a user fails to check in within a specified period of inactivity. This system ensures that critical information or actions are executed in the event of prolonged user absence. It features user authentication, comprehensive switch management, and background task processing for automated action triggering.

## Features Overview

*   **User Authentication & Management**: Secure user registration, login, and robust password reset functionalities powered by JWT (JSON Web Tokens).
*   **Dead Man's Switch Management**: Users can create, view, update, and delete their "switches," configuring an inactivity duration and an associated action.
*   **Automated Action Triggering**: If a user fails to "check-in" with their switch within the set inactivity period, the system automatically triggers a pre-defined action.
*   **Multiple Action Types**: Supports various actions upon trigger, including sending an email to a specified recipient or hitting a webhook URL.
*   **Periodic Background Tasks**: Utilizes Celery and `django-celery-beat` to periodically monitor all active switches and execute triggers when conditions are met.
*   **User Activity Monitoring**: Provides an endpoint for users to check the status of their switches and their last overall check-in time.
*   **Webhook Testing Utility**: An API endpoint to test the reachability and response of a webhook URL.
*   **RESTful API**: Built with Django REST Framework, offering a clean and intuitive API for integration.
*   **Scalable Architecture**: Leverages Redis as a message broker for efficient background task management.

## Installation Instructions

To set up the Dead Man's Switch API locally, follow these steps:

### Prerequisites

*   Python 3.8+
*   MySQL Server (or compatible database)
*   Redis Server

### Setup Steps

1.  **Clone the Repository**:
    ```bash
    git clone <repository_url>
    cd dms_project_root
    ```
    (Replace `<repository_url>` with the actual repository URL.)

2.  **Create and Activate a Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**:
    Create a `.env` file in the project's root directory (next to `manage.py`) and populate it with your database and email credentials.

    ```dotenv
    # Database Configuration
    DB_NAME=dms_db
    DB_USER=root
    DB_PASSWORD=your_db_password

    # Email Configuration (for password resets and email actions)
    EMAIL_HOST=smtp.gmail.com
    EMAIL_PORT=465
    EMAIL_HOST_USER=your_email@gmail.com
    EMAIL_HOST_PASSWORD=your_email_app_password
    ```
    *Note*: For `EMAIL_HOST_PASSWORD`, if using Gmail, you'll need to generate an App Password.

5.  **Database Setup**:
    *   Ensure your MySQL server is running.
    *   Create a database named `dms_db` (or whatever you set `DB_NAME` to in `.env`).
    *   Run Django migrations to create the necessary database tables:
        ```bash
        python manage.py makemigrations
        python manage.py migrate
        ```

6.  **Create a Superuser (Optional but Recommended)**:
    This allows access to the Django Admin panel.
    ```bash
    python manage.py createsuperuser
    ```
    Follow the prompts to create your superuser account.

7.  **Start Redis Server**:
    Ensure your Redis server is running. The application uses it as a Celery broker and backend.
    ```bash
    redis-server
    ```
    (Or start it as a service/daemon depending on your OS setup).

8.  **Start Celery Worker**:
    In a *separate terminal*, navigate to the project root and start the Celery worker.
    ```bash
    celery -A dms worker -l info
    ```

9.  **Start Celery Beat Scheduler**:
    In *another separate terminal*, navigate to the project root and start Celery Beat. This schedules the periodic tasks (e.g., hourly switch checks).
    ```bash
    celery -A dms beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    ```

10. **Run the Django Development Server**:
    Finally, in your *main terminal*, start the Django development server.
    ```bash
    python manage.py runserver
    ```
    The API will now be accessible at `http://127.0.0.1:8000/api/`.

## Usage Examples

The API provides endpoints for user authentication, managing dead man's switches, and utility functions. All API endpoints are prefixed with `/api/`.

### User Authentication

*   **Register**: Send a `POST` request to `/api/register/` with `username`, `email`, and `password` to create a new user and receive a JWT access token.
*   **Login**: Send a `POST` request to `/api/login/` with `email` and `password` to authenticate and obtain a JWT access token.
*   **Password Reset**:
    *   Initiate a reset with a `POST` request to `/api/password-reset/` providing the user's `email`. A reset link will be sent to the email.
    *   Confirm the reset with a `POST` request to `/api/password-reset-confirm/<uid>/<token>/` including the `new_password` in the body, using the `uid` and `token` from the reset link.

**Authentication for Protected Endpoints**:
Once you have an access token, include it in the `Authorization` header for all protected requests: `Authorization: Bearer YOUR_ACCESS_TOKEN`.

### Switch Management

*   **List/Create Switches**: Send a `GET` request to `/api/switches/` to retrieve all switches for the authenticated user, or a `POST` request to create a new switch. When creating, provide `title`, `message`, `inactivity_duration_days`, `action_type` (e.g., "email" or "webhook"), and `action_target` (e.g., an email address or URL).
*   **Retrieve/Update/Delete a Switch**: Send `GET`, `PATCH`, or `DELETE` requests to `/api/switches/<id>/` for a specific switch.
*   **Check-in**: To reset the inactivity timer for a specific switch, send a `POST` request to `/api/switches/<id>/checkin/`. This updates `last_checkin` and postpones the `next_trigger_date`.

### Utility Endpoints

*   **Get User Status**: Send a `GET` request to `/api/my-status/` to view a summary of your active and triggered switches, along with your most recent check-in time across all switches.
*   **List Action Types**: Send a `GET` request to `/api/actions/` to see available action types (e.g., "email", "webhook") and their descriptions.
*   **Test Webhook**: Send a `POST` request to `/api/webhook-test/` with a `url` in the body to test if a webhook endpoint is reachable and responds.

## File Structure Summary

The project follows a standard Django application structure with distinct apps for `user` and `switch` functionalities.

*   **`dms/`**: The main Django project directory.
    *   `settings.py`: Django project settings, including database configuration, installed apps, JWT settings, Celery configuration, and email settings.
    *   `urls.py`: Main URL routing for the entire project, including API endpoints from `user` and `switch` apps.
    *   `celery_app.py`: Celery application setup, defining the main Celery instance and periodic tasks.
*   **`user/`**: Django app for user management.
    *   `views.py`: API views for user registration, login, and password reset.
    *   `serializers.py`: Data serializers for user and authentication related operations.
    *   `forms.py`: Django forms used for user validation during registration.
*   **`switch/`**: Django app for Dead Man's Switch functionality.
    *   `models.py`: Defines database models for `Switch`, `Action`, and `CheckIn`.
    *   `views.py`: API views for managing switches, handling check-ins, listing action types, and providing user status.
    *   `serializers.py`: Data serializers for switch and action-related operations.
    *   `tasks.py`: Celery tasks for periodically checking and triggering switches, handling email sending and webhook calls.
*   **`celery_timer.py`**: A script (likely for initial setup or management) that demonstrates how to programmatically create `django-celery-beat` periodic tasks.
*   **`requirements.txt`**: Lists all Python dependencies required for the project.
*   **`manage.py`**: Django's command-line utility for administrative tasks.
*   **`test_apis.py`**: Contains comprehensive API tests for user authentication and switch management.

## Important Notes

*   **Environment Variables**: Sensitive information like database credentials and email server details are loaded from a `.env` file for security. Ensure this file is not committed to version control.
*   **JWT Token Lifetime**: Access tokens obtained via login or registration are valid for 3 days. There is no refresh token mechanism exposed via the API, so users will need to re-authenticate after token expiration.
*   **Background Tasks**: Celery worker and Celery Beat must be running concurrently with the Django server for the Dead Man's Switch functionality (periodic checks and action triggering) to operate correctly.
*   **CORS**: The API is configured to allow all CORS origins (`CORS_ALLOW_ALL_ORIGINS = True`), which is suitable for development but should be restricted in production environments for security.
*   **Timezone**: The application's timezone is set to `Africa/lagos` in `settings.py`. Ensure this aligns with your operational requirements or adjust as needed.