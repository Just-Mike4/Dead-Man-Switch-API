# Dead Man's Switch (DMS) API Documentation

This document provides comprehensive API documentation for the Dead Man's Switch (DMS) system. The DMS is a Django-based application designed to trigger predefined actions if a user fails to check in within a specified period, ensuring critical information or actions are taken in the event of prolonged inactivity.

The API is built using Django REST Framework and uses JWT for authentication, with Celery handling background tasks like switch triggering.

## Table of Contents

1.  [Introduction](#1-introduction)
2.  [Authentication](#2-authentication)
    *   [JWT Token Lifetime](#jwt-token-lifetime)
3.  [API Endpoints](#3-api-endpoints)
    *   [User Authentication & Management](#user-authentication--management)
        *   [Register a New User](#register-a-new-user)
        *   [Log In User](#log-in-user)
        *   [Initiate Password Reset](#initiate-password-reset)
        *   [Confirm Password Reset](#confirm-password-reset)
    *   [Switch Management](#switch-management)
        *   [List User's Switches](#list-users-switches)
        *   [Create a New Switch](#create-a-new-switch)
        *   [Retrieve a Specific Switch](#retrieve-a-specific-switch)
        *   [Partially Update a Switch](#partially-update-a-switch)
        *   [Delete a Switch](#delete-a-switch)
        *   [Check-in for a Switch](#check-in-for-a-switch)
    *   [Action Types](#action-types)
        *   [List Available Action Types](#list-available-action-types)
    *   [Utility Endpoints](#utility-endpoints)
        *   [Test a Webhook URL](#test-a-webhook-url)
        *   [Get Authenticated User Status](#get-authenticated-user-status)
4.  [Error Codes](#4-error-codes)
5.  [Rate Limiting](#5-rate-limiting)
6.  [Sample Usage](#6-sample-usage)

## 1. Introduction

The DMS system provides a robust API for managing user accounts and configuring "Dead Man's Switches." A switch, once configured, monitors user activity (specifically, check-ins). If the user fails to check in within a pre-defined `inactivity_duration_days`, the switch is "triggered," and an associated action (e.g., sending an email, hitting a webhook) is executed. Background tasks, managed by Celery, periodically check the status of all active switches and trigger those that have become overdue.

## 2. Authentication

The primary authentication mechanism for this API is JSON Web Token (JWT) authentication, powered by `djangorestframework-simplejwt`.

**Authentication Flow:**

1.  **Obtain Token**: Users register via `/api/register/` (which returns a token upon success) or log in via `/api/login/` to obtain an access token.
2.  **Use Token**: For subsequent authenticated requests, include the obtained access token in the `Authorization` header of your HTTP requests in the `Bearer` scheme.

    `Authorization: Bearer <YOUR_ACCESS_TOKEN>`

    **Example Header:**
    `Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjg1MTc5ODc3LCJpYXQiOjE2ODQ5MjA2NzcsImp0aSI6ImZhMzI0ZDg0YzA1MjQyMTc4Zjg3ZWI0NDM1NzVjNjUyIiwidXNlcl9pZCI6MX0.S0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0`

### JWT Token Lifetime

Access tokens are configured to expire after **3 days**. There is no explicit refresh token mechanism exposed via the API, so users will need to re-authenticate after their token expires.

## 3. API Endpoints

All API endpoints are prefixed with `/api/`.

---

### User Authentication & Management

These endpoints handle user registration, login, and password management.

#### Register a New User

*   **HTTP Method**: `POST`
*   **Path**: `/api/register/`
*   **Description**: Creates a new user account and returns an access token for immediate use.
*   **Authentication**: `AllowAny`
*   **Parameters (Body)**:

    | Parameter  | Type     | Required | Description                |
    | :--------- | :------- | :------- | :------------------------- |
    | `username` | `string` | Yes      | A unique username.         |
    | `email`    | `string` | Yes      | A unique and valid email.  |
    | `password` | `string` | Yes      | User's chosen password.    |

*   **Request Example**:

    ```json
    {
        "username": "api_user",
        "email": "api.user@example.com",
        "password": "securepassword123"
    }
    ```

*   **Success Response (201 Created)**:

    ```json
    {
        "username": "api_user",
        "email": "api.user@example.com",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjg1MTc5ODc3LCJpYXQiOjE2ODQ5MjA2NzcsImp0aSI6ImZhMzI0ZDg0YzA1MjQyMTc4Zjg3ZWI0NDM1NzVjNjUyIiwidXNlcl9pZCI6MX0.S0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0"
    }
    ```

*   **Error Response (400 Bad Request)**:

    ```json
    {
        "email": ["user with this email already exists."],
        "password": ["This password is too common."]
    }
    ```

#### Log In User

*   **HTTP Method**: `POST`
*   **Path**: `/api/login/`
*   **Description**: Authenticates an existing user and returns an access token.
*   **Authentication**: `AllowAny`
*   **Parameters (Body)**:

    | Parameter  | Type     | Required | Description                       |
    | :--------- | :------- | :------- | :-------------------------------- |
    | `email`    | `string` | Yes      | The user's registered email.      |
    | `password` | `string` | Yes      | The user's password.              |

*   **Request Example**:

    ```json
    {
        "email": "api.user@example.com",
        "password": "securepassword123"
    }
    ```

*   **Success Response (200 OK)**:

    ```json
    {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjg1MTc5ODc3LCJpYXQiOjE2ODQ5MjA2NzcsImp0aSI6ImZhMzI0ZDg0YzA1MjQyMTc4Zjg3ZWI0NDM1NzVjNjUyIiwidXNlcl9pZCI6MX0.S0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0"
    }
    ```

*   **Error Response (400 Bad Request)**:

    ```json
    {
        "detail": "No active account found with the given credentials"
    }
    ```

#### Initiate Password Reset

*   **HTTP Method**: `POST`
*   **Path**: `/api/password-reset/`
*   **Description**: Sends a password reset email to the specified email address.
*   **Authentication**: `AllowAny`
*   **Parameters (Body)**:

    | Parameter | Type     | Required | Description                                    |
    | :-------- | :------- | :------- | :--------------------------------------------- |
    | `email`   | `string` | Yes      | The email address associated with the account. |

*   **Request Example**:

    ```json
    {
        "email": "user@example.com"
    }
    ```

*   **Success Response (200 OK)**:

    ```json
    {
        "detail": "Password reset email has been sent."
    }
    ```

*   **Error Response (400 Bad Request)**:

    ```json
    {
        "email": ["Enter a valid email address."]
    }
    ```

#### Confirm Password Reset

*   **HTTP Method**: `POST`
*   **Path**: `/api/password-reset-confirm/<uid>/<token>/`
*   **Description**: Confirms the password reset process using the `uid` and `token` from the reset link and sets a new password.
*   **Authentication**: `AllowAny`
*   **Parameters (Path)**:

    | Parameter | Type     | Required | Description                              |
    | :-------- | :------- | :------- | :--------------------------------------- |
    | `uid`     | `string` | Yes      | Base64 encoded user ID from the URL.     |
    | `token`   | `string` | Yes      | Password reset token from the URL.       |

*   **Parameters (Body)**:

    | Parameter      | Type     | Required | Description                 |
    | :------------- | :------- | :------- | :-------------------------- |
    | `new_password` | `string` | Yes      | The new password for the user. |

*   **Request Example**:

    ```json
    {
        "new_password": "new_secure_password123"
    }
    ```
    (Note: `uid` and `token` are part of the URL path, not the body.)

*   **Success Response (200 OK)**:

    ```json
    {
        "detail": "Password has been reset successfully."
    }
    ```

*   **Error Response (400 Bad Request)**:

    ```json
    {
        "token": ["Invalid token for given user."]
    }
    ```
    Or:
    ```json
    {
        "new_password": ["This password is too common."]
    }
    ```

---

### Switch Management

These endpoints allow authenticated users to create, retrieve, update, and delete Dead Man's Switches, as well as perform check-ins.

#### List User's Switches

*   **HTTP Method**: `GET`
*   **Path**: `/api/switches/`
*   **Description**: Retrieves a list of all Dead Man's Switches owned by the authenticated user.
*   **Authentication**: `IsAuthenticated`
*   **Parameters**: None
*   **Request Example**:

    ```bash
    curl -X GET \
      -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
      http://localhost:8000/api/switches/
    ```

*   **Success Response (200 OK)**:

    ```json
    [
        {
            "id": 1,
            "title": "Important Document Release",
            "message": "Please release the confidential documents to John Doe.",
            "inactivity_duration_days": 30,
            "last_checkin": "2023-10-26T10:00:00Z",
            "created_at": "2023-09-26T10:00:00Z",
            "status": "active",
            "next_trigger_date": "2023-11-25T10:00:00Z",
            "action_type": "email",
            "action_target": "recipient@example.com"
        },
        {
            "id": 2,
            "title": "Website Takeover Protocol",
            "message": "Initiate automated website shutdown sequence.",
            "inactivity_duration_days": 7,
            "last_checkin": "2023-10-20T14:30:00Z",
            "created_at": "2023-10-15T14:30:00Z",
            "status": "active",
            "next_trigger_date": "2023-10-27T14:30:00Z",
            "action_type": "webhook",
            "action_target": "https://api.example.com/trigger/shutdown"
        }
    ]
    ```

*   **Error Response (401 Unauthorized)**:

    ```json
    {
        "detail": "Authentication credentials were not provided."
    }
    ```

#### Create a New Switch

*   **HTTP Method**: `POST`
*   **Path**: `/api/switches/`
*   **Description**: Creates a new Dead Man's Switch for the authenticated user.
*   **Authentication**: `IsAuthenticated`
*   **Parameters (Body)**:

    | Parameter              | Type     | Required | Description                                                              |
    | :--------------------- | :------- | :------- | :----------------------------------------------------------------------- |
    | `title`                | `string` | Yes      | A concise title for the switch.                                          |
    | `message`              | `string` | Yes      | The message content to be sent when the switch triggers.                 |
    | `inactivity_duration_days` | `integer` | Yes      | The number of days of inactivity before the switch triggers. (Must be >= 1)|
    | `action_type`          | `string` | Yes      | The type of action to perform (`email` or `webhook`).                    |
    | `action_target`        | `string` | Yes      | The target for the action (e.g., email address for `email`, URL for `webhook`). |

*   **Request Example**:

    ```json
    {
        "title": "Emergency Contact Alert",
        "message": "I haven't checked in for a week. Please contact my family at +1234567890.",
        "inactivity_duration_days": 7,
        "action_type": "email",
        "action_target": "emergency_contact@example.com"
    }
    ```

*   **Success Response (201 Created)**:

    ```json
    {
        "id": 3,
        "title": "Emergency Contact Alert",
        "message": "I haven't checked in for a week. Please contact my family at +1234567890.",
        "inactivity_duration_days": 7,
        "last_checkin": "2023-10-26T15:30:00Z",
        "created_at": "2023-10-26T15:30:00Z",
        "status": "active",
        "next_trigger_date": "2023-11-02T15:30:00Z",
        "action_type": "email",
        "action_target": "emergency_contact@example.com"
    }
    ```

*   **Error Response (400 Bad Request)**:

    ```json
    {
        "inactivity_duration_days": ["Ensure this value is greater than or equal to 1."],
        "action_target": ["Enter a valid email address."]
    }
    ```

#### Retrieve a Specific Switch

*   **HTTP Method**: `GET`
*   **Path**: `/api/switches/{id}/`
*   **Description**: Retrieves the detailed information for a specific Dead Man's Switch by its ID.
*   **Authentication**: `IsAuthenticated`
*   **Parameters (Path)**:

    | Parameter | Type     | Required | Description          |
    | :-------- | :------- | :------- | :------------------- |
    | `id`      | `integer` | Yes      | The ID of the switch. |

*   **Request Example**:

    ```bash
    curl -X GET \
      -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
      http://localhost:8000/api/switches/1/
    ```

*   **Success Response (200 OK)**:

    ```json
    {
        "id": 1,
        "title": "Important Document Release",
        "message": "Please release the confidential documents to John Doe.",
        "inactivity_duration_days": 30,
        "last_checkin": "2023-10-26T10:00:00Z",
        "created_at": "2023-09-26T10:00:00Z",
        "status": "active",
        "next_trigger_date": "2023-11-25T10:00:00Z",
        "action_type": "email",
        "action_target": "recipient@example.com"
    }
    ```

*   **Error Response (404 Not Found)**:

    ```json
    {
        "detail": "Not found."
    }
    ```
    (If the switch does not exist or does not belong to the authenticated user.)

#### Partially Update a Switch

*   **HTTP Method**: `PATCH`
*   **Path**: `/api/switches/{id}/`
*   **Description**: Partially updates one or more fields of an existing Dead Man's Switch.
*   **Authentication**: `IsAuthenticated`
*   **Parameters (Path)**:

    | Parameter | Type     | Required | Description          |
    | :-------- | :------- | :------- | :------------------- |
    | `id`      | `integer` | Yes      | The ID of the switch to update. |

*   **Parameters (Body)**: (Any of the following are optional)

    | Parameter              | Type     | Required | Description                                                    |
    | :--------------------- | :------- | :------- | :------------------------------------------------------------- |
    | `title`                | `string` | No       | New descriptive title.                                         |
    | `message`              | `string` | No       | New message content.                                           |
    | `inactivity_duration_days` | `integer` | No       | New number of days of inactivity before trigger. (Must be >= 1)|
    | `action_type`          | `string` | No       | New type of action (`email` or `webhook`).                     |
    | `action_target`        | `string` | No       | New target for the action (email address or URL).              |

*   **Request Example**:

    ```json
    {
        "inactivity_duration_days": 14,
        "action_target": "new_emergency_contact@example.com"
    }
    ```

*   **Success Response (200 OK)**:

    ```json
    {
        "id": 1,
        "title": "Important Document Release",
        "message": "Please release the confidential documents to John Doe.",
        "inactivity_duration_days": 14,
        "last_checkin": "2023-10-26T10:00:00Z",
        "created_at": "2023-09-26T10:00:00Z",
        "status": "active",
        "next_trigger_date": "2023-11-09T10:00:00Z",
        "action_type": "email",
        "action_target": "new_emergency_contact@example.com"
    }
    ```

*   **Error Response (400 Bad Request)**:

    ```json
    {
        "inactivity_duration_days": ["Ensure this value is greater than or equal to 1."]
    }
    ```

#### Delete a Switch

*   **HTTP Method**: `DELETE`
*   **Path**: `/api/switches/{id}/`
*   **Description**: Deletes a specific Dead Man's Switch by its ID.
*   **Authentication**: `IsAuthenticated`
*   **Parameters (Path)**:

    | Parameter | Type     | Required | Description              |
    | :-------- | :------- | :------- | :----------------------- |
    | `id`      | `integer` | Yes      | The ID of the switch to delete. |

*   **Request Example**:

    ```bash
    curl -X DELETE \
      -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
      http://localhost:8000/api/switches/1/
    ```

*   **Success Response (204 No Content)**: (Empty response body)

*   **Error Response (404 Not Found)**:

    ```json
    {
        "detail": "Not found."
    }
    ```
    (If the switch does not exist or does not belong to the authenticated user.)

#### Check-in for a Switch

*   **HTTP Method**: `POST`
*   **Path**: `/api/switches/{id}/checkin/`
*   **Description**: Records a check-in for a specific switch, updating its `last_checkin` timestamp to the current time and resetting its trigger timer.
*   **Authentication**: `IsAuthenticated`
*   **Parameters (Path)**:

    | Parameter | Type     | Required | Description                   |
    | :-------- | :------- | :------- | :---------------------------- |
    | `id`      | `integer` | Yes      | The ID of the switch to check-in. |

*   **Parameters (Body)**: None
*   **Request Example**:

    ```bash
    curl -X POST \
      -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
      http://localhost:8000/api/switches/1/checkin/
    ```

*   **Success Response (200 OK)**:

    ```json
    {
        "detail": "Check-in recorded successfully for switch ID 1."
    }
    ```

*   **Error Response (404 Not Found)**:

    ```json
    {
        "detail": "Not found."
    }
    ```
    (If the switch does not exist or does not belong to the authenticated user.)

---

### Action Types

This endpoint provides a list of actions that can be performed by a triggered switch.

#### List Available Action Types

*   **HTTP Method**: `GET`
*   **Path**: `/api/actions/`
*   **Description**: Retrieves a list of supported action types that can be configured for Dead Man's Switches (e.g., 'email', 'webhook').
*   **Authentication**: `IsAuthenticated`
*   **Parameters**: None
*   **Request Example**:

    ```bash
    curl -X GET \
      -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
      http://localhost:8000/api/actions/
    ```

*   **Success Response (200 OK)**:

    ```json
    [
        {
            "type": "email",
            "description": "Send an email notification"
        },
        {
            "type": "webhook",
            "description": "Send a POST request to a specified URL"
        }
    ]
    ```

*   **Error Response (401 Unauthorized)**:

    ```json
    {
        "detail": "Authentication credentials were not provided."
    }
    ```

---

### Utility Endpoints

These endpoints provide auxiliary functionalities, such as testing webhooks or getting a user's overall switch status.

#### Test a Webhook URL

*   **HTTP Method**: `POST`
*   **Path**: `/api/webhook-test/`
*   **Description**: Sends a test POST request to a provided webhook URL to verify its connectivity and response. This is useful for validating `action_target` URLs before creating a switch.
*   **Authentication**: `IsAuthenticated`
*   **Parameters (Body)**:

    | Parameter | Type     | Required | Description                   |
    | :-------- | :------- | :------- | :---------------------------- |
    | `url`     | `string` | Yes      | The URL of the webhook to test. |

*   **Request Example**:

    ```json
    {
        "url": "https://webhook.site/abcdef123-4567-890a-bcdef1234567"
    }
    ```

*   **Success Response (200 OK)**:

    ```json
    {
        "message": "Webhook test successful.",
        "status_code": 200,
        "response_text": "OK"
    }
    ```

*   **Error Response (400 Bad Request)**:

    ```json
    {
        "url": ["Enter a valid URL."]
    }
    ```
    Or (200 OK, but with error details if webhook fails to connect/respond):
    ```json
    {
        "message": "Webhook test failed.",
        "error": "Failed to connect to webhook URL: Max retries exceeded with url: https://invalid.url"
    }
    ```

#### Get Authenticated User Status

*   **HTTP Method**: `GET`
*   **Path**: `/api/my-status/`
*   **Description**: Provides an aggregate summary of the authenticated user's Dead Man's Switches, including counts of active/triggered switches and the timestamp of their most recent check-in across all switches.
*   **Authentication**: `IsAuthenticated`
*   **Parameters**: None
*   **Request Example**:

    ```bash
    curl -X GET \
      -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
      http://localhost:8000/api/my-status/
    ```

*   **Success Response (200 OK)**:

    ```json
    {
        "active_switches": 2,
        "triggered_switches": 0,
        "last_checkin": "2023-10-26T15:30:00Z"
    }
    ```
    (Note: `last_checkin` will be `null` if the user has no switches or no check-ins have ever occurred.)

*   **Error Response (401 Unauthorized)**:

    ```json
    {
        "detail": "Authentication credentials were not provided."
    }
    ```

## 4. Error Codes

The API uses standard HTTP status codes to indicate the success or failure of an API request. Specific error details are provided in the response body, typically in JSON format.

| Status Code | Meaning                 | Description                                                                 |
| :---------- | :---------------------- | :-------------------------------------------------------------------------- |
| `200 OK`    | Success                 | The request was successful.                                                 |
| `201 Created` | Resource Created        | A new resource was successfully created.                                    |
| `204 No Content` | Success (No Content)    | The request was successful, and there is no content to return (e.g., DELETE). |
| `400 Bad Request` | Invalid Input           | The request could not be understood or processed due to invalid parameters or malformed JSON. Specific error messages are provided in the response body. |
| `401 Unauthorized` | Authentication Required | The request lacks valid authentication credentials.                       |
| `403 Forbidden` | Access Denied           | The authenticated user does not have permission to access the requested resource or perform the action. |
| `404 Not Found` | Resource Not Found      | The requested resource (e.g., a switch with a given ID) does not exist. |
| `500 Internal Server Error` | Server Error            | An unexpected error occurred on the server. If this occurs, please report the issue. |

**Example Error Body (`400 Bad Request` for validation errors):**

```json
{
    "field_name": ["This field is required."],
    "another_field": ["Ensure this value is greater than or equal to 1."]
}
```

**Example Error Body (`401 Unauthorized` / `403 Forbidden`):**

```json
{
    "detail": "Authentication credentials were not provided."
}
```
Or:
```json
{
    "detail": "You do not have permission to perform this action."
}
```

## 5. Rate Limiting

There are no explicit API rate limits currently enforced on the Dead Man's Switch API. However, excessive requests may lead to temporary blocking or degraded service performance. It is recommended to implement reasonable retry mechanisms and respect server resources.

## 6. Sample Usage

Here are some `curl` command examples demonstrating common API interactions. Replace `YOUR_ACCESS_TOKEN` with a valid JWT obtained from the `/api/login/` or `/api/register/` endpoint.

**1. Register a new user:**

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "username": "sampleuser",
    "email": "sample@example.com",
    "password": "strongpassword123"
  }' \
  http://localhost:8000/api/register/
```

**2. Log in an existing user (if you already registered):**

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "email": "sample@example.com",
    "password": "strongpassword123"
  }' \
  http://localhost:8000/api/login/
```
*Take note of the `token` from the response.*

**3. Create a new Dead Man's Switch:**

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "My Important Reminder",
    "message": "This is the message to be sent if I don\'t check in.",
    "inactivity_duration_days": 10,
    "action_type": "email",
    "action_target": "alert_recipient@example.com"
  }' \
  http://localhost:8000/api/switches/
```

**4. List all your switches:**

```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  http://localhost:8000/api/switches/
```

**5. Check-in for a specific switch (e.g., switch with ID `1`):**

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  http://localhost:8000/api/switches/1/checkin/
```

**6. Partially update a switch (e.g., change its duration):**

```bash
curl -X PATCH \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "inactivity_duration_days": 14
  }' \
  http://localhost:8000/api/switches/1/
```

**7. Delete a switch:**

```bash
curl -X DELETE \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  http://localhost:8000/api/switches/1/
```

**8. Get your overall user status:**

```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  http://localhost:8000/api/my-status/
```

**9. Test a webhook:**

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "url": "https://your.test.webhook.site"
  }' \
  http://localhost:8000/api/webhook-test/
```