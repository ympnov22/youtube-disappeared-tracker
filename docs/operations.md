# YouTube Disappeared Video Tracker - Operations Guide

## Overview

This document provides operational guidance for deploying, monitoring, and maintaining the YouTube Disappeared Video Tracker application.

---

## Environment Setup

### Required Environment Variables

#### Core Application
```bash
# Application Configuration
APP_ENV=production
APP_DEBUG=false
APP_SECRET_KEY=your-secret-key-here
APP_BASE_URL=https://your-app.fly.dev

# Database Configuration
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://user:password@host:port/database

# YouTube API Configuration
YOUTUBE_API_KEY=your-youtube-api-key

# Session Configuration
SESSION_SECRET=your-session-secret
SESSION_TIMEOUT=3600
```

#### Optional Services
```bash
# Slack Notifications (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SLACK_CHANNEL=#youtube-tracker

# Email Notifications (Optional)
EMAIL_SERVICE_PROVIDER=sendgrid
EMAIL_API_KEY=your-email-api-key
EMAIL_FROM_ADDRESS=noreply@yourdomain.com

# Monitoring (Optional)
SENTRY_DSN=https://your-sentry-dsn
LOG_LEVEL=INFO
```

### Development Environment
```bash
# Development overrides
APP_ENV=development
APP_DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://localhost:5432/youtube_tracker_dev
REDIS_URL=redis://localhost:6379/0
```

---

## Deployment

### Fly.io Deployment

#### Initial Setup
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login to Fly.io
fly auth login

# Initialize Fly app
fly launch --name youtube-tracker --region nrt
```

#### Configuration Files

**fly.toml**
```toml
app = "youtube-tracker"
primary_region = "nrt"

[build]
  dockerfile = "Dockerfile"

[env]
  APP_ENV = "production"
  PORT = "8080"

[[services]]
  http_checks = []
  internal_port = 8080
  processes = ["app"]
  protocol = "tcp"
  script_checks = []

  [services.concurrency]
    hard_limit = 25
    soft_limit = 20
    type = "connections"

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [[services.tcp_checks]]
    grace_period = "1s"
    interval = "15s"
    restart_limit = 0
    timeout = "2s"

[checks]
  [checks.health]
    grace_period = "5s"
    interval = "30s"
    method = "get"
    path = "/health"
    port = 8080
    protocol = "http"
    restart_limit = 0
    timeout = "10s"
```

#### Database Setup
```bash
# Create PostgreSQL database
fly postgres create --name youtube-tracker-db --region nrt

# Attach database to app
fly postgres attach --app youtube-tracker youtube-tracker-db

# Create Redis instance
fly redis create --name youtube-tracker-redis --region nrt
```

#### Environment Variables
```bash
# Set environment variables
fly secrets set YOUTUBE_API_KEY=your-api-key
fly secrets set APP_SECRET_KEY=your-secret-key
fly secrets set SESSION_SECRET=your-session-secret

# Optional: Set notification secrets
fly secrets set SLACK_WEBHOOK_URL=your-slack-webhook
fly secrets set EMAIL_API_KEY=your-email-key
```

#### Deploy Application
```bash
# Deploy to production
fly deploy

# Check deployment status
fly status

# View logs
fly logs
```

---

## Monitoring & Logging

### Health Checks

#### Application Health Endpoint
```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "youtube_api": "healthy"
  },
  "metrics": {
    "uptime": 86400,
    "memory_usage": "45%",
    "cpu_usage": "12%"
  }
}
```

#### Key Metrics to Monitor
- **API Response Times**: YouTube API call latencies
- **Job Success Rates**: Background job completion rates
- **Error Rates**: Application and API error frequencies
- **Resource Usage**: CPU, memory, database connections
- **Rate Limit Usage**: YouTube API quota consumption

### Alerting Rules

#### Critical Alerts
- Application down (health check fails)
- Database connection failures
- YouTube API authentication failures
- High error rates (>5% over 5 minutes)

#### Warning Alerts
- High API quota usage (>80% daily limit)
- Job queue backlog (>100 pending jobs)
- High response times (>5s average)
- Memory usage >80%

---

## Backup & Recovery

### Database Backup

#### Automated Backups (Fly.io)
```bash
# Fly.io automatically backs up PostgreSQL databases
# View backup status
fly postgres db list --app youtube-tracker-db

