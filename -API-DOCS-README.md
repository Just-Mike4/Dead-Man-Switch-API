# Dead Man's Switch (DMS) API Documentation

This document provides comprehensive API documentation for the Dead Man's Switch (DMS) system. The DMS is a Django-based application designed to trigger predefined actions if a user fails to check in within a specified period, ensuring critical information or actions are taken in the event of prolonged inactivity.

The API is built using Django REST Framework and uses JWT for authentication, with Celery handling background tasks like switch triggering.

## Table of Contents

1.  Introduction
2.  Authentication
    *   JWT Token Lifetime
3.  API Endpoints
    *   User Authentication & Management
        *   Register a New User
        *   Log In User
        *   Initiate Password Reset
        *   Confirm Password Reset
    *   Switch Management
        *   List User's Switches
        *   Create a New Switch
        *   Retrieve a Specific Switch
        *   Partially Update a Switch
        *   Delete a Switch
        *   Check-in for a Switch
    *   Action Types
        *   List Available Action Types
    *   Utility Endpoints
        *   Test a Webhook URL
        *   Get Authenticated User Status
4.  Error Codes
5.  Rate Limiting
6.  Sample Usage

## 1. Introduction

The DMS system provides a robust API for managing user accounts and configuring "Dead Man's Switches." A switch, once configured, monitors user activity (specifically, check-ins). If the user fails to check in within a pre-defined inactivity duration, the switch is "triggered," and an associated action (e.g., sending an email, hitting a webhook) is executed. Background tasks, managed by Celery, periodically check the status of all active switches and trigger those that have become overdue.

## 2. Authentication

The primary authentication mechanism for this API is JSON Web Token (JWT) authentication, powered by djangorestframework-simplejwt.

Authentication Flow:

1.  **Obtain Token**: Users register via /api/register/ (which returns a token upon success) or log in via /api/login/ to obtain an access token.
2.  **Use Token**: For subsequent authenticated requests, include the obtained access token in the Authorization header of your HTTP requests in the Bearer scheme.

    Authorization: Bearer <YOUR_ACCESS_TOKEN>

    Example Header:
    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjg1MTc5ODc3LCJpYXQiOjE2ODQ5MjA2NzcsImp0aSI6ImZhMzI0ZDg0YzA1MjQyMTc4Zjg3ZWI0NDM1NzVjNjUyIiwidXNlcl9pZCI6MX0.S0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0

### JWT Token Lifetime

Access tokens are configured to expire after 3 days. There is no explicit refresh token mechanism exposed via the API, so users will need to re-authenticate after their token expires.

## 3. API Endpoints

All API endpoints are prefixed with /api/.

---

### User Authentication & Management

These endpoints handle user registration, login, and password management.

#### Register a New User

*   HTTP Method: POST
*   Path: /api/register/
*   Description: Creates a new user account and returns an access token for immediate use.
*   Authentication: AllowAny
*   Parameters (Body):

    | Parameter  | Type   | Required | Description                     |
    | :--------- | :----- | :------- | :------------------------------ |
    | username   | string | Yes      | A unique username.              |
    | email      | string | Yes      | A unique and valid email.       |
    | password   | string | Yes      | User's chosen password.         |

*   Request Example:

    {
        "username": "api_user",
        "email": "api.user@example.com",
        "password": "securepassword123"
    }

*   Success Response (201 Created):

    {
        "username": "api_user",
        "email": "api.user@example.com",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjg1MTc5ODc3LCJpYXQiOjE2ODQ5MjA2NzcsImp0aSI6ImZhMzI0ZDg0YzA1MjQyMTc4Zjg3ZWI0NDM1NzVjNjUyIiwidXNlcl9pZCI6MX0.S0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0"
    }

*   Error Response (400 Bad Request):

    {
        "email": [
            "user with this email already exists."
        ],
        "password": [
            "This password is too common."
        ]
    }

#### Log In User

*   HTTP Method: POST
*   Path: /api/login/
*   Description: Authenticates an existing user and returns an access token.
*   Authentication: AllowAny
*   Parameters (Body):

    | Parameter | Type   | Required | Description                       |
    | :-------- | :----- | :------- | :-------------------------------- |
    | email     | string | Yes      | The user's registered email.      |
    | password  | string | Yes      | The user's password.              |

*   Request Example:

    {
        "email": "api.user@example.com",
        "password": "securepassword123"
    }

*   Success Response (200 OK):

    {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjg1MTc5ODc3LCJpYXQiOjE2ODQ5MjA2NzcsImp0aSI6ImZhMzI0ZDg0YzA1MjQyMTc4Zjg3ZWI0NDM1NzVjNjUyIiwidXNlcl9pZCI6MX0.S0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0"
    }

