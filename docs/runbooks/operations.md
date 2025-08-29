# Operations Runbook

## Overview

**English**: This runbook provides comprehensive operational procedures for deploying, scaling, maintaining, and troubleshooting the YouTube Disappeared Video Tracker application.

**Japanese**: このランブックは、YouTube Disappeared Video Trackerアプリケーションのデプロイ、スケーリング、メンテナンス、トラブルシューティングに関する包括的な運用手順を提供します。

## Deployment Procedures

### Prerequisites

#### Required Tools
- Fly.io CLI (`flyctl`)
- Docker (for local testing)
- Git (for version control)
- Poetry (for dependency management)

#### Required Secrets
- `YOUTUBE_API_KEY`: YouTube Data API v3 key
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `APP_SECRET_KEY`: Application secret key
- `SESSION_SECRET`: Session encryption key

### Production Deployment

#### Initial Deployment

1. **Prepare Application**
   ```bash
   # Clone repository
   git clone https://github.com/ympnov22/youtube-disappeared-tracker.git
   cd youtube-disappeared-tracker
   
   # Install dependencies
   poetry install
   
   # Run tests
   poetry run pytest --cov=app --cov-report=term-missing
   ```

2. **Configure Fly.io Application**
   ```bash
   # Login to Fly.io
   fly auth login
   
   # Create application
   fly apps create youtube-tracker-prod --org your-org
   
   # Set region (Tokyo)
   fly regions set nrt
   ```

3. **Set Environment Variables**
   ```bash
   fly secrets set YOUTUBE_API_KEY="your-api-key"
   fly secrets set DATABASE_URL="postgresql://..."
   fly secrets set REDIS_URL="redis://..."
   fly secrets set APP_SECRET_KEY="your-secret-key"
   fly secrets set SESSION_SECRET="your-session-secret"
   fly secrets set SCAN_ENABLED="true"
   fly secrets set SCAN_INTERVAL_MINUTES="60"
   fly secrets set SCAN_CONCURRENCY="2"
   fly secrets set SCAN_BATCH_SIZE="10"
   ```

4. **Deploy Application**
   ```bash
   fly deploy --app youtube-tracker-prod
   ```

5. **Verify Deployment**
   ```bash
   # Check application status
   fly status --app youtube-tracker-prod
   
   # Check health endpoint
   curl https://youtube-tracker-prod.fly.dev/health
   
   # Check logs
   fly logs --app youtube-tracker-prod
   ```

#### Update Deployment

1. **Pre-deployment Checks**
   ```bash
   # Ensure on correct branch
   git checkout main
   git pull origin main
   
   # Run tests locally
   poetry run pytest --cov=app --cov-report=term-missing
   poetry run black --check .
   poetry run isort --check-only .
   poetry run flake8 .
   poetry run mypy app
   ```

2. **Deploy Update**
   ```bash
   # Deploy with zero-downtime
   fly deploy --app youtube-tracker-prod --strategy rolling
   ```

3. **Post-deployment Verification**
   ```bash
   # Check deployment status
   fly status --app youtube-tracker-prod
   
   # Verify health check
   curl https://youtube-tracker-prod.fly.dev/health
   
   # Monitor logs for errors
   fly logs --app youtube-tracker-prod --follow
   ```

#### Rollback Procedures

**English**: Comprehensive rollback procedures for Fly.io deployment recovery and incident response.

**Japanese**: Fly.ioデプロイメントの復旧とインシデント対応のための包括的なロールバック手順。

1. **Immediate Rollback (Standard)**
   ```bash
   # List recent releases with details
   fly releases --app youtube-tracker-prod
   
   # Check current release status
   fly status --app youtube-tracker-prod
   
   # Rollback to previous version (recommended)
   fly releases rollback --app youtube-tracker-prod
   
   # Verify rollback success
   curl https://youtube-tracker-prod.fly.dev/health
   fly logs --app youtube-tracker-prod | tail -20
   ```

2. **Rollback to Specific Version**
   ```bash
   # View release history with timestamps
   fly releases --app youtube-tracker-prod --json | jq '.[] | {version, created_at, status}'
   
   # Rollback to specific release (replace v123 with actual version)
   fly releases rollback v123 --app youtube-tracker-prod
   
   # Monitor rollback progress
   fly status --app youtube-tracker-prod --watch
   ```

