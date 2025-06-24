# API Documentation for Dead Man's Switch (DMS)

## Table of Contents

*   [Authentication](#authentication)
*   [Endpoints](#endpoints)
    *   [`POST /api/register/`](#post-apiregister)
    *   [`POST /api/login/`](#post-apilogin)
    *   [`POST /api/password-reset/`](#post-apipassword-reset)
    *   [`POST /api/password-reset-confirm/<uid>/<token>/`](#post-apipassword-reset-confirmuidtoken)
    *   [`GET /api/switches/`](#get-apiswitches)
    *   [`POST /api/switches/`](#post-apiswitches)
    *   [`GET /api/switches/{id}/`](#get-apiswitchesid)
    *   [`PATCH /api/switches/{id}/`](#patch-apiswitchesid)
    *   [`DELETE /api/switches/{id}/`](#delete-apiswitchesid)
    *   [`POST /api/switches/{id}/checkin/`](#post-apiswitchesidcheckin)
    *   [`GET /api/actions/`](#get-apiactions)
    *   [`POST /api/webhook-test/`](#post-apiwebhook-test)
    *   [`GET /api/my-status/`](#get-apimy-status)

## Authentication

The primary authentication mechanism for this API is JSON Web Token (JWT) authentication, powered by `djangorestframework-simplejwt`.

**Authentication Flow:**

1.  **Obtain Token**: Users register via `/api/register/` (which returns a token upon success) or log in via `/api/login/` to obtain an access token.
2.  **Use Token**: For subsequent authenticated requests, include the obtained access token in the `Authorization` header of your HTTP requests in the `Bearer` scheme.

    `Authorization: Bearer <YOUR_ACCESS_TOKEN>`

    **Example Header:**
    `Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjg1MTc5ODc3LCJpYXQiOjE2ODQ5MjA2NzcsImp0aSI6ImZhMzI0ZDg0YzA1MjQyMTc4Zjg3ZWI0NDM1NzVjNjUyIiwidXNlcl9pZCI6MX0.S0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0`

### JWT Token Lifetime

Access tokens are configured to expire after **3 days**. There is no explicit refresh token mechanism exposed via the API, so users will need to re-authenticate after their token expires.

## Endpoints

### `POST /api/register/`
**Description**  
Creates a new user account and returns an access token for immediate use.

**Parameters**  
| Type   | Name     | Data Type | Required | Constraints           |
|--------|----------|-----------|----------|-----------------------|
| Body   | `username` | `string`  | Yes      | Not documented in context |
| Body   | `email`    | `string`  | Yes      | Not documented in context |
| Body   | `password` | `string`  | Yes      | Not documented in context |

**Request Body**  
```json
{
    "username": "api_user",
    "email": "api.user@example.com",
    "password": "securepassword123"
}
```

**Responses**  
`201 Created`  
```json
{
    "username": "api_user",
    "email": "api.user@example.com",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjg1MTc5ODc3LCJpYXQiOjE2ODQ5MjA2NzcsImp0aSI6ImZhMzI0ZDg0YzA1MjQyMTc4Zjg3ZWI0NDM1NzVjNjUyIiwidXNlcl9pZCI6MX0.S0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0"
}
```
`400 Bad Request`  
```json
{
    "email": ["user with this email already exists."],
    "password": ["This password is too common."]
}
```

**Auth**  
`AllowAny`

### `POST /api/login/`
**Description**  
Authenticates an existing user and returns an access token.

**Parameters**  
| Type   | Name     | Data Type | Required | Constraints           |
|--------|----------|-----------|----------|-----------------------|
| Body   | `email`    | `string`  | Yes      | Not documented in context |
| Body   | `password` | `string`  | Yes      | Not documented in context |

**Request Body**  
```json
{
    "email": "api.user@example.com",
    "password": "securepassword123"
}
```

**Responses**  
`200 OK`  
```json
{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjg1MTc5ODc3LCJpYXQiOjE2ODQ5MjA2NzcsImp0aSI6ImZhMzI0ZDg0YzA1MjQyMTc4Zjg3ZWI0NDM1NzVjNjUyIiwidXNlcl9pZCI6MX0.S0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0mF0"
}
```
`400 Bad Request`  
```json
{
    "detail": "No active account found with the given credentials"
}
```

**Auth**  
`AllowAny`

### `POST /api/password-reset/`
**Description**  
Sends a password reset email to the specified email address.

**Parameters**  
| Type   | Name    | Data Type | Required | Constraints           |
|--------|---------|-----------|----------|-----------------------|
| Body   | `email` | `string`  | Yes      | Not documented in context |

**Request Body**  
```json
{
    "email": "user@example.com"
}
```

**Responses**  
`200 OK`  
```json
{
    "message": "Password reset link sent"
}
```
`400 Bad Request`  
```json
{
    "email": ["Enter a valid email address."]
}
```
`400 Bad Request`  
```json
{
    "email": ["User with this email does not exist."]
}
```

**Auth**  
`AllowAny`

### `POST /api/password-reset-confirm/<uid>/<token>/`
**Description**  
Confirms the password reset process using the `uid` (base64 encoded user ID) and a JWT `token` (generated specifically for reset) from the reset link, and sets a new password.

**Parameters**  
| Type   | Name           | Data Type | Required | Constraints           |
|--------|----------------|-----------|----------|-----------------------|
| Path   | `uid`          | `string`  | Yes      | Not documented in context |
| Path   | `token`        | `string`  | Yes      | Not documented in context |
| Body   | `new_password` | `string`  | Yes      | Not documented in context |

**Request Body**  
```json
{
    "new_password": "new_secure_password_123"
}
```

**Responses**  
`200 OK`  
```json
{
    "message": "Password has been reset"
}
```
`400 Bad Request`  
```json
{
    "detail": "Invalid token or user ID"
}
```
`400 Bad Request`  
```json
{
    "detail": "Invalid token"
}
```
`400 Bad Request`  
```json
{
    "new_password": ["This password is too common."]
}
```

**Auth**  
`AllowAny`

### `GET /api/switches/`
**Description**  
Retrieves a list of all Dead Man's Switches associated with the authenticated user.

**Parameters**  
No parameters documented in context.

**Request Body**  
No request body documented in context.

**Responses**  
`200 OK`  
```json
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
        "title": "Backup Webhook",
        "status": "triggered",
        "last_checkin": "2023-12-25 15:30:00",
        "next_trigger_date": "2024-01-01 15:30:00",
        "action_type": "webhook"
    }
]
```

**Auth**  
`IsAuthenticated`

### `POST /api/switches/`
**Description**  
Creates a new Dead Man's Switch for the authenticated user. An associated action will be created simultaneously based on `action_type` and `action_target`.

**Parameters**  
| Type   | Name                       | Data Type | Required | Constraints           |
|--------|----------------------------|-----------|----------|-----------------------|
| Body   | `title`                    | `string`  | Yes      | Not documented in context |
| Body   | `message`                  | `string`  | Yes      | Not documented in context |
| Body   | `inactivity_duration_days` | `integer` | Yes      | Not documented in context |
| Body   | `action_type`              | `string`  | Yes      | `email` or `webhook`  |
| Body   | `action_target`            | `string`  | Yes      | Email address or URL  |

**Request Body**  
```json
{
    "title": "Send Urgent Email",
    "message": "This is a critical message that needs to be sent!",
    "inactivity_duration_days": 7,
    "action_type": "email",
    "action_target": "recipient@example.com"
}
```

**Responses**  
`201 Created`  
```json
{
    "id": 3,
    "title": "Send Urgent Email",
    "status": "active",
    "last_checkin": "2024-01-15 11:30:00",
    "next_trigger_date": "2024-01-22 11:30:00",
    "action_type": "email"
}
```
`400 Bad Request`  
```json
{
    "action_type": ["\"invalid_type\" is not a valid choice."],
    "action_target": ["Enter a valid email address."]
}
```

**Auth**  
`IsAuthenticated`

### `GET /api/switches/{id}/`
**Description**  
Retrieves details for a specific Dead Man's Switch belonging to the authenticated user.

**Parameters**  
| Type   | Name | Data Type | Required | Constraints           |
|--------|------|-----------|----------|-----------------------|
| Path   | `id` | `integer` | Yes      | Not documented in context |

**Request Body**  
No request body documented in context.

**Responses**  
`200 OK`  
```json
{
    "id": 1,
    "title": "My Important Switch",
    "message": "This is the full message content.",
    "inactivity_duration_days": 7,
    "last_checkin": "2024-01-01 10:00:00",
    "created_at": "2023-12-20 09:00:00",
    "status": "active",
    "action": {
        "type": "email",
        "target": "john.doe@example.com"
    }
}
```
`404 Not Found`  
```json
{
    "detail": "Not found."
}
```

**Auth**  
`IsAuthenticated`

### `PATCH /api/switches/{id}/`
**Description**  
Partially updates details for a specific Dead Man's Switch belonging to the authenticated user. Only fields provided in the request body will be updated.

**Parameters**  
| Type   | Name | Data Type | Required | Constraints           |
|--------|------|-----------|----------|-----------------------|
| Path   | `id` | `integer` | Yes      | Not documented in context |
| Body   | `title` | `string` | No | Not documented in context |
| Body   | `message` | `string` | No | Not documented in context |
| Body   | `inactivity_duration_days` | `integer` | No | Not documented in context |
| Body   | `action_type` | `string` | No | `email` or `webhook` |
| Body   | `action_target` | `string` | No | Email address or URL |

**Request Body**  
```json
{
    "inactivity_duration_days": 14,
    "message": "New updated message for the switch."
}
```

**Responses**  
`200 OK`  
```json
{
    "id": 1,
    "title": "My Important Switch",
    "status": "active",
    "last_checkin": "2024-01-01 10:00:00",
    "next_trigger_date": "2024-01-29 10:00:00",
    "action_type": "email"
}
```
`400 Bad Request`  
```json
{
    "inactivity_duration_days": ["Ensure this value is greater than or equal to 1."]
}
```
`404 Not Found`  
```json
{
    "detail": "Not found."
}
```

**Auth**  
`IsAuthenticated`

### `DELETE /api/switches/{id}/`
**Description**  
Deletes a specific Dead Man's Switch belonging to the authenticated user. This will also delete the associated action.

**Parameters**  
| Type   | Name | Data Type | Required | Constraints           |
|--------|------|-----------|----------|-----------------------|
| Path   | `id` | `integer` | Yes      | Not documented in context |

**Request Body**  
No request body documented in context.

**Responses**  
`204 No Content`  
```
```
`404 Not Found`  
```json
{
    "detail": "Not found."
}
```

**Auth**  
`IsAuthenticated`

### `POST /api/switches/{id}/checkin/`
**Description**  
Performs a check-in for a specific Dead Man's Switch. This updates its `last_checkin` timestamp and resets its `next_trigger_date`, preventing it from triggering for the set `inactivity_duration_days`.

**Parameters**  
| Type   | Name | Data Type | Required | Constraints           |
|--------|------|-----------|----------|-----------------------|
| Path   | `id` | `integer` | Yes      | Not documented in context |

**Request Body**  
No request body documented in context.

**Responses**  
`200 OK`  
```json
{
    "message": "Check-in successful. Next trigger reset."
}
```
`404 Not Found`  
```json
{
    "detail": "Not found."
}
```

**Auth**  
`IsAuthenticated`

### `GET /api/actions/`
**Description**  
Retrieves a list of all available action types that can be configured for a Dead Man's Switch, along with their descriptions.

**Parameters**  
No parameters documented in context.

**Request Body**  
No request body documented in context.

**Responses**  
`200 OK`  
```json
[
    {
        "type": "email",
        "description": "Send an email to a specified recipient."
    },
    {
        "type": "webhook",
        "description": "Trigger a custom webhook URL."
    }
]
```

**Auth**  
`IsAuthenticated`

### `POST /api/webhook-test/`
**Description**  
Tests a webhook endpoint by sending a sample POST request to the provided URL. Useful for verifying webhook configurations.

**Parameters**  
| Type   | Name  | Data Type | Required | Constraints           |
|--------|-------|-----------|----------|-----------------------|
| Body   | `url` | `string`  | Yes      | Not documented in context |

**Request Body**  
```json
{
    "url": "https://webhook.site/abcdef12-3456-7890-abcd-ef1234567890"
}
```

**Responses**  
`200 OK`  
```json
{
    "status": 200,
    "response": "Webhook received successfully."
}
```
`400 Bad Request`  
```json
{
    "error": "URL required"
}
```
`400 Bad Request`  
```json
{
    "error": "Failed to connect to the webhook URL: Max retries exceeded with url:..."
}
```

**Auth**  
`IsAuthenticated`

### `GET /api/my-status/`
**Description**  
Retrieves a summary of the authenticated user's Dead Man's Switches, including counts of active and triggered switches, and the timestamp of their most recent check-in across all switches.

**Parameters**  
No parameters documented in context.

**Request Body**  
No request body documented in context.

**Responses**  
`200 OK`  
```json
{
    "active_switches": 2,
    "triggered_switches": 1,
    "last_checkin": "2024-01-15 11:30:00"
}
```
`200 OK`  
```json
{
    "active_switches": 0,
    "triggered_switches": 0,
    "last_checkin": null
}
```

**Auth**  
`IsAuthenticated`