*   Error Response (401 Unauthorized):

    {
        "detail": "No active account found with the given credentials"
    }

#### Initiate Password Reset

*   HTTP Method: POST
*   Path: /api/password-reset/
*   Description: Sends a password reset email to the specified email address.
*   Authentication: AllowAny
*   Parameters (Body):

    | Parameter | Type   | Required | Description                                    |
    | :-------- | :----- | :------- | :--------------------------------------------- |
    | email     | string | Yes      | The email address associated with the account. |

*   Request Example:

    {
        "email": "user@example.com"
    }

*   Success Response (200 OK):

    {
        "message": "Password reset link sent"
    }

*   Error Response (400 Bad Request):

    {
        "email": [
            "Enter a valid email address."
        ]
    }

    Or if user does not exist:

    {
        "email": [
            "User with this email does not exist."
        ]
    }

#### Confirm Password Reset

*   HTTP Method: POST
*   Path: /api/password-reset-confirm/<uid>/<token>/
*   Description: Confirms the password reset process using the uid and token from the reset link and sets a new password.
*   Authentication: AllowAny
*   Parameters (Path):

    | Parameter | Type   | Required | Description                            |
    | :-------- | :----- | :------- | :------------------------------------- |
    | uid       | string | Yes      | Base64 encoded user ID from the URL.   |
    | token     | string | Yes      | Password reset token from the URL.     |

*   Parameters (Body):

    | Parameter      | Type   | Required | Description                 |
    | :------------- | :----- | :------- | :-------------------------- |
    | new_password   | string | Yes      | The new password for the user. |

*   Request Example:

    {
        "new_password": "ANewSecurePassword123!"
    }

*   Success Response (200 OK):

    {
        "message": "Password has been reset"
    }

*   Error Response (400 Bad Request):

    {
        "detail": "Invalid token or user ID"
    }

---

### Switch Management

These endpoints allow authenticated users to manage their Dead Man's Switches.

#### List User's Switches

*   HTTP Method: GET
*   Path: /api/switches/
*   Description: Retrieves a list of all Dead Man's Switches owned by the authenticated user.
*   Authentication: JWT (IsAuthenticated)
*   Parameters: None
*   Request Example:

    (No request body needed)

*   Success Response (200 OK):

    [
        {
            "id": 1,
            "title": "My Important Switch",
            "status": "active",
            "last_checkin": "2024-01-01 10:00:00",
            "next_trigger_date": "2024-01-08 10:00:00",
            "action_type": "email"
        },
        {
            "id": 2,
            "title": "Another Switch",
            "status": "triggered",
            "last_checkin": "2023-12-01 12:00:00",
            "next_trigger_date": "2023-12-05 12:00:00",
            "action_type": "webhook"
        }
    ]

*   Error Response (401 Unauthorized):

    {
        "detail": "Authentication credentials were not provided."
    }

#### Create a New Switch

*   HTTP Method: POST
*   Path: /api/switches/
*   Description: Creates a new Dead Man's Switch for the authenticated user.
*   Authentication: JWT (IsAuthenticated)
*   Parameters (Body):

    | Parameter                  | Type   | Required | Description                                                    |
    | :------------------------- | :----- | :------- | :------------------------------------------------------------- |
    | title                      | string | Yes      | A descriptive title for the switch.                            |
    | message                    | string | Yes      | The message to be sent or included in the action upon trigger. |
    | inactivity_duration_days   | integer | Yes      | Number of days of inactivity before the switch triggers.       |
    | action_type                | string | Yes      | The type of action to perform. Allowed: "email", "webhook".    |
    | action_target              | string | Yes      | The target for the action (e.g., email address, webhook URL).  |

*   Request Example:

    {
        "title": "Financial Documents Release",
        "message": "Please send these documents to my lawyer upon trigger.",
        "inactivity_duration_days": 7,
        "action_type": "email",
        "action_target": "lawyer@example.com"
    }

*   Success Response (201 Created):

    {
        "id": 3,
        "title": "Financial Documents Release",
        "status": "active",
        "last_checkin": "2024-05-15 14:30:00",
        "next_trigger_date": "2024-05-22 14:30:00",
        "action_type": "email"
    }

*   Error Response (400 Bad Request):

    {
        "inactivity_duration_days": [
            "A valid integer is required."
        ],
        "action_type": [
            "\"invalid_type\" is not a valid choice."
        ]
    }

#### Retrieve a Specific Switch