3. **Emergency Rollback (Force)**
   ```bash
   # Force rollback (bypasses health checks) - USE WITH CAUTION
   fly releases rollback --force --app youtube-tracker-prod
   
   # Alternative: Deploy previous known-good commit
   git checkout <previous-commit-hash>
   fly deploy --app youtube-tracker-prod --strategy immediate
   ```

4. **Rollback Verification Checklist**
   - [ ] Health endpoint responds: `curl https://youtube-tracker-prod.fly.dev/health`
   - [ ] Admin interface accessible: `curl -u admin:pass https://youtube-tracker-prod.fly.dev/admin/channels`
   - [ ] Database connectivity confirmed in health check
   - [ ] Background jobs running (if SCAN_ENABLED=true)
   - [ ] No error spikes in logs: `fly logs --app youtube-tracker-prod`
   - [ ] Slack notifications working (if configured)

5. **Post-Rollback Actions**
   ```bash
   # Document rollback in incident log
   echo "$(date): Rolled back from v$(fly releases --app youtube-tracker-prod | head -2 | tail -1 | awk '{print $1}') due to [reason]" >> rollback-log.txt
   
   # Notify stakeholders
   # Update incident tracking system
   # Schedule post-incident review
   
   # Monitor for 30 minutes post-rollback
   fly logs --app youtube-tracker-prod --follow
   ```

6. **Rollback Failure Recovery**
   ```bash
   # If rollback fails, try alternative approaches:
   
   # Option 1: Scale down and up to force restart
   fly scale count 0 --app youtube-tracker-prod
   sleep 30
   fly scale count 1 --app youtube-tracker-prod
   
   # Option 2: Deploy from known-good Git commit
   git checkout <last-known-good-commit>
   fly deploy --app youtube-tracker-prod --strategy immediate
   
   # Option 3: Create new app instance (last resort)
   fly apps create youtube-tracker-recovery --org your-org
   fly secrets import --app youtube-tracker-recovery < secrets-backup.txt
   fly deploy --app youtube-tracker-recovery
   # Update DNS/load balancer to point to recovery instance
   ```

### Staging Environment

#### Setup Staging
```bash
# Create staging app
fly apps create youtube-tracker-staging --org your-org

# Set staging-specific secrets
fly secrets set --app youtube-tracker-staging YOUTUBE_API_KEY="staging-api-key"
fly secrets set --app youtube-tracker-staging DATABASE_URL="postgresql://staging..."
fly secrets set --app youtube-tracker-staging REDIS_URL="redis://staging..."
fly secrets set --app youtube-tracker-staging APP_SECRET_KEY="staging-secret"
fly secrets set --app youtube-tracker-staging SESSION_SECRET="staging-session"
fly secrets set --app youtube-tracker-staging SCAN_ENABLED="false"

# Deploy to staging
fly deploy --app youtube-tracker-staging
```

#### Staging Deployment Process
1. Deploy to staging first
2. Run integration tests
3. Verify functionality
4. Deploy to production if staging tests pass

## Scaling Guidelines

### Horizontal Scaling

#### Scale Up
```bash
# Increase instance count
fly scale count 3 --app youtube-tracker-prod

# Scale specific regions
fly scale count 2 --region nrt --app youtube-tracker-prod
```

#### Scale Down
```bash
# Decrease instance count
fly scale count 1 --app youtube-tracker-prod
```

### Vertical Scaling

#### Memory Scaling
```bash
# Scale memory (available: 256mb, 512mb, 1gb, 2gb, 4gb, 8gb)
fly scale memory 1gb --app youtube-tracker-prod
```

#### CPU Scaling
```bash
# Scale CPU (shared-cpu-1x, dedicated-cpu-1x, dedicated-cpu-2x, etc.)
fly scale vm dedicated-cpu-1x --app youtube-tracker-prod
```

### Auto-scaling Configuration

Update `fly.toml`:
```toml
[http_service]
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1
  max_machines_running = 5

[[http_service.checks]]
  grace_period = "10s"
  interval = "30s"
  method = "GET"
  path = "/health"
  timeout = "5s"
```

