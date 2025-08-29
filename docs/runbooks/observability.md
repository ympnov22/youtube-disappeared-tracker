# Observability Runbook

## Overview

**English**: This runbook provides comprehensive guidance for monitoring, observability, and troubleshooting the YouTube Disappeared Video Tracker application.

**Japanese**: このランブックは、YouTube Disappeared Video Trackerアプリケーションの監視、観測可能性、トラブルシューティングに関する包括的なガイダンスを提供します。

## Monitoring Setup

### Key Metrics to Track

#### Application Metrics
- **API Response Times**: Monitor `/api/channels`, `/api/videos`, `/api/scan` endpoints
- **Error Rates**: Track 4xx and 5xx HTTP status codes
- **Request Volume**: Monitor requests per second and daily active users
- **Background Job Performance**: Track scan completion times and failure rates

#### Infrastructure Metrics
- **Database Performance**: Connection pool usage, query execution times
- **Redis Performance**: Memory usage, connection count, command latency
- **System Resources**: CPU usage, memory consumption, disk I/O

#### Business Metrics
- **Channel Monitoring**: Number of active channels, scan frequency
- **Video Detection**: New videos found, disappeared videos detected
- **User Activity**: Channel registrations, API usage patterns

### Monitoring Stack

#### Recommended Tools
1. **Application Performance Monitoring (APM)**
   - Sentry for error tracking and performance monitoring
   - Configure via `SENTRY_DSN` environment variable

2. **Infrastructure Monitoring**
   - Fly.io built-in metrics for basic system monitoring
   - Prometheus + Grafana for detailed metrics collection

3. **Log Aggregation**
   - Fly.io log aggregation for centralized logging
   - Structured logging with JSON format for better parsing

### Health Checks

#### Application Health Endpoint
```bash
curl https://your-app.fly.dev/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "background_jobs": {
    "enabled": true,
    "running": true,
    "next_run": "2025-08-28T11:00:00Z"
  }
}
```

#### Database Health Check
```sql
SELECT 1;
SELECT COUNT(*) FROM channels WHERE is_active = true;
```

#### Redis Health Check
```bash
redis-cli ping
redis-cli info memory
```

## Alerting Configuration

### Slack Notifications

#### Slack Alert Configuration
**English**: The application sends automated Slack notifications for video disappearance events when `SLACK_WEBHOOK_URL` is configured.

**Japanese**: `SLACK_WEBHOOK_URL`が設定されている場合、アプリケーションは動画消失イベントに対して自動的にSlack通知を送信します。

#### Slack Alert Types
1. **Video Disappearance Events**
   - **Trigger**: New `DisappearanceEvent` created (PRIVATE, DELETED, GEO_BLOCKED, AGE_RESTRICTED, UNKNOWN)
   - **Format**: Rich message with channel name, video title/ID, event type, detected timestamp
   - **Action Button**: "Check on YouTube" link to video URL
   - **Context**: View count, duration, published date (if available)

2. **Slack Alert Success Conditions**
   - **Success**: HTTP 200 response from Slack webhook within 10 seconds
   - **Logging**: Structured log entry with video_id, channel_id, event_type, detected_at
   - **Retry**: No automatic retry (fire-and-forget for performance)

3. **Slack Alert Failure Conditions**
   - **Timeout**: Request timeout > 10 seconds
   - **HTTP Error**: Non-200 response from Slack webhook
   - **Network Error**: Connection failure or DNS resolution failure
   - **Logging**: Warning-level logs with failure reason, no sensitive data exposure

#### Slack Alert Monitoring
- **Success Rate**: Monitor successful vs failed Slack notifications
- **Response Time**: Track webhook response times (target < 2 seconds)
- **Threshold**: Alert if Slack notification failure rate > 20% over 1 hour
- **Test Notifications**: Use `/admin/test-slack` endpoint for verification

#### Advanced Slack Configuration

**Environment Variables**:
- `SLACK_NOTIFICATION_LANGUAGE`: Language for notifications (`en` or `ja`, default: `en`)
- `SLACK_MIN_SEVERITY`: Minimum severity threshold (`LOW`, `MEDIUM`, `HIGH`, default: `LOW`)
- `SLACK_RENOTIFICATION_HOURS`: Hours between re-notifications for same video (default: `24`)
- `SLACK_MAX_NOTIFICATIONS_PER_VIDEO`: Maximum notifications per video (default: `3`)

