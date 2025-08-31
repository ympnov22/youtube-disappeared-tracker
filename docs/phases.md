# YouTube Disappeared Video Tracker - Development Phases

## Phase Overview

This project will be developed in incremental phases, each building upon the previous phase's deliverables. Each phase requires user approval before proceeding to the next phase.

---

## Phase 0: Project Bootstrap & Foundation
**Status**: ✅ Complete  
**Duration**: 3 hours  
**Branch**: `devin/1756288215-phase0-bootstrap` (merged to main)

### Objectives
- Set up project repository structure
- Create comprehensive documentation
- Establish development workflow
- Initialize basic project scaffolding

### Tasks
- [x] Create repository structure (`/app`, `/tests`, `/docs`, `/.github`)
- [x] Write technical specification document
- [x] Create phases breakdown document
- [x] Set up GitHub issue templates and PR template
- [x] Initialize Docker configuration with multi-stage build
- [x] Create initial API documentation structure
- [x] Set up CI/CD workflow (GitHub Actions) with security, test, and build checks
- [x] Initialize git repository with proper branch structure
- [x] Implement Continuity Kit for session handoffs
- [x] Resolve CI issues (security vulnerabilities, Docker build fixes)

### Deliverables
- Complete project structure
- `docs/specification.md` - Technical specification
- `docs/phases.md` - This phases document
- `docs/api.md` - API documentation skeleton
- `docs/operations.md` - Operations guide skeleton
- GitHub templates for issues and PRs
- `Dockerfile` and `docker-compose.yml`
- `README.md` with project overview
- Initial git repository with `main` branch

### Success Criteria
- All documentation is complete and accurate
- Project structure follows specified conventions
- Git workflow is properly configured
- Ready for Phase 1 development

---

## Phase 1: Channel Management & Resolver
**Status**: 🚀 Ready to Start  
**Duration**: 3-4 hours  
**Branch**: `devin/{timestamp}-phase1-channels`

### Objectives
- Implement user-managed channel registration system (max 10 channels)
- Create channel resolver to handle URLs, @handles, and channel IDs
- Build channel management API with CRUD operations
- Create channel management UI with usage counter and validation

### Tasks

#### Channels API Implementation
- [ ] **POST /channels** - Add new channel with input validation
  - Accept: Full channel URL (/channel/UC…, /@handle, /user/..., /c/...)
  - Accept: @handle format
  - Accept: Raw channelId (UC…)
  - Validate: Max 10 active channels per user
  - Validate: No duplicate channels
  - Return: channelId, title, source_input, added_at
- [ ] **GET /channels** - List all registered channels
  - Return: channelId, title, source_input, added_at, is_active
  - Include: Usage counter (X/10 used)
- [ ] **DELETE /channels/{channelId}** - Remove channel
  - Validate: Channel exists and belongs to user
  - Soft delete: Set is_active = false
- [ ] **POST /channels/reorder** (optional) - Reorder channels
  - Accept: Array of channelIds in desired order

#### Channel Resolver Service
- [ ] **URL Parser** - Extract channel info from various URL formats
  - Handle: youtube.com/channel/UC...
  - Handle: youtube.com/@handle
  - Handle: youtube.com/user/username
  - Handle: youtube.com/c/customname
- [ ] **YouTube API Integration** - Resolve to canonical channel data
  - Use: YouTube Data API v3 with API key (no OAuth)
  - Resolve: @handle → channelId via search
  - Fetch: Channel title, uploads playlist ID
  - Handle: API rate limiting and errors
- [ ] **Channel Validator** - Ensure channel exists and is accessible
  - Verify: Channel exists via channels.list API
  - Extract: uploads_playlist_id for video fetching
  - Store: Original source_input for user reference

#### Channels Management UI
- [ ] **Settings → Channels Page** - Main channel management interface
  - Input box with placeholder: "Enter channel URL, @handle, or channel ID"
  - "Add Channel" button with loading state
  - Channel list with: title, channelId, added date, status
  - Remove button for each channel
  - Usage indicator: "7/10 channels used"
  - Error handling for invalid inputs, duplicates, limit exceeded
- [ ] **Channel List Component** - Display registered channels
  - Show: Channel thumbnail, title, subscriber count (if available)
  - Show: Added date, source input format
  - Action: Remove button with confirmation dialog
- [ ] **Add Channel Form** - Input validation and feedback
  - Real-time validation of input format
  - Loading state during resolution
  - Success/error messages
  - Auto-clear input on successful add