### Scaling Decision Matrix

| Metric | Threshold | Action |
|--------|-----------|--------|
| CPU Usage | > 80% for 10 min | Scale up CPU or add instances |
| Memory Usage | > 85% for 5 min | Scale up memory |
| Response Time | > 2s for 95th percentile | Scale up or optimize |
| Error Rate | > 5% for 5 min | Investigate and potentially scale |
| Queue Depth | > 100 jobs | Scale background workers |

## Backup and Recovery

### Database Backup

#### Automated Backups
- Fly.io PostgreSQL provides automated daily backups
- Backups retained for 7 days (configurable)
- Point-in-time recovery available

#### Manual Backup
```bash
# Create manual backup
fly postgres backup create --app youtube-tracker-prod-db

# List backups
fly postgres backup list --app youtube-tracker-prod-db
```

#### Backup Verification
```bash
# Test backup restoration (staging environment)
fly postgres backup restore <backup-id> --app youtube-tracker-staging-db
```

### Application Configuration Backup

#### Environment Variables
```bash
# Export current secrets (for backup)
fly secrets list --app youtube-tracker-prod > secrets-backup.txt

# Restore secrets from backup
fly secrets import --app youtube-tracker-prod < secrets-backup.txt
```

#### Code Backup
- All code stored in Git repository
- Tagged releases for each deployment
- Automated CI/CD pipeline preserves deployment artifacts

### Recovery Procedures

#### Database Recovery

1. **Point-in-time Recovery**
   ```bash
   # Restore to specific timestamp
   fly postgres backup restore --timestamp "2025-08-28T10:00:00Z" --app youtube-tracker-prod-db
   ```

2. **Full Database Recovery**
   ```bash
   # Restore from backup
   fly postgres backup restore <backup-id> --app youtube-tracker-prod-db
   ```

3. **Partial Data Recovery**
   ```sql
   -- Connect to database
   fly postgres connect --app youtube-tracker-prod-db
   
   -- Restore specific tables from backup
   pg_restore --table=channels backup.sql
   ```

#### Application Recovery

1. **Configuration Recovery**
   ```bash
   # Restore from Git
   git checkout <commit-hash>
   fly deploy --app youtube-tracker-prod
   ```

2. **Complete Environment Recovery**
   ```bash
   # Recreate application
   fly apps create youtube-tracker-recovery --org your-org
   
   # Restore secrets
   fly secrets import --app youtube-tracker-recovery < secrets-backup.txt
   
   # Deploy application
   fly deploy --app youtube-tracker-recovery
   
   # Update DNS if necessary
   fly certs create youtube-tracker.yourdomain.com --app youtube-tracker-recovery
   ```

## Incident Response Procedures

### Incident Classification

#### Severity 1 (Critical)
- **Definition**: Complete service outage, data loss, security breach
- **Response Time**: < 15 minutes
- **Escalation**: Immediate notification to all stakeholders

#### Severity 2 (High)
- **Definition**: Significant performance degradation, major feature unavailable
- **Response Time**: < 1 hour
- **Escalation**: Notification to development team and management

#### Severity 3 (Medium)
- **Definition**: Minor performance issues, non-critical feature problems
- **Response Time**: < 4 hours
- **Escalation**: Standard development team notification

#### Severity 4 (Low)
- **Definition**: Cosmetic issues, enhancement requests
- **Response Time**: Next business day
- **Escalation**: Standard ticket queue

### Incident Response Steps

#### Initial Response (First 15 minutes)
1. **Acknowledge Incident**
   - Confirm incident severity
   - Notify relevant stakeholders
   - Create incident tracking ticket

2. **Immediate Assessment**
   - Check application health: `curl https://youtube-tracker-prod.fly.dev/health`
   - Review recent deployments: `fly releases --app youtube-tracker-prod`
   - Check system metrics: `fly status --app youtube-tracker-prod`

3. **Initial Mitigation**
   - If recent deployment caused issue: `fly releases rollback --app youtube-tracker-prod`
   - If resource exhaustion: `fly scale memory 2gb --app youtube-tracker-prod`
   - If external service issue: Enable maintenance mode

