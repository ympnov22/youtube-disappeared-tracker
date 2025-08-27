# YouTube Disappeared Video Tracker - Technical Specification

## 1. Project Overview

### 1.1 Purpose
The YouTube Disappeared Video Tracker is a personal practice project designed to monitor YouTube channels for video changes and detect when videos become unavailable or are removed. The system tracks metadata only (no video downloads) and provides insights into content availability over time.

### 1.2 Scope
- **MVP Focus**: Track subscribed channels, detect video changes, provide basic web UI
- **Authentication**: YouTube Data API v3 with OAuth (youtube.readonly scope)
- **Storage**: Metadata only - video titles, descriptions, thumbnails, upload dates
- **Detection**: Periodic diffing to identify NEW/CHANGED/MISSING videos
- **Interface**: Simple web dashboard with channel timeline view and CSV export
- **Notifications**: Optional Slack/email alerts for daily missing video summaries
- **Deployment**: Fly.io platform (Tokyo region)

## 2. Functional Requirements

### 2.1 Core Features

#### 2.1.1 Channel Management
- **FR-001**: User can authenticate with YouTube OAuth (youtube.readonly)
- **FR-002**: System fetches user's subscribed channels list
- **FR-003**: User can select which channels to monitor
- **FR-004**: System stores channel metadata (name, ID, description, subscriber count)

#### 2.1.2 Video Tracking
- **FR-005**: System periodically fetches video lists for monitored channels
- **FR-006**: System stores video metadata:
  - Video ID, title, description
  - Upload date, duration
  - Thumbnail URLs
  - View count, like count (if available)
  - Channel association
- **FR-007**: System detects video status changes:
  - NEW: Previously unseen videos
  - CHANGED: Modified metadata (title, description, etc.)
  - MISSING: Videos that no longer appear in channel listings

#### 2.1.3 Change Detection
- **FR-008**: System performs periodic diff operations between current and previous states
- **FR-009**: System confirms video disappearance using videos.list API call
- **FR-010**: System categorizes disappearance reasons:
  - Deleted by creator
  - Made private
  - Removed by YouTube
  - Temporarily unavailable

#### 2.1.4 Web Interface
- **FR-011**: Dashboard showing overview of monitored channels
- **FR-012**: Channel timeline view displaying video history and changes
- **FR-013**: Video status indicators (active, missing, changed)
- **FR-014**: Search and filter functionality for videos and channels
- **FR-015**: CSV export for video data and change history

#### 2.1.5 Notifications (Optional)
- **FR-016**: Daily summary of missing videos via Slack
- **FR-017**: Email notifications for significant changes
- **FR-018**: Configurable notification preferences

### 2.2 Non-Functional Requirements

#### 2.2.1 Performance
- **NFR-001**: API rate limiting compliance with YouTube Data API v3
- **NFR-002**: Efficient data storage and retrieval
- **NFR-003**: Background job processing for periodic updates

#### 2.2.2 Security
- **NFR-004**: Secure OAuth token storage and refresh
- **NFR-005**: Environment variable configuration for sensitive data
- **NFR-006**: No storage of actual video content

#### 2.2.3 Reliability
- **NFR-007**: Graceful handling of API errors and rate limits
- **NFR-008**: Data consistency during updates
- **NFR-009**: Logging and monitoring capabilities

## 3. Data Models

### 3.1 Channel Model
```
Channel:
  - id: string (YouTube channel ID)
  - name: string
  - description: string
  - subscriber_count: integer
  - thumbnail_url: string
  - created_at: datetime
  - updated_at: datetime
  - is_monitored: boolean
  - last_checked: datetime
```

### 3.2 Video Model
```
Video:
  - id: string (YouTube video ID)
  - channel_id: string (foreign key)
  - title: string
  - description: text
  - upload_date: datetime
  - duration: string
  - thumbnail_url: string
  - view_count: integer
  - like_count: integer
  - status: enum (active, missing, private, deleted)
  - created_at: datetime
  - updated_at: datetime
```

### 3.3 Change Log Model
```
ChangeLog:
  - id: integer (primary key)
  - video_id: string (foreign key)
  - change_type: enum (new, modified, missing)
  - old_value: json
  - new_value: json
  - detected_at: datetime
  - confirmed_at: datetime
```

## 4. API Specifications

### 4.1 External APIs