**Severity Levels**:
- **HIGH**: DELETED events (🚨 immediate attention required)
- **MEDIUM**: PRIVATE, UNKNOWN events (⚠️ monitor and investigate)
- **LOW**: GEO_BLOCKED, AGE_RESTRICTED events (ℹ️ informational)

**Bilingual Support**:
- **English**: Default notification language with standard terminology
- **Japanese**: Full translation including event types, field labels, and button text
- **Language Detection**: Automatically uses configured language for all notifications

**Threshold Configuration Examples**:
```bash
# Only send high-severity alerts (DELETED videos only)
SLACK_MIN_SEVERITY=HIGH

# Send all alerts in Japanese
SLACK_NOTIFICATION_LANGUAGE=ja

# Reduce notification frequency (48 hours between re-notifications)
SLACK_RENOTIFICATION_HOURS=48
```

**Re-notification Rules**:
- Same video disappearance events respect `SLACK_RENOTIFICATION_HOURS` interval
- Maximum `SLACK_MAX_NOTIFICATIONS_PER_VIDEO` notifications per video lifetime
- Different event types for same video count as separate notification chains
- Manual channel scans bypass re-notification throttling

### Critical Alerts (Immediate Response Required)

1. **Application Down**
   - Condition: Health check fails for > 2 minutes
   - Action: Immediate investigation and restart if necessary

2. **Database Connection Failure**
   - Condition: Database connection errors > 5 in 1 minute
   - Action: Check database status and connection pool

3. **High Error Rate**
   - Condition: 5xx errors > 10% of requests for > 5 minutes
   - Action: Check application logs and recent deployments

4. **Background Jobs Stopped**
   - Condition: No successful scans for > 2 hours
   - Action: Check scheduler status and Redis connectivity

5. **Slack Notification Failure**
   - Condition: Slack notification failure rate > 50% for > 30 minutes
   - Action: Check SLACK_WEBHOOK_URL configuration and Slack service status

### Warning Alerts (Monitor and Plan Response)

1. **High Response Time**
   - Condition: 95th percentile response time > 2 seconds for > 10 minutes
   - Action: Monitor and investigate if trend continues

2. **YouTube API Quota Warning**
   - Condition: API quota usage > 80%
   - Action: Review scan frequency and optimize API calls

3. **High Memory Usage**
   - Condition: Memory usage > 85% for > 15 minutes
   - Action: Monitor for memory leaks and consider scaling

## Log Analysis

### Log Levels and Categories

#### Application Logs
- **ERROR**: Application errors, API failures, database issues
- **WARN**: Performance degradation, quota warnings, retry attempts
- **INFO**: Normal operations, scan completions, user actions
- **DEBUG**: Detailed execution flow (development only)

#### Log Format
```json
{
  "timestamp": "2025-08-28T10:35:00Z",
  "level": "INFO",
  "logger": "app.services.video_ingestion",
  "message": "Scanned channel UCtest123: added=5, updated=2, events=1",
  "channel_id": "UCtest123",
  "scan_results": {
    "added": 5,
    "updated": 2,
    "events": 1
  }
}
```

### Common Log Queries

#### Find Recent Errors
```bash
fly logs --app your-app | grep '"level":"ERROR"' | tail -20
```

#### Monitor Scan Performance
```bash
fly logs --app your-app | grep "Scanned channel" | tail -10
```

#### Track API Usage
```bash
fly logs --app your-app | grep "YouTube API" | tail -20
```

## Performance Monitoring

### Key Performance Indicators (KPIs)

1. **API Response Time**
   - Target: < 500ms for 95th percentile
   - Critical: > 2 seconds

2. **Background Job Completion**
   - Target: < 30 seconds per channel scan
   - Critical: > 5 minutes

3. **Database Query Performance**
   - Target: < 100ms for 95th percentile
   - Critical: > 1 second

4. **YouTube API Rate Limiting**
   - Target: < 80% of daily quota
   - Critical: > 95% of daily quota

### Performance Optimization

#### Database Optimization
- Monitor slow queries using PostgreSQL logs
- Ensure proper indexing on frequently queried columns
- Use connection pooling to manage database connections

#### API Optimization
- Implement caching for frequently accessed data
- Use batch operations where possible
- Monitor and optimize YouTube API call patterns

