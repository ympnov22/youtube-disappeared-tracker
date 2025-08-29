# YouTube Disappeared Video Tracker

A personal practice project to track YouTube channel uploads and detect disappeared videos using the YouTube Data API v3.

## Overview

This application monitors subscribed YouTube channels for video changes, storing metadata and detecting when videos become unavailable or are removed. It provides a web interface for viewing channel timelines and exporting data.

## Features

- Register up to 10 channels via web UI using URLs, @handles, or channel IDs
- Store video metadata (no downloads)
- Detect NEW / CHANGED / MISSING videos through periodic diffing
- Simple web UI with dashboard and channel timeline
- CSV export functionality
- Optional notifications (Slack/email) for daily missing video summaries
- Deploy on Fly.io (Tokyo region)

## Project Structure

```
/app
  /api          # API endpoints
  /core         # Core business logic
  /jobs         # Background jobs and schedulers
  /models       # Data models
  /services     # External service integrations
  /web          # Web UI components
/tests          # Test files
/docs           # Documentation
  specification.md
  phases.md
  api.md
  operations.md
/.github        # GitHub templates
  /ISSUE_TEMPLATE
    feature_request.md
    phase_report.md
  pull_request_template.md
```

## Development

### Prerequisites
- Python 3.12+
- Poetry for dependency management
- PostgreSQL 15+
- Redis 7+
- YouTube Data API v3 key

### Setup
```bash
# Clone repository
git clone https://github.com/ympnov22/youtube-disappeared-tracker.git
cd youtube-disappeared-tracker

# Install dependencies
poetry install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
poetry run alembic upgrade head

# Start the application
poetry run uvicorn app.main:app --reload
```

### Testing
```bash
# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app

# Run linting
poetry run black .
poetry run isort .
poetry run flake8 .
poetry run mypy app
```

## Fly.io Deployment Configuration

### Core Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `app` | `youtube-tracker` | Application name on Fly.io |
| `primary_region` | `nrt` | Tokyo region for low latency to Japanese users |
| `cpu_kind` | `shared` | Shared CPU for cost optimization |
| `cpus` | `1` | Single CPU core |
| `memory_mb` | `512` | 512MB RAM allocation |
| `internal_port` | `8080` | Application port inside container |

### Scaling Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `auto_stop_machines` | `true` | Stop machines when idle to save costs |
| `auto_start_machines` | `true` | Start machines on incoming requests |
| `min_machines_running` | `0` | No always-on machines (cost optimization) |
| `max_machines_running` | `3` | Maximum 3 machines for high traffic |
| `hard_limit` | `25` | Maximum concurrent connections per machine |
| `soft_limit` | `20` | Soft limit for connection handling |

### Health Check Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `grace_period` | `10s` | Time to wait before first health check |
| `interval` | `30s` | Health check frequency |
| `timeout` | `10s` | Health check timeout |
| `path` | `/healthz` | Health check endpoint |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `production` | Application environment |
| `SCAN_ENABLED` | `false` | Background scanning (disabled by default) |
| `SLACK_MIN_SEVERITY` | `MEDIUM` | Minimum alert severity |
| `SLACK_NOTIFICATION_LANGUAGE` | `en` | Notification language (en/ja) |
| `SLACK_RENOTIFICATION_HOURS` | `24` | Hours between re-notifications |

### Deployment Commands

```bash
# Deploy application
make deploy

# Rollback to previous version
make rollback

# Rollback to specific version
make rollback-to VERSION=123

# Check deployment status
make status

# View logs
make logs
```

This project follows a phased development approach with clear milestones and documentation requirements.

For detailed development guidelines and operational procedures, see [Project Guidelines](docs/project_guidelines.md).

## License

MIT License