#### Investigation Phase
1. **Gather Information**
   ```bash
   # Check logs
   fly logs --app youtube-tracker-prod | tail -100
   
   # Check metrics
   fly status --app youtube-tracker-prod
   
   # Check database
   fly postgres connect --app youtube-tracker-prod-db
   ```

2. **Root Cause Analysis**
   - Review code changes
   - Check external service status
   - Analyze performance metrics
   - Review error patterns

3. **Document Findings**
   - Timeline of events
   - Root cause identification
   - Impact assessment

#### Resolution Phase
1. **Implement Fix**
   - Code fix and deployment
   - Configuration changes
   - Infrastructure adjustments

2. **Verify Resolution**
   - Functional testing
   - Performance validation
   - Monitoring confirmation

3. **Communication**
   - Update stakeholders
   - Document resolution
   - Schedule post-incident review

### Emergency Contacts

#### Internal Team
- **Primary On-call**: Development Team Lead
- **Secondary On-call**: DevOps Engineer
- **Escalation**: Engineering Manager

#### External Services
- **Fly.io Support**: support@fly.io
- **Google Cloud Support**: For YouTube API issues
- **Database Support**: For database-specific problems

## Database Maintenance

### Regular Maintenance Tasks

#### Daily
- Monitor database performance metrics
- Check backup completion status
- Review slow query logs

#### Weekly
- Analyze query performance trends
- Update database statistics
- Review and optimize indexes

#### Monthly
- Perform database health check
- Review storage usage and growth
- Update maintenance procedures

### Database Operations

#### Connection Management
```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Kill long-running queries
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
WHERE state = 'active' AND query_start < now() - interval '1 hour';
```

#### Performance Monitoring
```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check table sizes
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### Index Maintenance
```sql
-- Check unused indexes
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0;

-- Rebuild indexes if needed
REINDEX INDEX CONCURRENTLY index_name;
```

### Migration Procedures

#### Database Schema Updates
```bash
# Run migrations
fly ssh console --app youtube-tracker-prod
cd /app
poetry run alembic upgrade head
```

#### Data Migration
```bash
# Create migration script
poetry run alembic revision --autogenerate -m "migration description"

# Review migration before applying
poetry run alembic show head

# Apply migration
poetry run alembic upgrade head
```

#### Rollback Migrations
```bash
# Rollback to previous version
poetry run alembic downgrade -1

# Rollback to specific version
poetry run alembic downgrade <revision_id>
```

## Security Procedures

### Security Monitoring

#### Regular Security Checks
- Review access logs for suspicious activity
- Monitor failed authentication attempts
- Check for unusual API usage patterns
- Verify SSL certificate status

#### Security Updates
```bash
# Check for security updates
poetry update

# Run security audit
poetry run safety check

# Run security linting
poetry run bandit -r app/
```

### Access Management

#### API Key Rotation
```bash
# Generate new YouTube API key in Google Cloud Console
# Update secret
fly secrets set YOUTUBE_API_KEY="new-api-key" --app youtube-tracker-prod

# Verify application still works
curl https://youtube-tracker-prod.fly.dev/health
```

#### Database Credentials Rotation
```bash
# Update database password in Fly.io dashboard
# Update DATABASE_URL secret
fly secrets set DATABASE_URL="postgresql://new-credentials..." --app youtube-tracker-prod

# Restart application
fly deploy --app youtube-tracker-prod
```

### Incident Response for Security Issues

#### Security Breach Response
1. **Immediate Actions**
   - Isolate affected systems
   - Revoke compromised credentials
   - Enable additional logging

2. **Assessment**
   - Determine scope of breach
   - Identify compromised data
   - Document timeline

3. **Remediation**
   - Patch vulnerabilities
   - Update security measures
   - Notify affected users if required

4. **Recovery**
   - Restore from clean backups if necessary
   - Implement additional security controls
   - Monitor for continued threats

## Monitoring and Alerting

### Key Metrics Dashboard

#### Application Metrics
- Request rate and response times
- Error rates by endpoint
- Background job completion rates
- YouTube API quota usage

#### Infrastructure Metrics
- CPU and memory utilization
- Database connection pool usage
- Redis memory usage and hit rates
- Network I/O and latency

#### Business Metrics
- Active channels being monitored
- Videos scanned per hour
- Disappearance events detected
- User activity levels

### Alert Configuration

#### Critical Alerts
```yaml
# Application down
- alert: ApplicationDown
  expr: up{job="youtube-tracker"} == 0
  for: 2m
  
