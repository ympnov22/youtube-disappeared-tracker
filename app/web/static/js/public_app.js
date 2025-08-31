function showLoading() {
    document.getElementById('loading-overlay').classList.add('show');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('show');
}

function showResult(elementId, content, isError = false) {
    const element = document.getElementById(elementId);
    element.innerHTML = content;
    element.className = `result-area ${isError ? 'error' : 'success'}`;
    element.style.display = 'block';
}

function clearResult(elementId) {
    const element = document.getElementById(elementId);
    element.innerHTML = '';
    element.style.display = 'none';
}

async function apiCall(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    const response = await fetch(url, { ...defaultOptions, ...options });
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    
    return response.json();
}

async function triggerScan() {
    const channelId = document.getElementById('channel-id').value.trim();
    
    if (!channelId) {
        showResult('scan-result', '<p class="error">Please enter a channel ID</p>', true);
        return;
    }
    
    if (!channelId.startsWith('UC') || channelId.length !== 24) {
        showResult('scan-result', '<p class="error">Channel ID must start with "UC" and be 24 characters long</p>', true);
        return;
    }
    
    showLoading();
    clearResult('scan-result');
    
    try {
        const result = await apiCall(`/api/scan/${channelId}`, {
            method: 'POST'
        });
        
        const html = `
            <div class="scan-success">
                <h4>Scan completed successfully! / スキャン完了</h4>
                <p><strong>Channel:</strong> ${result.channel_id}</p>
                <p><strong>Message:</strong> ${result.message}</p>
                <ul>
                    <li>Videos added: ${result.added}</li>
                    <li>Videos updated: ${result.updated}</li>
                    <li>Events created: ${result.events_created}</li>
                </ul>
            </div>
        `;
        
        showResult('scan-result', html);
    } catch (error) {
        showResult('scan-result', `<p class="error">Error: ${error.message}</p>`, true);
    } finally {
        hideLoading();
    }
}

async function loadChannelVideos() {
    const channelId = document.getElementById('videos-channel-id').value.trim();
    const status = document.getElementById('video-status').value;
    
    if (!channelId) {
        showResult('videos-result', '<p class="error">Please enter a channel ID</p>', true);
        return;
    }
    
    showLoading();
    clearResult('videos-result');
    
    try {
        let url = `/api/channels/${channelId}/videos?limit=50`;
        if (status) {
            url += `&status=${status}`;
        }
        
        const result = await apiCall(url);
        
        if (result.videos.length === 0) {
            showResult('videos-result', '<p>No videos found for this channel</p>');
            return;
        }
        
        let html = `
            <div class="videos-list">
                <h4>Videos (${result.total} total, showing ${result.videos.length})</h4>
                <div class="videos-table-container">
                    <table class="videos-table">
                        <thead>
                            <tr>
                                <th>Title</th>
                                <th>Status</th>
                                <th>Published</th>
                                <th>Duration</th>
                                <th>Views</th>
                            </tr>
                        </thead>
                        <tbody>
        `;
        
        result.videos.forEach(video => {
            const statusClass = video.is_available ? 'status-active' : 'status-missing';
            const statusText = video.is_available ? 'Active' : 'Missing';
            const publishedDate = new Date(video.published_at).toLocaleDateString();
            const duration = video.duration || 'N/A';
            const views = video.view_count ? video.view_count.toLocaleString() : 'N/A';
            
            html += `
                <tr class="video-row ${video.is_available ? 'available' : 'missing'}">
                    <td class="video-title">
                        <div class="title">${video.title}</div>
                        <div class="video-id">${video.video_id}</div>
                    </td>
                    <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                    <td class="published-date">${publishedDate}</td>
                    <td>${duration}</td>
                    <td>${views}</td>
                </tr>
            `;
        });
        
        html += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        showResult('videos-result', html);
    } catch (error) {
        showResult('videos-result', `<p class="error">Error: ${error.message}</p>`, true);
    } finally {
        hideLoading();
    }
}

async function loadEvents() {
    const channelId = document.getElementById('events-channel-id').value.trim();
    const eventType = document.getElementById('event-type').value;
    const limit = document.getElementById('events-limit').value;
    
    showLoading();
    clearResult('events-result');
    
    try {
        let url = `/api/events?limit=${limit}`;
        if (channelId) {
            url += `&channel_id=${channelId}`;
        }
        if (eventType) {
            url += `&event_type=${eventType}`;
        }
        
        const result = await apiCall(url);
        
        if (result.events.length === 0) {
            showResult('events-result', '<p>No events found</p>');
            return;
        }
        
        let html = `
            <div class="events-list">
                <h4>Disappearance Events (${result.total} total, showing ${result.events.length})</h4>
                <div class="events-table-container">
                    <table class="events-table">
                        <thead>
                            <tr>
                                <th>Video</th>
                                <th>Event Type</th>
                                <th>Detected</th>
                                <th>Channel</th>
                            </tr>
                        </thead>
                        <tbody>
        `;
        
        result.events.forEach(event => {
            const detectedDate = new Date(event.detected_at).toLocaleString();
            const eventClass = `event-${event.event_type.toLowerCase()}`;
            
            html += `
                <tr>
                    <td class="video-title">
                        <div class="title">${event.video.title}</div>
                        <div class="video-id">${event.video.video_id}</div>
                    </td>
                    <td><span class="event-badge ${eventClass}">${event.event_type}</span></td>
                    <td class="detected-date">${detectedDate}</td>
                    <td>${event.video.channel_id}</td>
                </tr>
            `;
        });
        
        html += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        showResult('events-result', html);
    } catch (error) {
        showResult('events-result', `<p class="error">Error: ${error.message}</p>`, true);
    } finally {
        hideLoading();
    }
}

const style = document.createElement('style');
style.textContent = `
    .result-area {
        margin-top: 1rem;
        padding: 1rem;
        border-radius: 4px;
        display: none;
    }
    .result-area.success {
        background-color: #e8f5e8;
        border: 1px solid #4caf50;
    }
    .result-area.error {
        background-color: #ffebee;
        border: 1px solid #f44336;
    }
    .result-area .error {
        color: #c62828;
        font-weight: 500;
    }
    .scan-success h4 {
        color: #2e7d32;
        margin-bottom: 0.5rem;
    }
    .filters-form {
        display: flex;
        gap: 1rem;
        margin-bottom: 1rem;
        flex-wrap: wrap;
    }
    .filter-group {
        flex: 1;
        min-width: 200px;
    }
`;
document.head.appendChild(style);
