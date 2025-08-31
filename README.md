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
- Deploy on Render (free tier)

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

## Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/ympnov22/youtube-disappeared-tracker)

### Quick Deploy

1. Click the "Deploy to Render" button above
2. Set the required environment variables:
   - `SLACK_WEBHOOK_URL`: Your Slack webhook URL for notifications (optional)
   - `YOUTUBE_API_KEY`: YouTube Data API v3 key (required)
   - `REDIS_URL`: Redis connection URL (provided by Render)
   - `ENV`: Set to `production`

### Using the Web UI

After deployment, the application provides a public web interface at the root URL:

**English**:
- **Home Page**: Access the main interface at `/` to interact with the tracker
- **Channel Scanning**: Enter a YouTube channel ID (UCxxxxx format) to trigger manual scans
- **Video Listing**: View all videos for a specific channel with status filtering (active/missing)
- **Event Monitoring**: Browse disappearance events with filtering by channel, event type, and date
- **API Documentation**: Access interactive API docs at `/docs`

**Japanese**:
- **ホームページ**: `/` でメインインターフェースにアクセスしてトラッカーを操作
- **チャンネルスキャン**: YouTubeチャンネルID（UCxxxxx形式）を入力して手動スキャンを実行
- **動画一覧**: 特定チャンネルの全動画をステータスフィルタ（アクティブ/消失）で表示
- **イベント監視**: チャンネル、イベントタイプ、日付でフィルタリングして消失イベントを閲覧
- **API文書**: `/docs` でインタラクティブなAPI文書にアクセス

### Health Check Endpoints

The application provides health check endpoints for monitoring:
- `/health`: Basic health status
- `/ready`: Readiness check including database connectivity

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `YOUTUBE_API_KEY` | Yes | YouTube Data API v3 access key |
| `SLACK_WEBHOOK_URL` | No | Slack webhook for notifications |
| `REDIS_URL` | Yes | Redis connection URL (auto-provided by Render) |
| `DATABASE_URL` | Yes | PostgreSQL connection URL (auto-provided by Render) |
| `APP_SECRET_KEY` | Yes | Secret key for application security |
| `SESSION_SECRET` | Yes | Secret key for session management |
| `ENV` | Yes | Set to `production` for production deployment |

### Render Configuration

The application is configured for Render deployment with:
- **Service Type**: Web service
- **Plan**: Free tier compatible
- **Health Check**: `/health` endpoint
- **Auto Deploy**: Enabled for main branch
- **Port**: Automatically configured via `$PORT` environment variable

### Deployment Platform Status

**Primary Platform**: Render (active auto-deploy)
- Auto-deploy enabled for `main` branch
- Health checks configured
- Environment variables managed via Render dashboard

**Secondary Platform**: Fly.io (dormant)
- Configuration maintained in `fly.toml` for future use
- Deployment workflows disabled by default in CI
- To re-enable: Remove `if: false` from `.github/workflows/release.yml` and restore `FLY_API_TOKEN` secret

This project follows a phased development approach with clear milestones and documentation requirements.

For detailed development guidelines and operational procedures, see [Project Guidelines](docs/project_guidelines.md).

## License

MIT License