#### Background Job Optimization
- Adjust `SCAN_INTERVAL_MINUTES` based on channel activity
- Use `SCAN_BATCH_SIZE` to control resource usage
- Monitor Redis memory usage for job queuing

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Application Won't Start
**Symptoms**: Health check fails, application logs show startup errors

**Investigation Steps**:
1. Check environment variables are properly set
2. Verify database connectivity
3. Check Redis connectivity
4. Review application logs for specific error messages

**Solutions**:
- Restart the application: `fly deploy --app your-app`
- Check and update environment variables
- Verify external service connectivity

#### 2. High Memory Usage
**Symptoms**: Application becomes slow, potential out-of-memory errors

**Investigation Steps**:
1. Check memory usage: `fly status --app your-app`
2. Review application logs for memory-related errors
3. Monitor database connection pool usage

**Solutions**:
- Scale up memory: Update `fly.toml` and redeploy
- Optimize database queries and connection pooling
- Review background job batch sizes

#### 3. YouTube API Quota Exceeded
**Symptoms**: API calls fail with quota exceeded errors

**Investigation Steps**:
1. Check YouTube API usage in Google Cloud Console
2. Review scan frequency and batch sizes
3. Analyze API call patterns in logs

**Solutions**:
- Reduce scan frequency: Increase `SCAN_INTERVAL_MINUTES`
- Optimize API calls: Reduce `SCAN_BATCH_SIZE`
- Implement intelligent scanning based on channel activity

#### 4. Background Jobs Not Running
**Symptoms**: No recent scan logs, channels not being updated

**Investigation Steps**:
1. Check background job status: `curl /health`
2. Verify Redis connectivity
3. Check scheduler configuration

**Solutions**:
- Restart background jobs: Redeploy application
- Verify Redis connection and configuration
- Check `SCAN_ENABLED` environment variable

#### 5. Database Connection Issues
**Symptoms**: Database connection errors in logs

**Investigation Steps**:
1. Check database status in Fly.io dashboard
2. Verify `DATABASE_URL` environment variable
3. Monitor connection pool usage

**Solutions**:
- Restart database if necessary
- Update connection string if changed
- Optimize connection pool settings

## Incident Response Procedures

### Severity Levels

#### Severity 1 (Critical)
- Application completely down
- Data loss or corruption
- Security breach

**Response Time**: Immediate (< 15 minutes)
**Actions**:
1. Acknowledge incident
2. Assess impact and root cause
3. Implement immediate fix or rollback
4. Communicate status to stakeholders

#### Severity 2 (High)
- Significant performance degradation
- Feature unavailable
- High error rates

**Response Time**: < 1 hour
**Actions**:
1. Investigate root cause
2. Implement fix or workaround
3. Monitor for resolution
4. Document incident

#### Severity 3 (Medium)
- Minor performance issues
- Non-critical feature problems
- Warning alerts

**Response Time**: < 4 hours
**Actions**:
1. Schedule investigation
2. Plan and implement fix
3. Update monitoring if needed

### Post-Incident Review

After resolving any Severity 1 or 2 incident:

1. **Document Timeline**: Record what happened and when
2. **Root Cause Analysis**: Identify underlying cause
3. **Action Items**: Define preventive measures
4. **Update Runbooks**: Improve procedures based on learnings
5. **Share Learnings**: Communicate findings to team

## Maintenance Procedures

### Regular Maintenance Tasks

#### Daily
- Review error logs and alerts
- Check application health and performance metrics
- Monitor YouTube API quota usage

#### Weekly
- Review performance trends and capacity planning
- Update monitoring dashboards if needed
- Check for security updates and patches

#### Monthly
- Review and update alerting thresholds
- Analyze performance trends and optimization opportunities
- Update documentation and runbooks

### Backup and Recovery

#### Database Backups
- Automated daily backups via Fly.io PostgreSQL
- Test backup restoration monthly
- Document recovery procedures

#### Configuration Backups
- Environment variables stored in Fly.io secrets
- Application configuration in version control
- Document configuration restoration procedures

## Contact Information

### Escalation Path
1. **Primary**: Development Team
2. **Secondary**: DevOps/Infrastructure Team
3. **Emergency**: System Administrator

### External Services
- **Fly.io Support**: For infrastructure issues
- **Google Cloud Support**: For YouTube API issues
- **Database Provider**: For database-specific problems

---

**Last Updated**: August 28, 2025
**Version**: 1.0.0
**Next Review**: September 28, 2025
