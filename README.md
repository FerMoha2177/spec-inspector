# OpenAPI 3.1 Spec Inspector

## What is this?

This is a minimal, production-ready API for validating and correcting OpenAPI 3.1 (Swagger) specification files. It provides:
- Suggestions: Clear list of issues found in your uploaded spec
- Corrected Spec: Complete, OpenAPI 3.1-compliant YAML
- Working API: Upload a file, get validation and AI-powered corrections in one step

## How it works

1. User uploads a YAML file via the `/inspect` endpoint
2. The API validates the file and checks for issues
3. If problems are found, the API uses Claude Sonnet to generate suggestions and a corrected specification
4. The response contains both:
   - A list of suggestions (what's wrong and how to fix it)
   - The corrected YAML spec (ready to copy-paste)

## Why this is a great MVP

- No unnecessary features. Just upload, validate, and fix.
- No file storage, buckets, or downloads. All results are returned in the API response.
- Clean output: suggestions and the fixed spec.
- Works with Postman or any HTTP client.

## Usage

### Main Endpoint

- **POST `/inspect`**
  - Upload your OpenAPI YAML file as form-data (key: `file`)
  - Response: JSON with `suggestions` and `corrected_spec`

### Health Check Endpoints

- **GET `/api/v1/health`**
  - Returns basic health status of the API (200 OK if running)

- **GET `/api/v1/health/quick-test`**
  - Checks if the Claude LLM is reachable and responding
  - Returns a quick status and timestamp

- **GET `/api/v1/health/detailed`**
  - Returns detailed information about the API, environment, and LLM service status

#### Example health check response

```json
{
  "status": "healthy",
  "timestamp": "2025-07-27T06:34:00Z",
  "message": "SpecInspector API"
}
```

### Example response

```
{
  "status": "success",
  "filename": "example.yaml",
  "validation_passed": false,
  "suggestions": "- Missing 'info' section\n- Version field required\n...",
  "corrected_spec": "openapi: 3.1.0\ninfo: ... (fixed YAML here)"
}
```

## Running locally

1. Install dependencies: `pip install -r backend/requirements.txt`
2. Set your environment variables in `.env` (see `.env.example`)
3. Start the API: `uvicorn backend.api.main:app --reload`
4. Upload files to `/inspect` using Postman or curl

## Docker Setup

You can run the API in Docker using the provided scripts and compose file. This is the fastest way to get up and running in a consistent environment.

### Quick Start with local_run.sh

From the project root, run:

```sh
./devel/local_run.sh start
```

This script will:
- Check that Docker and docker-compose are installed and running
- Set up your `.env` file if needed
- Create all necessary data and log directories
- Build and start the API container using Docker Compose

Once started, the API will be available at `http://localhost:8000`.

### Manual Docker Compose Usage

Alternatively, you can run Docker Compose directly:

```sh
cd devel
# Build and start the API
docker-compose up --build
```

### Stopping and Cleaning Up

To stop the containers:

```sh
./devel/local_run.sh stop
```

To remove all containers, networks, and volumes:

```sh
./devel/local_run.sh cleanup
```

For more options, run:

```sh
./devel/local_run.sh help
```

## Optional improvements

- Test with more OpenAPI files
- Add more robust error handling
- Expand test coverage

## That's it!

This project is ready for code review and demo. Simple, clean, and solves the problem without over-engineering.