#### 4.1.1 YouTube Data API v3
- **Endpoint**: `https://www.googleapis.com/youtube/v3/`
- **Authentication**: OAuth 2.0 (youtube.readonly scope)
- **Key Operations**:
  - `subscriptions.list`: Get user's subscribed channels
  - `channels.list`: Get channel details
  - `search.list`: Get channel's videos
  - `videos.list`: Verify video existence and get details

#### 4.1.2 Rate Limiting
- **Quota**: 10,000 units per day (default)
- **Cost per operation**:
  - subscriptions.list: 1 unit
  - channels.list: 1 unit
  - search.list: 100 units
  - videos.list: 1 unit per video ID

### 4.2 Internal API Endpoints

#### 4.2.1 Authentication
- `GET /auth/youtube` - Initiate YouTube OAuth flow
- `GET /auth/callback` - Handle OAuth callback
- `POST /auth/logout` - Clear authentication

#### 4.2.2 Channels
- `GET /api/channels` - List monitored channels
- `POST /api/channels/{id}/monitor` - Start monitoring channel
- `DELETE /api/channels/{id}/monitor` - Stop monitoring channel
- `GET /api/channels/{id}/videos` - Get channel's videos

#### 4.2.3 Videos
- `GET /api/videos` - List videos with filters
- `GET /api/videos/{id}` - Get video details
- `GET /api/videos/{id}/history` - Get video change history

#### 4.2.4 Export
- `GET /api/export/videos.csv` - Export videos as CSV
- `GET /api/export/changes.csv` - Export change log as CSV

## 5. System Architecture

### 5.1 Components

#### 5.1.1 Web Application
- **Framework**: FastAPI (Python) or Express.js (Node.js)
- **Frontend**: React with TypeScript
- **Styling**: Tailwind CSS

#### 5.1.2 Background Jobs
- **Scheduler**: Periodic tasks for channel monitoring
- **Queue**: Job processing for API calls and data updates

#### 5.1.3 Database
- **Primary**: PostgreSQL for structured data
- **Caching**: Redis for temporary data and rate limiting

#### 5.1.4 External Services
- **YouTube API**: Video and channel data
- **Slack API**: Notifications (optional)
- **Email Service**: Notifications (optional)

### 5.2 Deployment

#### 5.2.1 Platform
- **Primary**: Fly.io (Tokyo region)
- **Configuration**: Environment variables for secrets
- **Scaling**: Single instance initially, horizontal scaling capability

#### 5.2.2 Environment Variables
```
YOUTUBE_CLIENT_ID=<oauth_client_id>
YOUTUBE_CLIENT_SECRET=<oauth_client_secret>
DATABASE_URL=<postgresql_connection_string>
REDIS_URL=<redis_connection_string>
SLACK_WEBHOOK_URL=<slack_webhook_url> (optional)
EMAIL_SERVICE_KEY=<email_service_key> (optional)
```

## 6. User Interface Composition

### 6.1 Dashboard Page
- **Header**: Navigation, user info, logout
- **Summary Cards**: Total channels, videos tracked, recent changes
- **Channel List**: Monitored channels with status indicators
- **Recent Activity**: Latest video changes and discoveries

### 6.2 Channel Timeline Page
- **Channel Header**: Name, subscriber count, monitoring status
- **Timeline View**: Chronological list of videos with status indicators
- **Filters**: Date range, status (active/missing), search
- **Actions**: Export, toggle monitoring

### 6.3 Video Details Modal
- **Video Info**: Title, description, upload date, metrics
- **Change History**: Timeline of detected changes
- **Status**: Current availability and reason for changes

### 6.4 Settings Page
- **Channel Management**: Add/remove monitored channels
- **Notification Preferences**: Slack/email configuration
- **Export Options**: CSV download settings
- **Account**: OAuth status, re-authentication

## 7. Implementation Notes

### 7.1 Development Approach
- **Phase-based development** with clear milestones
- **Documentation-first** approach with continuous updates
- **Test-driven development** for core functionality
- **Bilingual documentation** (English + Japanese) for reports

### 7.2 Key Considerations
- **API Rate Limiting**: Implement exponential backoff and quota management
- **Data Consistency**: Handle concurrent updates and API failures gracefully
- **Privacy**: Store only necessary metadata, respect user privacy
- **Scalability**: Design for future expansion to multiple users

### 7.3 Success Criteria
- **Functional**: Successfully detect video disappearances with <5% false positives
- **Performance**: Complete channel scan within rate limit constraints
- **Usability**: Intuitive web interface requiring minimal user training
- **Reliability**: 99% uptime with graceful error handling