*   HTTP Method: GET
*   Path: /api/switches/<id>/
*   Description: Retrieves details for a single Dead Man's Switch by its ID.
*   Authentication: JWT (IsAuthenticated)
*   Parameters (Path):

    | Parameter | Type    | Required | Description               |
    | :-------- | :------ | :------- | :------------------------ |
    | id        | integer | Yes      | The ID of the switch.     |

*   Request Example:

    (No request body needed)

*   Success Response (200 OK):

    {
        "id": 1,
        "title": "My Important Switch",
        "status": "active",
        "last_checkin": "2024-01-01 10:00:00",
        "next_trigger_date": "2024-01-08 10:00:00",
        "action_type": "email"
    }

*   Error Response (404 Not Found):

    {
        "detail": "Not found."
    }

*   Error Response (403 Forbidden): (If the switch belongs to another user)

    {
        "detail": "You do not have permission to perform this action."
    }

#### Partially Update a Switch

*   HTTP Method: PATCH
*   Path: /api/switches/<id>/
*   Description: Updates one or more fields of an existing Dead Man's Switch.
*   Authentication: JWT (IsAuthenticated)
*   Parameters (Path):

    | Parameter | Type    | Required | Description               |
    | :-------- | :------ | :------- | :------------------------ |
    | id        | integer | Yes      | The ID of the switch.     |

*   Parameters (Body):

    | Parameter                  | Type   | Required | Description                                                    |
    | :------------------------- | :----- | :------- | :------------------------------------------------------------- |
    | title                      | string | No       | New title for the switch.                                      |
    | message                    | string | No       | New message for the action.                                    |
    | inactivity_duration_days   | integer | No       | New inactivity duration in days.                               |
    | action_type                | string | No       | New action type. Allowed: "email", "webhook".                  |
    | action_target              | string | No       | New target for the action (e.g., email address, webhook URL).  |
    | status                     | string | No       | New status for the switch. Allowed: "active", "triggered".     |

*   Request Example:

    {
        "inactivity_duration_days": 10
    }

*   Success Response (200 OK):

    {
        "id": 1,
        "title": "My Important Switch",
        "status": "active",
        "last_checkin": "2024-01-01 10:00:00",
        "next_trigger_date": "2024-01-11 10:00:00",
        "action_type": "email"
    }

*   Error Response (400 Bad Request):

    {
        "action_type": [
            "\"invalid\" is not a valid choice."
        ]
    }

*   Error Response (404 Not Found):

    {
        "detail": "Not found."
    }

#### Delete a Switch

*   HTTP Method: DELETE
*   Path: /api/switches/<id>/
*   Description: Deletes a specific Dead Man's Switch.
*   Authentication: JWT (IsAuthenticated)
*   Parameters (Path):

    | Parameter | Type    | Required | Description               |
    | :-------- | :------ | :------- | :------------------------ |
    | id        | integer | Yes      | The ID of the switch.     |

*   Request Example:

    (No request body needed)

*   Success Response (204 No Content):
    (No content in response body)

*   Error Response (404 Not Found):

    {
        "detail": "Not found."
    }

#### Check-in for a Switch

*   HTTP Method: POST
*   Path: /api/switches/<id>/checkin/
*   Description: Resets the inactivity timer for a specific switch by updating its last_checkin timestamp to the current time. This postpones the next_trigger_date.
*   Authentication: JWT (IsAuthenticated)
*   Parameters (Path):

    | Parameter | Type    | Required | Description               |
    | :-------- | :------ | :------- | :------------------------ |
    | id        | integer | Yes      | The ID of the switch.     |

*   Request Example:

    (No request body needed)

*   Success Response (200 OK):

    {
        "message": "Check-in successful. Next trigger reset."
    }

*   Error Response (404 Not Found):

    {
        "detail": "Not found."
    }

---

### Action Types

These endpoints provide information about supported action types.

#### List Available Action Types

*   HTTP Method: GET
*   Path: /api/actions/
*   Description: Retrieves a list of supported action types that can be configured for a switch.
*   Authentication: JWT (IsAuthenticated)
*   Parameters: None
*   Request Example:

    (No request body needed)

*   Success Response (200 OK):

    [
        {
            "type": "email",
            "description": "Email"
        },
        {
            "type": "webhook",
            "description": "Webhook"
        }
    ]

*   Error Response (401 Unauthorized):

    {
        "detail": "Authentication credentials were not provided."
    }

---

### Utility Endpoints

These endpoints provide auxiliary functionalities.

#### Test a Webhook URL