# Create manual backup
fly postgres backup create --app youtube-tracker-db
```

#### Manual Backup
```bash
# Create database dump
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
psql $DATABASE_URL < backup_20250115_103000.sql
```

### Recovery Procedures

#### Application Recovery
1. Check application logs: `fly logs`
2. Verify environment variables: `fly secrets list`
3. Check database connectivity: `fly postgres connect`
4. Restart application: `fly restart`
5. Monitor health endpoint: `/health`

#### Database Recovery
1. Identify backup to restore from
2. Stop application: `fly scale count 0`
3. Restore database from backup
4. Run database migrations if needed
5. Restart application: `fly scale count 1`
6. Verify data integrity

---

## Maintenance Tasks

### Daily Tasks
- [ ] Check application health status
- [ ] Review error logs for issues
- [ ] Monitor API quota usage
- [ ] Verify background jobs are running

### Weekly Tasks
- [ ] Review performance metrics
- [ ] Check database growth and optimization
- [ ] Update dependencies if needed
- [ ] Review and clean up old logs

### Monthly Tasks
- [ ] Full backup verification
- [ ] Security updates and patches
- [ ] Performance optimization review
- [ ] Capacity planning assessment

---

## Troubleshooting

### Common Issues

#### YouTube API Rate Limiting
**Symptoms**: 403 errors, quota exceeded messages
**Solutions**:
1. Check current quota usage in Google Cloud Console
2. Implement exponential backoff in API calls
3. Optimize API usage patterns
4. Request quota increase if needed

#### Database Connection Issues
**Symptoms**: Connection timeouts, pool exhaustion
**Solutions**:
1. Check database server status
2. Review connection pool configuration
3. Optimize long-running queries
4. Scale database resources if needed

#### Background Job Failures
**Symptoms**: Jobs stuck in queue, processing errors
**Solutions**:
1. Check Redis connectivity
2. Review job error logs
3. Restart job workers
4. Clear failed job queue if needed

### Debug Commands

#### Application Debugging
```bash
# View application logs
fly logs --app youtube-tracker

# Connect to application console
fly ssh console --app youtube-tracker

# Check environment variables
fly secrets list --app youtube-tracker

# Scale application
fly scale count 2 --app youtube-tracker
```

#### Database Debugging
```bash
# Connect to database
fly postgres connect --app youtube-tracker-db

# Check database size
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Check active connections
SELECT count(*) FROM pg_stat_activity;
```

---

## Security Considerations

### API Security
- Use HTTPS for all communications
- Secure API key management for YouTube Data API access
- Rate limiting on all endpoints
- Input validation and sanitization
- CORS configuration for web interface

### Data Security
- Encrypt sensitive data at rest
- Use environment variables for secrets
- Regular security updates
- Access logging and monitoring
- Backup encryption

### Infrastructure Security
- Network security groups
- Regular OS updates
- Firewall configuration
- SSL/TLS certificate management
- Intrusion detection

---

## Performance Optimization

### Database Optimization
```sql
-- Add indexes for common queries
CREATE INDEX idx_videos_channel_id ON videos(channel_id);
CREATE INDEX idx_videos_status ON videos(status);
CREATE INDEX idx_videos_upload_date ON videos(upload_date);
CREATE INDEX idx_change_log_video_id ON change_log(video_id);
CREATE INDEX idx_change_log_detected_at ON change_log(detected_at);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM videos WHERE channel_id = 'UCxxxxxx';
```

### Application Optimization
- Implement caching for frequently accessed data
- Use connection pooling for database connections
- Optimize API call batching
- Implement pagination for large datasets
- Use background jobs for heavy operations

---

*Last Updated: 2025-08-27*  
*Version: 1.0.0*
