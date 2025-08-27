# YouTube Disappeared Video Tracker

A personal practice project to track YouTube channel uploads and detect disappeared videos using the YouTube Data API v3.

## Overview

This application monitors subscribed YouTube channels for video changes, storing metadata and detecting when videos become unavailable or are removed. It provides a web interface for viewing channel timelines and exporting data.

## Features

- Track subscribed channels via YouTube Data API v3 (OAuth youtube.readonly)
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

This project follows a phased development approach with clear milestones and documentation requirements.

## License

MIT License
