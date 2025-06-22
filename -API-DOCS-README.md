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

The DMS system provides a robust API for managing user accounts and configuring "Dead Man's Switches." A switch, once configured, monitors user activity (specifically, check-ins). If the user fails to check in within a pre-defined `inactivity_duration_days`, the switch is "triggered," and an associated action (e.g., sending an email, hitting a webhook) is executed. Background tasks, managed by Celery, periodically check the status of all active switches and trigger those that have become overdue.

## 2. Authentication

The primary authentication mechanism for this API is JSON Web Token (JWT) authentication, powered by `djangorestframework-simplejwt`.

Authentication Flow:

1.  **Obtain Token**: Users register via `/api/register/` (which returns a token upon success) or log in via `/api/login/` to obtain an access token.
2.  **Use Token**: For subsequent authenticated requests, include the obtained access token in the `Authorization` header of your HTTP requests in the `Bearer` scheme.

    Authorization: Bearer <YOUR_ACCESS_TOKEN>

    Example Header:
    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjg1MTc5ODc3LCJpYXQiOjE2ODQ5MjA2NzcsImp0aSI6ImZhMzI0ZDg0YzA1MjQyMTc4Zjg3ZWI0NDM1NzVjNjUyIiwidXNlcl9pZCI6MX0.S0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0

### JWT Token Lifetime

Access tokens are configured to expire after **3 days**. There is no explicit refresh token mechanism exposed via the API, so users will need to re-authenticate after their token expires.

## 3. API Endpoints

All API endpoints are prefixed with `/api/`.

---

### User Authentication & Management

These endpoints handle user registration, login, and password management.

#### Register a New User

*   **HTTP Method**: POST
*   **Path**: `/api/register/`
*   **Description**: Creates a new user account and returns an access token for immediate use.
*   **Authentication**: AllowAny
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

*   **HTTP Method**: POST
*   **Path**: `/api/login/`
*   **Description**: Authenticates an existing user and returns an access token.
*   **Authentication**: AllowAny
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

