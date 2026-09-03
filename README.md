# FirePredictionSystem Prediction Server

A Flask-based backend service that accepts fire-risk prediction requests from a [seperate interactive UI](https://github.com/devkulemannege/FirePredictionSystem-interactive-ui), retrieves Earth observation data from NASA AppEEARS, runs a trained machine learning model, and sends the prediction result to the user by email.

This project is designed to process requests asynchronously through a local queue so that long-running Earth data retrieval and prediction jobs do not block the API response.

## Overview

The service does the following:

1. Receives a prediction request over HTTP.
2. Validates Basic Authentication credentials.
3. Enqueues the request with the user's email, AppEEARS token, and task ID.
4. Starts a background worker thread.
5. Polls the AppEEARS task status until the dataset is ready.
6. Downloads the requested bundle files into a temporary folder.
7. Extracts the needed MODIS metrics (LST, NDVI, surface reflectance).
8. Loads a saved ML model (`model.pkl`) and calculates a fire prediction.
9. Sends an email notification with the result.

---

## Project Structure

```text
.
├── app.py                    # Flask app and API routes
├── model.pkl                 # Trained prediction model
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
├── modules/
│   ├── error_mail.py         # Code which executes when SMTP fails
│   ├── prediction_worker.py  # ML prediction and email result logic
│   ├── request_queue.py      # Queue implementation for queued requests
│   ├── worker.py             # Background job worker that polls AppEEARS
│   └── appeears_data/        # Temporary downloaded data directory
├── templates/
│   ├── emailNo.html
│   ├── emailYes.html
│   └── fail.html
└── trainer/
    ├── model_exporter.py
    └── training_dataset.csv
```

---

## Tech Stack

- Python 3
- Flask
- Flask-Limiter
- Pandas
- scikit-learn
- Requests
- Resend / HTTP email service
- NASA AppEEARS API

---

## Environment Variables

Create a `.env` file in the project root with values like:

```env
// to authenticate requests from interactive UI
API_USR=your_api_username 
API_PSW=your_api_password 

// connect your SMTP server by specifying variables
SMTP_KEY=your_smtp_key
SMTP_URL=your_smtp_server_url
```


The app expects HTTP Basic Auth for the `/transfer` endpoint. The same credentials are checked against `API_USR` and `API_PSW`.

---

## API Routes

### GET /

Health check endpoint.

- Method: `GET`
- Route: `/`
- Purpose: Confirms the service is running.
- Response:

```json
{
  "status": "ok"
}
```

- HTTP status: `200`
- Exempt from rate limiting.

#### What it does

This endpoint simply returns a basic status message to verify the Flask application is alive and serving requests.

---

### POST /transfer

Main request endpoint used to submit prediction jobs.

- Method: `POST`
- Route: `/transfer`
- Requires: HTTP Basic Authentication
- Request body (JSON):

```json
{
  "taskId": "APP_EAARS_TASK_ID",
  "token": "APP_EAARS_ACCESS_TOKEN",
  "email": "user@example.com"
}
```

#### Authentication behavior

The server reads the Basic Auth header with `request.authorization`.

- If no authorization header is supplied, it returns:

```json
{
  "status": "missing_authorization"
}
```

with HTTP status `401`.

- If credentials are present but do not match `API_USR` and `API_PSW`, it returns:

```json
{
  "status": "unauthorized"
}
```

with HTTP status `401`.

- If credentials are valid, the request is accepted and queued.

#### Successful request behavior

On success, the server:

1. Reads the JSON payload.
2. Calls `queue.enqueue(payload['taskId'], payload['token'], payload['email'])`.
3. Starts the worker process via `worker.start_worker(queue, app)`.
4. Returns:

```json
{
  "status": "ok"
}
```

with HTTP status `200`.

#### What it does in plain terms

This is the entry point for the fire prediction workflow. It accepts user data and hands off the heavy processing to the background worker so the API can respond quickly.

---

## Rate Limiting

The app uses Flask-Limiter with a per-email rate limit:

```python
default_limits=['10 per day']
```

The limiter key is based on the request email value (`get_email()`), meaning each email address is limited to 10 requests per day. The root health route (`/`) is exempt from this limiter.

**Note:** on an actual production implementation this would be configured differently.

---

## Request Queue

The request queue is implemented in `modules/request_queue.py`.

### Queue structure

- `Node`: stores `taskId`, `token`, and `email`
- `request_queue`: manages a FIFO queue with:
  - `enqueue()`
  - `dequeue()`
  - `getFront()`
  - `isEmpty()`

### Why it exists

The backend may receive many requests, but the prediction processing is a long-running operation. The queue ensures each job is handled in order and not all at once.

**Note:** this has been made in this manner in order to save system resources on  small headless servers *(RAM usage when a thread is active: 150MB ~ 300MB)*.

---

## Background Worker Process

The background worker is implemented in `modules/worker.py`.

### Worker lifecycle

- A singleton-style `WORKING` flag prevents multiple background workers from running at the same time.
- When a request is added to the queue, the app starts a new daemon thread.
- The thread calls `retrieve_data(queue, app)`.

### Worker responsibilities

The worker does the following:

1. Checks whether the queue is empty.
2. Dequeues the next request.
3. Builds an authorization header using the AppEEARS token.
4. Polls the AppEEARS task endpoint until the task status becomes `done`.
5. Downloads the result bundle files into `modules/appeears_data`.
6. Calls `prediction_worker.start(payload.email)` once the files are ready.
7. Deletes the temporary data directory after processing.

If there is an error at any step, it logs the exception and sends an error email using `error_mail.send(...)`.

---

## Prediction Workflow - Logistic Regression

The actual prediction logic lives in `modules/prediction_worker.py`.

### What it does

It processes the downloaded AppEEARS CSV files and extracts:

- LST (Land Surface Temperature)
- Surface reflectance band values
- NDVI (Normalized Difference Vegetation Index)
- Month value for seasonal context

It then builds a `promptSample` DataFrame like this:

```python
{
    'lst': [...],
    'sur_refl': [...],
    'ndvi': [...],
    'month': [...]
}
```

This is passed to the trained model in `model.pkl`:

```python
model = pickle.load(open('model.pkl', 'rb'))
rawPrediction = model.predict(promptSample)
```

### Result interpretation

- If prediction is `1`, it loads the positive email template (`emailYes.html`).
- Otherwise it loads the negative email template (`emailNo.html`).

The result is then sent via an HTTP POST to the configured email service.

---

## Email Flow

### Success email

The app uses the `templates` folder to render HTML email content:

- `emailYes.html` for a positive fire-risk prediction
- `emailNo.html` for a negative result

The payload includes:

- user email
- subject
- HTML content
- current date
- latitude and longitude

### Failure email

If AppEEARS or model processing fails, the app sends a failure email using `modules/error_mail.py`.

---

## How the Full Request Works

A complete request flow looks like this:

```text
Client -> POST /transfer
    -> Basic Auth validation
    -> Queue request
    -> Start background worker
    -> Poll AppEEARS task status
    -> Download files
    -> Read CSVs
    -> Compute inputs for ML model
    -> Predict fire risk
    -> Send email result
```

---

## Running the App

Install dependencies:

```bash
pip install -r requirements.txt
```

Then run:

```bash
python app.py
```

The Flask app listens on:

```text
0.0.0.0:8080
```

Example success response:

```json
{
  "status": "ok"
}
```

---

## Notes

- The service is not a traditional REST API with many endpoints; most of the logic is handled internally after a request is accepted.
- The app is intended for background processing and asynchronous prediction work.
- The model and processing pipeline depend on NASA AppEEARS output files being available in the expected format.


---

## Summary of Route Behavior

| Route | Method | Description |
| --- | --- | --- |
| `/` | GET | Health check; returns service status |
| `/transfer` | POST | Accepts prediction jobs, validates auth, queues the task, and starts background processing |