#### Database Schema Updates
- [ ] **ALTER TABLE channels** - Add new fields for user-managed channels
  ```sql
  ALTER TABLE channels
    ADD COLUMN source_input TEXT,
    ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true,
    ADD COLUMN added_at TIMESTAMP NOT NULL DEFAULT now();
  
  CREATE UNIQUE INDEX IF NOT EXISTS ux_channels_id ON channels(id);
  ```

#### Testing & Documentation
- [ ] **Unit Tests** - Channel operations and validation
  - Test: URL parsing for all supported formats
  - Test: API endpoint validation and error handling
  - Test: 10-channel limit enforcement
  - Test: Duplicate prevention logic
- [ ] **Integration Tests** - YouTube API integration
  - Test: Channel resolution via API
  - Test: Error handling for invalid channels
  - Test: Rate limiting behavior
- [ ] **API Documentation** - Update docs/api.md with new endpoints

### Deliverables
- **Channel Management API** - Complete CRUD operations with validation
- **Channel Resolver Service** - URL/handle to channelId conversion
- **Channel Management UI** - User-friendly settings page
- **Database Schema** - Updated with new channel fields
- **YouTube API Client** - API key-based integration (no OAuth)
- **Test Suite** - Comprehensive unit and integration tests
- **Documentation** - Updated API docs and user guides

### Success Criteria
- ✅ Users can register up to 10 channels via URL, @handle, or channel ID
- ✅ System correctly resolves all supported input formats to canonical channel IDs
- ✅ 10-channel limit is strictly enforced with clear error messages
- ✅ Duplicate channels are prevented across all input formats
- ✅ Channel management UI is intuitive with real-time feedback
- ✅ All API endpoints handle errors gracefully
- ✅ Test coverage > 80% for all channel operations
- ✅ YouTube API integration works reliably with rate limiting

---

## Phase 2: Channel Management & Data Models
**Status**: Planned  
**Duration**: 4-5 hours  
**Branch**: `devin/{timestamp}-phase2-channels`

### Objectives
- Implement data models for channels and videos
- Create channel discovery and management features
- Set up database schema and migrations
- Implement basic CRUD operations

### Tasks
- [ ] Design and implement database schema
- [ ] Create Channel and Video data models
- [ ] Implement channel subscription fetching
- [ ] Create channel management API endpoints
- [ ] Set up database migrations
- [ ] Implement channel monitoring toggle
- [ ] Add data validation and constraints
- [ ] Write integration tests for channel operations

### Deliverables
- Database schema with migrations
- Channel and Video data models
- Channel management API endpoints
- Channel subscription integration
- Data validation framework
- Integration tests

### Success Criteria
- Database schema is properly designed and migrated
- Channels can be fetched from YouTube subscriptions
- Channel monitoring can be toggled on/off
- All data operations work correctly

---

## Phase 3: Video Tracking & Change Detection
**Status**: Planned  
**Duration**: 5-6 hours  
**Branch**: `devin/{timestamp}-phase3-tracking`

### Objectives
- Implement video fetching and storage
- Create change detection algorithm
- Set up background job processing
- Implement video status verification

### Tasks
- [ ] Create video fetching service
- [ ] Implement change detection logic (NEW/CHANGED/MISSING)
- [ ] Set up background job scheduler
- [ ] Create video verification service using videos.list API
- [ ] Implement change logging system
- [ ] Add job queue for API operations
- [ ] Create monitoring dashboard for job status
- [ ] Write comprehensive tests for change detection

### Deliverables
- Video fetching and storage system
- Change detection algorithm
- Background job processing
- Video verification service
- Change logging system
- Job monitoring capabilities

### Success Criteria
- Videos are accurately fetched and stored
- Changes are detected with high accuracy (<5% false positives)
- Background jobs run reliably
- Video disappearances are properly verified

---

## Phase 4: Web Interface Development
**Status**: Planned  
**Duration**: 6-7 hours  
**Branch**: `devin/{timestamp}-phase4-frontend`

### Objectives
- Create React-based web interface
- Implement dashboard and channel timeline views
- Add search and filtering capabilities
- Create responsive design with Tailwind CSS

### Tasks
- [ ] Set up React application with TypeScript
- [ ] Create main dashboard layout
- [ ] Implement channel list and management interface
- [ ] Create channel timeline view
- [ ] Add video details modal
- [ ] Implement search and filtering
- [ ] Create responsive design
- [ ] Add loading states and error handling
- [ ] Write frontend tests

### Deliverables
- Complete React web application
- Dashboard with channel overview
- Channel timeline interface
- Video details and history views
- Search and filtering functionality
- Responsive design
- Frontend test suite

### Success Criteria
- Web interface is intuitive and responsive
- All core features are accessible via UI
- Performance is acceptable for typical usage
- UI follows modern design principles

---

