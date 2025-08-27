# YouTube Disappeared Video Tracker - API Documentation

## Overview

This document describes the REST API endpoints for the YouTube Disappeared Video Tracker application.

**Base URL**: `https://your-app.fly.dev/api/v1`  
**Authentication**: API Key (YouTube Data API v3)  
**Content Type**: `application/json`

---

## Channel Management

### Register Channel
```http
POST /api/channels
Content-Type: application/json

{
  "input": "<channel_url|@handle|channel_id>"
}
```

**Description**: Register a new channel for monitoring (max 10)  
**Input Examples**:
- `https://www.youtube.com/channel/UCxxx`
- `https://www.youtube.com/@handle`
- `https://www.youtube.com/c/channelname`
- `@handle`
- `UCxxx` (raw channel ID)

**Response**: `201 Created`
```json
{
  "channel": {
    "id": "UCxxxxxx",
    "title": "Channel Name",
    "description": "Channel description",
    "thumbnail_url": "https://...",
    "subscriber_count": 1000000,
    "source_input": "@handle",
    "is_active": true,
    "added_at": "2025-08-27T10:30:00Z"
  },
  "message": "Channel registered successfully"
}
```

### List Registered Channels
```http
GET /api/channels
```

Returns list of user-registered channels.

**Response**:
```json
{
  "channels": [
    {
      "id": "UCxxxxxx",
      "name": "Channel Name",
      "description": "Channel description",
      "subscriber_count": 1000000,
      "thumbnail_url": "https://...",
      "is_monitored": true,
      "last_checked": "2025-01-15T10:30:00Z",
      "video_count": 150,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20
}
```

---

### Remove Channel
```http
DELETE /api/channels/{channelId}
```

Remove a channel from monitoring.

**Parameters**:
- `channelId` (string): YouTube channel ID to remove

**Response**: `200 OK`
```json
{
  "message": "Channel removed successfully",
  "channel_id": "UCxxxxxx"
}
```

---

### Reorder Channels (Optional)
```http
POST /api/channels/reorder
Content-Type: application/json

{
  "order": ["UCxxx", "UCyyy", "UCzzz"]
}
```

Update the display order of registered channels.

**Body**: Array of channel IDs in desired order

**Response**: `200 OK`
```json
{
  "message": "Channel order updated successfully",
  "order": ["UCxxx", "UCyyy", "UCzzz"]
}
```

---

### Get Channel Videos
```http
GET /api/channels/{channel_id}/videos
```

Returns videos for a specific channel with filtering options.

**Parameters**:
- `channel_id` (string): YouTube channel ID

**Query Parameters**:
- `status` (string, optional): Filter by status (`active`, `missing`, `private`, `deleted`)
- `from_date` (string, optional): ISO date string for date range start
- `to_date` (string, optional): ISO date string for date range end
- `page` (integer, optional): Page number (default: 1)
- `per_page` (integer, optional): Items per page (default: 20, max: 100)

**Response**:
```json
{
  "videos": [
    {
      "id": "dQw4w9WgXcQ",
      "channel_id": "UCxxxxxx",
      "title": "Video Title",
      "description": "Video description...",
      "upload_date": "2025-01-10T15:30:00Z",
      "duration": "PT3M42S",
      "thumbnail_url": "https://...",
      "view_count": 50000,
      "like_count": 1500,
      "status": "active",
      "created_at": "2025-01-10T16:00:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "per_page": 20,
  "channel": {
    "id": "UCxxxxxx",
    "name": "Channel Name"
  }
}
```

---

## Video Management

### List Videos
```http
GET /api/videos
```

Returns videos across all monitored channels with filtering options.

**Query Parameters**:
- `status` (string, optional): Filter by status
- `channel_id` (string, optional): Filter by channel
- `search` (string, optional): Search in title and description
- `from_date` (string, optional): ISO date string for date range start
- `to_date` (string, optional): ISO date string for date range end
- `page` (integer, optional): Page number
- `per_page` (integer, optional): Items per page

**Response**: Similar to channel videos endpoint but across all channels

---

### Get Video Details
```http
GET /api/videos/{video_id}
```

Returns detailed information about a specific video.

**Parameters**:
- `video_id` (string): YouTube video ID

**Response**:
```json
{
  "video": {
    "id": "dQw4w9WgXcQ",
    "channel_id": "UCxxxxxx",
    "channel_name": "Channel Name",
    "title": "Video Title",
    "description": "Video description...",
    "upload_date": "2025-01-10T15:30:00Z",
    "duration": "PT3M42S",
    "thumbnail_url": "https://...",
    "view_count": 50000,
    "like_count": 1500,
    "status": "active",
    "created_at": "2025-01-10T16:00:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
  }
}
```

---

### Get Video Change History
```http
GET /api/videos/{video_id}/history
```

Returns change history for a specific video.

**Parameters**:
- `video_id` (string): YouTube video ID

**Response**:
```json
{
  "changes": [
    {
      "id": 1,
      "video_id": "dQw4w9WgXcQ",
      "change_type": "modified",
      "old_value": {
        "title": "Old Title",
        "view_count": 45000
      },
      "new_value": {
        "title": "New Title",
        "view_count": 50000
      },
      "detected_at": "2025-01-15T10:30:00Z",
      "confirmed_at": "2025-01-15T10:35:00Z"
    }
  ],
  "total": 5,
  "video": {
    "id": "dQw4w9WgXcQ",
    "title": "Current Title"
  }
}
```

---

## Export Endpoints

### Export Videos CSV
```http
GET /api/export/videos.csv
```

Exports video data as CSV file.

**Query Parameters**:
- `channel_id` (string, optional): Filter by channel
- `status` (string, optional): Filter by status
- `from_date` (string, optional): Date range start
- `to_date` (string, optional): Date range end

**Response**: `200 OK` with CSV file
```
Content-Type: text/csv
Content-Disposition: attachment; filename="videos_export_20250115.csv"
```

---

### Export Changes CSV
```http
GET /api/export/changes.csv
```

Exports change log as CSV file.

**Query Parameters**: Similar to videos export

**Response**: `200 OK` with CSV file

---

## Dashboard & Statistics

### Get Dashboard Summary
```http
GET /api/dashboard/summary
```

Returns summary statistics for the dashboard.

**Response**:
```json
{
  "summary": {
    "total_channels": 10,
    "monitored_channels": 8,
    "total_videos": 1500,
    "active_videos": 1450,
    "missing_videos": 50,
    "recent_changes": 25,
    "last_scan": "2025-01-15T10:30:00Z"
  },
  "recent_activity": [
    {
      "type": "video_missing",
      "video_id": "abc123",
      "video_title": "Missing Video Title",
      "channel_name": "Channel Name",
      "detected_at": "2025-01-15T09:15:00Z"
    }
  ]
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "bad_request",
  "message": "Invalid request parameters",
  "details": {
    "field": "channel_id",
    "issue": "Invalid channel ID format"
  }
}
```

### 401 Unauthorized
```json
{
  "error": "unauthorized",
  "message": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "error": "forbidden",
  "message": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "error": "not_found",
  "message": "Resource not found"
}
```

### 429 Too Many Requests
```json
{
  "error": "rate_limit_exceeded",
  "message": "API rate limit exceeded",
  "retry_after": 60
}
```

### 500 Internal Server Error
```json
{
  "error": "internal_error",
  "message": "An unexpected error occurred"
}
```

---

## Rate Limiting

- **General API**: 1000 requests per hour per user
- **Export endpoints**: 10 requests per hour per user
- **YouTube API operations**: Subject to YouTube Data API v3 quotas

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642248000
```

---

*Current version: v1.0.0*