*   **HTTP Method**: POST
*   **Path**: `/api/password-reset/`
*   **Description**: Sends a password reset email to the specified email address.
*   **Authentication**: AllowAny
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
        "message": "Password reset link sent"
    }
    ```

*   **Error Response (400 Bad Request)**:

    ```json
    {
        "email": ["Enter a valid email address."]
    }
    ```
    Or if user does not exist:
    ```json
    {
        "email": ["User with this email does not exist."]
    }
    ```

#### Confirm Password Reset

*   **HTTP Method**: POST
*   **Path**: `/api/password-reset-confirm/<uid>/<token>/`
*   **Description**: Confirms the password reset process using the `uid` (base64 encoded user ID) and a JWT `token` (generated specifically for reset) from the reset link, and sets a new password.
*   **Authentication**: AllowAny
*   **Parameters (Path)**:

    | Parameter | Type     | Required | Description                              |
    | :-------- | :------- | :------- | :--------------------------------------- |
    | `uid`     | `string` | Yes      | Base64 encoded user ID from the URL.     |
    | `token`   | `string` | Yes      | JWT token from the URL.                  |

*   **Parameters (Body)**:

    | Parameter      | Type     | Required | Description                 |
    | :------------- | :------- | :------- | :-------------------------- |
    | `new_password` | `string` | Yes      | The new password for the user. |

*   **Request Example**:

    ```json
    {
        "new_password": "my_new_secure_password123"
    }
    ```

*   **Success Response (200 OK)**:

    ```json
    {
        "message": "Password has been reset"
    }
    ```

*   **Error Response (400 Bad Request)**:

    ```json
    {
        "detail": "Invalid token or user ID"
    }
    ```
    Or:
    ```json
    {
        "detail": "Invalid token"
    }
    ```
    Or (due to password validation):
    ```json
    {
        "new_password": ["This password is too short."]
    }
    ```

---

### Switch Management

These endpoints allow authenticated users to manage their Dead Man's Switches.

#### List User's Switches

*   **HTTP Method**: GET
*   **Path**: `/api/switches/`
*   **Description**: Retrieves a list of all Dead Man's Switches belonging to the authenticated user.
*   **Authentication**: IsAuthenticated
*   **Parameters**: None
*   **Request Example**:
    No request body.
*   **Success Response (200 OK)**:

    ```json
    [
        {
            "id": 1,
            "title": "My Critical Data Release",
            "status": "active",
            "last_checkin": "2024-01-01 10:00:00",
            "next_trigger_date": "2024-01-08 10:00:00",
            "action_type": "email"
        },
        {
            "id": 2,
            "title": "Company Webhook Trigger",
            "status": "triggered",
            "last_checkin": "2023-12-01 08:00:00",
            "next_trigger_date": "2023-12-08 08:00:00",
            "action_type": "webhook"
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

*   **HTTP Method**: POST
*   **Path**: `/api/switches/`
*   **Description**: Creates a new Dead Man's Switch for the authenticated user. An associated action will be created simultaneously based on the provided `action_type` and `action_target`.
*   **Authentication**: IsAuthenticated
*   **Parameters (Body)**:

    | Parameter                | Type     | Required | Description                                                    |
    | :----------------------- | :------- | :------- | :------------------------------------------------------------- |
    | `title`                  | `string` | Yes      | A brief title for the switch.                                  |
    | `message`                | `string` | Yes      | The message or content to be used when the action triggers.    |
    | `inactivity_duration_days` | `integer` | Yes      | The number of days of inactivity after which the switch triggers. |
    | `action_type`            | `string` | Yes      | The type of action to perform (`email` or `webhook`).          |
    | `action_target`          | `string` | Yes      | The target for the action (e.g., email address, URL).          |

*   **Request Example**:

    ```json
    {
        "title": "My Emergency Email Switch",
        "message": "This is the message to be sent if I don't check in for 30 days.",
        "inactivity_duration_days": 30,
        "action_type": "email",
        "action_target": "emergency.contact@example.com"
    }
    ```

*   **Success Response (201 Created)**:

    ```json
    {
        "id": 3,
        "title": "My Emergency Email Switch",
        "status": "active",
        "last_checkin": "2024-01-15 14:30:00",
        "next_trigger_date": "2024-02-14 14:30:00",
        "action_type": "email"
    }
    ```

*   **Error Response (400 Bad Request)**:

    ```json
    {
        "inactivity_duration_days": ["A valid integer is required."],
        "action_type": ["\"invalid_type\" is not a valid choice."]
    }
    ```

#### Retrieve a Specific Switch

*   **HTTP Method**: GET
*   **Path**: `/api/switches/{id}/`
*   **Description**: Retrieves the details of a specific Dead Man's Switch by its ID, belonging to the authenticated user.
*   **Authentication**: IsAuthenticated
*   **Parameters (Path)**:

    | Parameter | Type     | Required | Description              |
    | :-------- | :------- | :------- | :----------------------- |
    | `id`      | `integer` | Yes      | The ID of the switch.    |

*   **Request Example**:
    No request body.
*   **Success Response (200 OK)**:

    ```json
    {
        "id": 1,
        "title": "My Critical Data Release",
        "status": "active",
        "last_checkin": "2024-01-01 10:00:00",
        "next_trigger_date": "2024-01-08 10:00:00",
        "action_type": "email"
    }
    ```

*   **Error Response (404 Not Found)**:

    ```json
    {
        "detail": "Not found."
    }
    ```
    (This usually means the switch with the given ID does not exist or does not belong to the authenticated user).

#### Partially Update a Switch

*   **HTTP Method**: PATCH
*   **Path**: `/api/switches/{id}/`
*   **Description**: Partially updates the details of an existing Dead Man's Switch. Only `title`, `message`, and `inactivity_duration_days` can be updated through this endpoint. Action type or target cannot be modified directly here.
*   **Authentication**: IsAuthenticated
*   **Parameters (Path)**:

    | Parameter | Type     | Required | Description              |
    | :-------- | :------- | :------- | :----------------------- |
    | `id`      | `integer` | Yes      | The ID of the switch.    |

*   **Parameters (Body)**:
    (Any of the following, optional for partial update)

    | Parameter                | Type     | Required | Description                                                    |
    | :----------------------- | :------- | :------- | :------------------------------------------------------------- |
    | `title`                  | `string` | No       | A new title for the switch.                                    |
    | `message`                | `string` | No       | The new message or content for the action.                     |
    | `inactivity_duration_days` | `integer` | No       | The new number of days of inactivity for triggering.           |

*   **Request Example**:

    ```json
    {
        "title": "Updated Emergency Switch",
        "inactivity_duration_days": 45
    }
    ```

*   **Success Response (200 OK)**:

    ```json
    {
        "id": 1,
        "title": "Updated Emergency Switch",
        "status": "active",
        "last_checkin": "2024-01-01 10:00:00",
        "next_trigger_date": "2024-02-15 10:00:00",
        "action_type": "email"
    }
    ```

*   **Error Response (400 Bad Request)**:

    ```json
    {
        "inactivity_duration_days": ["Ensure this value is greater than or equal to 0."]
    }
    ```

*   **Error Response (404 Not Found)**:

    ```json
    {
        "detail": "Not found."
    }
    ```

#### Delete a Switch

*   **HTTP Method**: DELETE
*   **Path**: `/api/switches/{id}/`
*   **Description**: Deletes a specific Dead Man's Switch and its associated action.
*   **Authentication**: IsAuthenticated
*   **Parameters (Path)**:

    | Parameter | Type     | Required | Description              |
    | :-------- | :------- | :------- | :----------------------- |
    | `id`      | `integer` | Yes      | The ID of the switch.    |

*   **Request Example**:
    No request body.
*   **Success Response (204 No Content)**:
    No response body.
*   **Error Response (404 Not Found)**:

    ```json
    {
        "detail": "Not found."
    }
    ```

#### Check-in for a Switch

*   **HTTP Method**: POST
*   **Path**: `/api/switches/{id}/checkin/`
*   **Description**: Records a check-in for a specific switch, updating its `last_checkin` timestamp to the current time and resetting its next trigger date.
*   **Authentication**: IsAuthenticated
*   **Parameters (Path)**:

    | Parameter | Type     | Required | Description              |
    | :-------- | :------- | :------- | :----------------------- |
    | `id`      | `integer` | Yes      | The ID of the switch.    |

*   **Request Example**:
    No request body.
*   **Success Response (200 OK)**:

    ```json
    {
        "message": "Check-in successful. Next trigger reset."
    }
    ```

*   **Error Response (404 Not Found)**:

    ```json
    {
        "detail": "Not found."
    }
    ```

---

### Action Types

This endpoint provides information about the types of actions available for a Dead Man's Switch.

#### List Available Action Types

*   **HTTP Method**: GET
*   **Path**: `/api/actions/`
*   **Description**: Retrieves a list of supported action types (e.g., email, webhook) with their descriptions.
*   **Authentication**: IsAuthenticated
*   **Parameters**: None
*   **Request Example**:
    No request body.
*   **Success Response (200 OK)**:

    ```json
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
    ```

*   **Error Response (401 Unauthorized)**:

    ```json
    {
        "detail": "Authentication credentials were not provided."
    }
    ```

---

### Utility Endpoints

These are general utility endpoints for testing or retrieving user-specific summaries.

#### Test a Webhook URL

*   **HTTP Method**: POST
*   **Path**: `/api/webhook-test/`
*   **Description**: Sends a test payload to a provided webhook URL to verify its reachability and response.
*   **Authentication**: IsAuthenticated
*   **Parameters (Body)**:

    | Parameter | Type     | Required | Description                                |
    | :-------- | :------- | :------- | :----------------------------------------- |
    | `url`     | `string` | Yes      | The URL of the webhook endpoint to test.   |

*   **Request Example**:

    ```json
    {
        "url": "https://webhook.site/your-unique-id"
    }
    ```

*   **Success Response (200 OK)**:

    ```json
    {
        "status": 200,
        "response": "Test successful"
    }
    ```
    (The `response` field will contain the text response from the webhook.)

*   **Error Response (400 Bad Request)**:

    ```json
    {
        "error": "URL required"
    }
    ```
    Or (if the webhook URL is invalid or unreachable):
    ```json
    {
        "error": "Invalid URL or connection error: Max retries exceeded with url: ..."
    }
    ```

#### Get Authenticated User Status

*   **HTTP Method**: GET
*   **Path**: `/api/my-status/`
*   **Description**: Provides a summary of the authenticated user's Dead Man's Switches, including counts of active and triggered switches, and the timestamp of their most recent check-in across all switches.
*   **Authentication**: IsAuthenticated
*   **Parameters**: None
*   **Request Example**:
    No request body.
*   **Success Response (200 OK)**:

    ```json
    {
        "active_switches": 5,
        "triggered_switches": 2,
        "last_checkin": "2024-01-15 15:00:00"
    }
    ```
    If no check-ins have occurred:
    ```json
    {
        "active_switches": 0,
        "triggered_switches": 0,
        "last_checkin": null
    }
    ```

*   **Error Response (401 Unauthorized)**:

    ```json
    {
        "detail": "Authentication credentials were not provided."
    }
    ```

## 4. Error Codes

The API uses standard HTTP status codes to indicate the success or failure of a request. Common error codes you might encounter include:

*   **200 OK**: The request was successful, and the response body contains the requested data.
*   **201 Created**: The request was successful, and a new resource was created.
*   **204 No Content**: The request was successful, but there is no content to return (e.g., for a successful DELETE operation).
*   **400 Bad Request**: The request was malformed or contained invalid parameters. The response body will usually provide specific details about the error (e.g., missing required fields, invalid data formats, validation errors).
*   **401 Unauthorized**: The request requires authentication, or the provided authentication credentials (JWT token) are invalid or missing.
*   **403 Forbidden**: The authenticated user does not have permission to perform the requested action on the specified resource.
*   **404 Not Found**: The requested resource could not be found. This typically means the URL path is incorrect or the specific ID provided does not correspond to an existing resource accessible by the user.
*   **500 Internal Server Error**: An unexpected error occurred on the server. This usually indicates a problem on the server's end.

## 5. Rate Limiting

There are no explicit API rate limits implemented in this version of the Dead Man's Switch API. Clients are advised to implement sensible retry mechanisms with exponential backoff to avoid overwhelming the server with requests.

## 6. Sample Usage

The following outlines general usage patterns for interacting with the Dead Man's Switch API:

*   **User Registration and Authentication**:
    *   To get started, send a POST request to `/api/register/` with a username, email, and password. The response will include an access token.
    *   Alternatively, if you're an existing user, send a POST request to `/api/login/` with your email and password to obtain an access token.
    *   Always include the obtained access token in the `Authorization: Bearer <token>` header for subsequent requests to protected endpoints.

*   **Managing Switches**:
    *   To view all your existing switches, send a GET request to `/api/switches/` with your authentication token.
    *   To create a new switch, send a POST request to `/api/switches/` including the `title`, `message`, `inactivity_duration_days`, `action_type`, and `action_target` in the request body.
    *   To retrieve details for a specific switch, send a GET request to `/api/switches/{id}/`.
    *   To modify a switch's title, message, or inactivity duration, send a PATCH request to `/api/switches/{id}/` with the fields you wish to update.
    *   To delete a switch, send a DELETE request to `/api/switches/{id}/`.
    *   Crucially, to prevent a switch from triggering, periodically send a POST request to `/api/switches/{id}/checkin/` for that specific switch. This resets its inactivity timer.

*   **Discovering Action Types**:
    *   Before creating a switch, you can query the available action types by sending a GET request to `/api/actions/`. This will show you options like "email" and "webhook".

*   **Monitoring Your Status**:
    *   To get a quick overview of your active and triggered switches and your overall last check-in time, send a GET request to `/api/my-status/`.

*   **Testing Webhooks**:
    *   If your action type is "webhook," you can test a target URL independently by sending a POST request to `/api/webhook-test/` with the `url` in the request body.