*   HTTP Method: POST
*   Path: /api/webhook-test/
*   Description: Sends a test POST request to a provided webhook URL to verify its reachability and response.
*   Authentication: JWT (IsAuthenticated)
*   Parameters (Body):

    | Parameter | Type   | Required | Description                  |
    | :-------- | :----- | :------- | :--------------------------- |
    | url       | string | Yes      | The URL of the webhook to test. |

*   Request Example:

    {
        "url": "https://example.com/my-webhook-endpoint"
    }

*   Success Response (200 OK):

    {
        "status": 200,
        "response": "Webhook test successful"
    }

*   Error Response (400 Bad Request):

    {
        "error": "URL required"
    }

    Or if the webhook test fails (e.g., network error, invalid URL):

    {
        "error": "Connection refused"
    }

#### Get Authenticated User Status

*   HTTP Method: GET
*   Path: /api/my-status/
*   Description: Provides a summary of the authenticated user's switches, including counts of active and triggered switches, and the timestamp of their last overall check-in.
*   Authentication: JWT (IsAuthenticated)
*   Parameters: None
*   Request Example:

    (No request body needed)

*   Success Response (200 OK):

    {
        "active_switches": 2,
        "triggered_switches": 1,
        "last_checkin": "2024-05-15 14:30:00"
    }

    Or if no switches exist:

    {
        "active_switches": 0,
        "triggered_switches": 0,
        "last_checkin": null
    }

*   Error Response (401 Unauthorized):

    {
        "detail": "Authentication credentials were not provided."
    }

## 4. Error Codes

The API uses standard HTTP status codes to indicate the success or failure of an API request. Specific error messages are provided in the response body.

| Status Code | Meaning        | Description                                                                                                                                                                                                                                           |
| :---------- | :------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 200 OK      | Success        | The request was successful.                                                                                                                                                                                                                           |
| 201 Created | Resource Created | The request was successful and a new resource was created.                                                                                                                                                                                            |
| 204 No Content | Success (No Content) | The request was successful, but there is no content to return (e.g., for DELETE requests).                                                                                                                                                            |
| 400 Bad Request | Invalid Request | The request was malformed or invalid. This often indicates issues with the request body (e.g., missing required fields, invalid data format, validation errors). The response body will contain specific error messages about what went wrong. |
| 401 Unauthorized | Authentication Required | The request requires user authentication. This usually means a missing or invalid JWT token in the `Authorization` header.                                                                                                              |
| 403 Forbidden | Access Denied  | The authenticated user does not have permission to access the requested resource or perform the action. This can happen if a user tries to access a switch belonging to another user.                                                                  |
| 404 Not Found | Resource Not Found | The requested resource (e.g., a switch with a given ID) could not be found.                                                                                                                                                                       |
| 500 Internal Server Error | Server Error   | An unexpected error occurred on the server. This typically indicates a bug on the server side. If you encounter this, please report it to the API developers.                                                                          |

## 5. Rate Limiting

The Dead Man's Switch API does not have explicit API-level rate limits configured by default within the Django REST Framework settings provided. However, infrastructure-level rate limiting (e.g., via a proxy server like Nginx or cloud provider services) may be in place in a production environment to protect against abuse. Clients should implement sensible retry logic and exponential backoff to avoid overwhelming the server.

## 6. Sample Usage

This section provides a high-level conceptual flow for interacting with the API.

1.  **Register a User**:
    *   Send a POST request to /api/register/ with username, email, and password.
    *   Receive a JWT token.

2.  **Log In (if not registered or token expired)**:
    *   Send a POST request to /api/login/ with email and password.
    *   Receive a new JWT token.

3.  **Create a Dead Man's Switch**:
    *   Include your JWT token in the Authorization: Bearer header.
    *   Send a POST request to /api/switches/ with details like title, message, inactivity duration, action type (e.g., "email"), and action target (e.g., "recipient@example.com").

4.  **Periodically Check-in**:
    *   To keep your switch active and prevent it from triggering, you must regularly check in.
    *   Include your JWT token in the Authorization: Bearer header.
    *   Send a POST request to /api/switches/<switch_id>/checkin/. This will reset the countdown for that specific switch.

5.  **Monitor Your Switches**:
    *   Include your JWT token in the Authorization: Bearer header.
    *   Send a GET request to /api/my-status/ to see a summary of your switches and your last check-in activity.
    *   Send a GET request to /api/switches/ to list all your configured switches.

6.  **Manage Existing Switches**:
    *   To update a switch, send a PATCH request to /api/switches/<switch_id>/ with the fields you want to change.
    *   To delete a switch, send a DELETE request to /api/switches/<switch_id>/.

7.  **Test Webhooks**:
    *   If you plan to use webhook actions, you can test a target URL by sending a POST request to /api/webhook-test/ with the URL in the request body.