# High error rate
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
  for: 5m

# Database connection failure
- alert: DatabaseConnectionFailure
  expr: postgresql_up == 0
  for: 1m
```

#### Warning Alerts
```yaml
# High response time
- alert: HighResponseTime
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
  for: 10m

# High memory usage
- alert: HighMemoryUsage
  expr: memory_usage_percent > 85
  for: 15m
```

## Capacity Planning

### Growth Projections

#### User Growth
- Monitor user registration trends
- Plan for seasonal variations
- Consider viral growth scenarios

#### Data Growth
- Track database size growth
- Monitor video metadata accumulation
- Plan for long-term storage needs

#### API Usage Growth
- Monitor YouTube API quota usage trends
- Plan for increased scanning frequency
- Consider API cost implications

### Resource Planning

#### Compute Resources
- Monitor CPU and memory trends
- Plan for peak usage periods
- Consider auto-scaling thresholds

#### Storage Resources
- Track database growth rates
- Plan for backup storage needs
- Monitor log storage requirements

#### Network Resources
- Monitor bandwidth usage
- Plan for increased API calls
- Consider CDN requirements for static assets

## Release Management

### Release Tagging Workflow

**English**: Production deployments are triggered by Git tags following semantic versioning.

**Japanese**: 本番デプロイメントは、セマンティックバージョニングに従うGitタグによってトリガーされます。

#### Creating a Release

1. **Prepare Release**:
   ```bash
   # Ensure all tests pass
   make test
   make lint
   
   # Update CHANGELOG.md with release notes
   # Commit all changes
   git add .
   git commit -m "chore: prepare release v1.2.3"
   ```

2. **Create and Push Tag**:
   ```bash
   # Create annotated tag
   git tag -a v1.2.3 -m "Release v1.2.3: Phase 5 hardening and UX improvements"
   
   # Push tag to trigger deployment
   git push origin v1.2.3
   ```

3. **Monitor Deployment**:
   ```bash
   # Watch GitHub Actions
   gh run watch
   
   # Check Fly.io deployment status
   make status
   
   # Verify health
   make health
   ```

### Rollback Procedures

#### Automatic Rollback (Recommended)

```bash
# Rollback to previous version
make rollback

# Rollback to specific version
make rollback-to VERSION=123

# List available versions
make list-releases
```

#### Manual Rollback

```bash
# List releases
flyctl releases --app youtube-tracker

# Rollback to specific release
flyctl releases rollback --app youtube-tracker --version 123

# Verify rollback
flyctl status --app youtube-tracker
```

#### Rollback Verification

1. **Health Check**: `make health`
2. **Functionality Test**: Test critical user flows
3. **Log Monitoring**: `make logs` for 5-10 minutes
4. **Slack Notifications**: Verify alerts are working

### Emergency Procedures

#### Application Down

1. **Immediate Response**:
   ```bash
   # Check status
   make status
   
   # View recent logs
   make logs
   
   # Restart if needed
   flyctl restart --app youtube-tracker
   ```

2. **If Restart Fails**: `make rollback`

3. **If Rollback Fails**: Contact Fly.io support

#### Database Issues

1. **Check Database Status**:
   ```bash
   flyctl postgres list
   flyctl postgres status --app youtube-tracker-db
   ```

2. **Connection Issues**: Verify `DATABASE_URL` secret

3. **Performance Issues**: Check slow query logs

#### High Resource Usage

1. **Scale Up Temporarily**:
   ```bash
   # Increase memory
   flyctl scale memory 1024 --app youtube-tracker
   
   # Add more machines
   flyctl scale count 2 --app youtube-tracker
   ```

2. **Monitor and Investigate**: Use logs and metrics to identify cause

3. **Scale Down**: After issue resolution

---

**Last Updated**: August 29, 2025
**Version**: 1.1.0
**Next Review**: September 29, 2025