## Phase 5: Data Export & Reporting
**Status**: Planned  
**Duration**: 2-3 hours  
**Branch**: `devin/{timestamp}-phase5-export`

### Objectives
- Implement CSV export functionality
- Create reporting features
- Add data visualization components
- Optimize query performance

### Tasks
- [ ] Create CSV export endpoints
- [ ] Implement data filtering for exports
- [ ] Add basic charts and visualizations
- [ ] Create summary reports
- [ ] Optimize database queries
- [ ] Add export scheduling options
- [ ] Implement data archiving strategy
- [ ] Write tests for export functionality

### Deliverables
- CSV export functionality
- Data visualization components
- Summary reporting features
- Query optimization
- Export scheduling
- Test coverage for exports

### Success Criteria
- Data can be exported in useful formats
- Reports provide valuable insights
- Export performance is acceptable
- Data integrity is maintained

---

## Phase 6: Notifications & Alerts (Optional)
**Status**: Planned  
**Duration**: 3-4 hours  
**Branch**: `devin/{timestamp}-phase6-notifications`

### Objectives
- Implement Slack notification integration
- Add email notification support
- Create notification preferences system
- Set up daily summary reports

### Tasks
- [ ] Set up Slack webhook integration
- [ ] Implement email service integration
- [ ] Create notification preferences UI
- [ ] Design daily summary format
- [ ] Implement notification scheduling
- [ ] Add notification history tracking
- [ ] Create notification templates
- [ ] Write tests for notification system

### Deliverables
- Slack integration
- Email notification system
- Notification preferences interface
- Daily summary reports
- Notification scheduling
- Template system

### Success Criteria
- Notifications are delivered reliably
- Users can configure preferences easily
- Daily summaries provide useful information
- System handles notification failures gracefully

---

## Phase 7: Deployment & Production Setup
**Status**: Planned  
**Duration**: 3-4 hours  
**Branch**: `devin/{timestamp}-phase7-deployment`

### Objectives
- Deploy application to Render (primary), maintain Fly.io configuration (dormant)
- Set up production environment configuration
- Implement monitoring and logging
- Create deployment documentation

### Tasks
- [ ] Configure Fly.io deployment
- [ ] Set up production database
- [ ] Configure environment variables
- [ ] Implement health checks
- [ ] Set up logging and monitoring
- [ ] Create backup strategy
- [ ] Write deployment documentation
- [ ] Test production deployment

### Deliverables
- Production deployment on Fly.io
- Environment configuration
- Monitoring and logging setup
- Backup and recovery procedures
- Deployment documentation
- Production testing results

### Success Criteria
- Application runs reliably in production
- All features work in production environment
- Monitoring provides adequate visibility
- Deployment process is documented and repeatable

---

## Phase 8: Testing & Quality Assurance
**Status**: Planned  
**Duration**: 2-3 hours  
**Branch**: `devin/{timestamp}-phase8-qa`

### Objectives
- Comprehensive testing of all features
- Performance optimization
- Security review
- Documentation finalization

### Tasks
- [ ] Run comprehensive integration tests
- [ ] Perform load testing
- [ ] Security audit and fixes
- [ ] Performance optimization
- [ ] Documentation review and updates
- [ ] User acceptance testing
- [ ] Bug fixes and refinements
- [ ] Final deployment verification

### Deliverables
- Complete test suite execution
- Performance optimization results
- Security audit report
- Updated documentation
- Bug fixes and improvements
- Final production verification

### Success Criteria
- All tests pass consistently
- Performance meets requirements
- Security vulnerabilities are addressed
- Documentation is complete and accurate
- Application is ready for use

---

## Development Guidelines

### Branch Naming Convention
- Format: `devin/{timestamp}-{phase}-{short-topic}`
- Example: `devin/1724403880-phase0-bootstrap`
- Generate timestamp with: `date +%s`

### Commit Message Format
- Use Conventional Commits format
- Examples: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`

### Phase Completion Requirements
- All tasks completed
- Tests passing
- Documentation updated
- Phase report submitted (English + Japanese)
- User approval received

### Quality Standards
- Code coverage > 80%
- All linting rules pass
- Documentation is current
- Security best practices followed
- Performance requirements met

---

## Risk Assessment

### High Risk Items
- YouTube API rate limiting constraints
- OAuth token management complexity
- Change detection accuracy requirements

### Medium Risk Items
- Background job reliability
- Database performance at scale
- Frontend responsiveness

### Low Risk Items
- CSV export functionality
- Basic UI components
- Documentation maintenance

### Mitigation Strategies
- Implement comprehensive error handling
- Use exponential backoff for API calls
- Regular testing and monitoring
- Incremental development approach
- User feedback integration
