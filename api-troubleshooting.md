# API Troubleshooting

> A practical guide to understanding and troubleshooting common API issues in SaaS and web applications.

## Purpose

APIs allow different software systems to communicate with each other.

When an API-related problem occurs, technical support should identify the request, inspect the response, determine whether the issue is related to authentication, permissions, data, configuration, or the server, and collect evidence for escalation when necessary.

## Common HTTP Methods

### GET

Used to retrieve information.

Example: GET /users/123

### POST

Used to create or submit information.

Example: POST /users

### PUT

Used to update an existing resource.

Example: PUT /users/123

### DELETE

Used to remove a resource.

Example: DELETE /users/123

## Common HTTP Status Codes

### 200 — OK

The request was successful.

### 201 — Created

The request successfully created a resource.

### 400 — Bad Request

The server could not process the request because the request was invalid.

Possible causes:

- Missing required fields
- Invalid data
- Incorrect request format

### 401 — Unauthorized

Authentication is required or the authentication credentials are invalid.

Possible causes:

- Missing authentication token
- Expired token
- Invalid credentials

### 403 — Forbidden

The server understood the request but refused to authorize it.

Possible causes:

- Insufficient permissions
- Restricted resource
- Account access limitations

### 404 — Not Found

The requested resource or endpoint could not be found.

Possible causes:

- Incorrect URL
- Incorrect endpoint
- Resource does not exist

### 500 — Internal Server Error

The server encountered an unexpected problem while processing the request.

This may require investigation by the application or engineering team.

## API Troubleshooting Process

### 1. Identify the Endpoint

Record the API endpoint involved in the issue.

Example:

https://example.com/api/users/123

### 2. Identify the HTTP Method

Determine whether the request uses:

- GET
- POST
- PUT
- DELETE

### 3. Check the Status Code

The HTTP status code provides an important starting point for investigation.

Examples:

- 200 = successful request
- 400 = invalid request
- 401 = authentication problem
- 403 = authorization problem
- 404 = resource not found
- 500 = server-side error

### 4. Inspect the Response

Look at the response body for useful information.

Example response:

{
  "error": "Invalid customer ID"
}

The response may provide information about what went wrong.

### 5. Check the Request

For requests that send data, verify:

- Request URL
- HTTP method
- Headers
- Authentication
- Request parameters
- Request body
- Data format

### 6. Check Authentication and Permissions

Determine whether the user or application has the required access.

Check for:

- Authentication tokens
- Expired credentials
- Missing permissions
- Incorrect account configuration

### 7. Reproduce the Request

If possible, reproduce the API request using an appropriate tool or browser developer tools.

Record:

- Request
- Response
- Status code
- Timestamp
- Relevant error message

### 8. Escalate With Evidence

If the issue cannot be resolved by support, provide the technical team with:

- Endpoint
- HTTP method
- Status code
- Timestamp
- Request details
- Response details
- Error message
- Steps to reproduce
- Customer impact

Do not include passwords, authentication tokens, API keys, or other sensitive credentials in an escalation.

## Example Investigation

### Problem

A customer reports that a system integration is failing.

### Investigation

1. Identify the API endpoint.
2. Confirm the HTTP method.
3. Record the timestamp.
4. Check the HTTP status code.
5. Inspect the response.
6. Verify authentication.
7. Verify permissions.
8. Check the request data.
9. Reproduce the request if possible.
10. Document the evidence.
11. Resolve or escalate based on the findings.

## Key Principle

API troubleshooting should be evidence-based.

A useful sequence is:

**Identify Endpoint → Check Method → Check Status Code → Inspect Request → Inspect Response → Verify Authentication → Reproduce → Resolve or Escalate**
