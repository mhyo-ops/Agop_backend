# Agrotech Backend Frontend Integration Guide

This document describes exactly how the frontend should connect to the backend, what data to send, and how to use the IDs returned by the API.

## Backend startup

Run from the project root:

```bash
uvicorn main:app --reload
```

The API will be available at:

- `http://127.0.0.1:8000`

API docs are available at:

- `http://127.0.0.1:8000/docs`

## CORS

CORS is already enabled for all origins in `main.py`:

- `allow_origins=["*"]`
- `allow_methods=["*"]`
- `allow_headers=["*"]`

So the frontend can call the backend from another origin such as `http://localhost:3000`.

## Base URL

```text
http://127.0.0.1:8000
```

## Authentication / Session

The backend does not currently use JWT or token authentication. The frontend should:

- call `POST /users/login` to verify credentials
- store the returned `user_id` and `username` in app state or local storage
- use `user_id` as `farmer_id` when calling crop endpoints

## ID usage

- `user_id` from login/register becomes `farmer_id` for crop access
- `crop_id` identifies a crop for details, logs, recommendations, and tasks
- `task_id` identifies a task for update or delete operations

## Endpoints

### 1. Register user

`POST /users/register`

Request body:

```json
{
  "username": "farmer1",
  "email": "email@example.com",
  "phone": "0123456789",
  "password": "secret"
}
```

Response example:

```json
{
  "id": 1,
  "username": "farmer1",
  "email": "email@example.com",
  "phone": "0123456789",
  "created_at": "2026-04-15T00:00:00"
}
```

### 2. Login user

`POST /users/login`

Request body:

```json
{
  "email": "email@example.com",
  "password": "secret"
}
```

Response example:

```json
{
  "message": "Login successful",
  "user_id": 1,
  "username": "farmer1"
}
```

> Frontend should store `user_id` and use it as `farmer_id`.

### 3. Create crop

`POST /crops/?farmer_id={farmer_id}`

Request body:

```json
{
  "crop_name": "Maize",
  "field_name": "Field A",
  "soil_type": "Loam",
  "area": 3.5,
  "growth_stage": "germination",
  "planting_date": "2026-04-15T00:00:00"
}
```

Response example:

```json
{
  "id": 1,
  "farmer_id": 1,
  "crop_name": "Maize",
  "field_name": "Field A",
  "soil_type": "Loam",
  "area": 3.5,
  "growth_stage": "germination",
  "planting_date": "2026-04-15T00:00:00",
  "created_at": "2026-04-15T00:00:00"
}
```

### 4. Get crops for a farmer

`GET /crops/?farmer_id={farmer_id}`

Response example:

```json
[
  {
    "id": 1,
    "farmer_id": 1,
    "crop_name": "Maize",
    "field_name": "Field A",
    "soil_type": "Loam",
    "area": 3.5,
    "growth_stage": "germination",
    "planting_date": "2026-04-15T00:00:00",
    "created_at": "2026-04-15T00:00:00"
  }
]
```

### 5. Get crop by id

`GET /crops/{crop_id}`

Response example:

```json
{
  "id": 1,
  "farmer_id": 1,
  "crop_name": "Maize",
  "field_name": "Field A",
  "soil_type": "Loam",
  "area": 3.5,
  "growth_stage": "germination",
  "planting_date": "2026-04-15T00:00:00",
  "created_at": "2026-04-15T00:00:00"
}
```

### 6. Delete crop

`DELETE /crops/{crop_id}`

No request body.

Response:

- `204 No Content` on success

### 7. Submit a daily log

`POST /logs/`

Request body:

```json
{
  "crop_id": 1,
  "water_quantity": 25.0,
  "fertilizer_qty": 5.0
}
```

Response example:

```json
{
  "id": 1,
  "crop_id": 1,
  "water_quantity": 25.0,
  "fertilizer_qty": 5.0,
  "logged_at": "2026-04-15T00:00:00"
}
```

### 8. Get logs by crop

`GET /logs/{crop_id}`

Response example:

```json
[
  {
    "id": 1,
    "crop_id": 1,
    "water_quantity": 25.0,
    "fertilizer_qty": 5.0,
    "logged_at": "2026-04-15T00:00:00"
  }
]
```

### 9. Create recommendation

`POST /recommendations/`

Request body:

```json
{
  "crop_id": 1,
  "message": "Add more nitrogen fertilizer.",
  "recommendation_type": "fertilizer"
}
```

Response example:

```json
{
  "id": 1,
  "crop_id": 1,
  "message": "Add more nitrogen fertilizer.",
  "recommendation_type": "fertilizer",
  "created_at": "2026-04-15T00:00:00"
}
```

### 10. Get recommendations by crop

`GET /recommendations/{crop_id}`

Response example:

```json
[
  {
    "id": 1,
    "crop_id": 1,
    "message": "Add more nitrogen fertilizer.",
    "recommendation_type": "fertilizer",
    "created_at": "2026-04-15T00:00:00"
  }
]
```

### 11. Create task

`POST /tasks/`

Request body:

```json
{
  "crop_id": 1,
  "description": "Check soil moisture",
  "due_date": "2026-04-18T00:00:00"
}
```

Response example:

```json
{
  "id": 1,
  "crop_id": 1,
  "description": "Check soil moisture",
  "due_date": "2026-04-18T00:00:00",
  "is_done": false,
  "created_at": "2026-04-15T00:00:00"
}
```

### 12. Get tasks by crop

`GET /tasks/{crop_id}`

Response example:

```json
[
  {
    "id": 1,
    "crop_id": 1,
    "description": "Check soil moisture",
    "due_date": "2026-04-18T00:00:00",
    "is_done": false,
    "created_at": "2026-04-15T00:00:00"
  }
]
```

### 13. Update task status

`PUT /tasks/{task_id}`

Request body:

```json
{
  "is_done": true
}
```

Response example:

```json
{
  "id": 1,
  "crop_id": 1,
  "description": "Check soil moisture",
  "due_date": "2026-04-18T00:00:00",
  "is_done": true,
  "created_at": "2026-04-15T00:00:00"
}
```

### 14. Delete task

`DELETE /tasks/{task_id}`

No request body.

Response:

- `204 No Content` on success

## JSON examples and frontend contract

The frontend should use the exact field names shown above.

The `schemas/` folder in the backend is a good reference for the exact shape of requests and responses, but this document is the frontend contract.

## Example frontend usage

### Fetch example

```js
const baseUrl = "http://127.0.0.1:8000";

async function login(email, password) {
  const response = await fetch(`${baseUrl}/users/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return response.json();
}

async function getCrops(userId) {
  const response = await fetch(`${baseUrl}/crops/?farmer_id=${userId}`);
  return response.json();
}
```

### Axios example

```js
import axios from "axios";

const api = axios.create({ baseURL: "http://127.0.0.1:8000" });

export function login(email, password) {
  return api.post("/users/login", { email, password });
}

export function getCrops(userId) {
  return api.get(`/crops/?farmer_id=${userId}`);
}
```

## Recommended frontend workflow

1. Register or login the user.
2. Save `user_id` and `username`.
3. Load crops using `GET /crops/?farmer_id={user_id}`.
4. Use crop cards or a crop details page to store `crop_id`.
5. Use `crop_id` for logs, recommendations, and tasks.
6. Use `task_id` for updating or deleting tasks.

## Notes

- Dates should be sent as ISO strings like `2026-04-15T00:00:00`.
- All request bodies are JSON.
- The backend returns error responses in JSON with a `detail` field.
- Because authentication is minimal, protect the user session on the frontend manually.
