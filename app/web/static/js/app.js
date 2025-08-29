
function getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : null;
}

function showAddChannelForm() {
    const form = document.getElementById('add-channel-form');
    if (form) {
        form.style.display = 'block';
        const input = form.querySelector('input[name="channel_input"]');
        if (input) input.focus();
    }
}

function hideAddChannelForm() {
    const form = document.getElementById('add-channel-form');
    if (form) {
        form.style.display = 'none';
        form.reset();
    }
}

function confirmScan(channelTitle) {
    return confirm(`Scan channel "${channelTitle}" for new videos?\n\nThis will check for new videos and detect any that have disappeared.`);
}

function confirmDelete(channelTitle) {
    return confirm(`Delete channel "${channelTitle}"?\n\nThis will stop monitoring this channel. Videos and events will be preserved.`);
}

function setLoading(element, isLoading) {
    if (isLoading) {
        element.classList.add('loading');
        element.disabled = true;
        
        if (element.tagName === 'BUTTON') {
            const originalText = element.textContent;
            element.dataset.originalText = originalText;
            element.innerHTML = '<span class="spinner"></span> ' + originalText;
        }
    } else {
        element.classList.remove('loading');
        element.disabled = false;
        
        if (element.dataset.originalText) {
            element.textContent = element.dataset.originalText;
            delete element.dataset.originalText;
        }
    }
}

function handleFormSubmission(form) {
    const submitButton = form.querySelector('button[type="submit"]');
    if (submitButton) {
        setLoading(submitButton, true);
    }
    
    setTimeout(() => {
        if (submitButton) {
            setLoading(submitButton, false);
        }
    }, 5000);
}

let autoRefreshInterval = null;

function startAutoRefresh(intervalMs = 30000) {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    autoRefreshInterval = setInterval(() => {
        if (document.hidden || Date.now() - lastUserActivity > 10000) {
            window.location.reload();
        }
    }, intervalMs);
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

let lastUserActivity = Date.now();

function updateUserActivity() {
    lastUserActivity = Date.now();
}

document.addEventListener('DOMContentLoaded', function() {
    ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
        document.addEventListener(event, updateUserActivity, true);
    });
    
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            handleFormSubmission(this);
        });
    });
    
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
    
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[type="search"], input[name="channel_input"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        if (e.key === 'Escape') {
            hideAddChannelForm();
        }
    });
    
    if (window.location.pathname.includes('/events')) {
        startAutoRefresh(60000); // Refresh every minute
    }
    
    enhanceTableInteractions();
});

function enhanceTableInteractions() {
    document.querySelectorAll('.videos-table tbody tr').forEach(row => {
        const link = row.querySelector('a[href*="youtube.com"]');
        if (link) {
            row.style.cursor = 'pointer';
            row.addEventListener('click', function(e) {
                if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'A') {
                    link.click();
                }
            });
        }
    });
    
    document.querySelectorAll('th').forEach(header => {
        if (header.textContent.trim() && !header.querySelector('button')) {
            header.style.cursor = 'pointer';
            header.addEventListener('click', function() {
                sortTable(this);
            });
        }
    });
}

function sortTable(header) {
    const table = header.closest('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const columnIndex = Array.from(header.parentNode.children).indexOf(header);
    
    const isAscending = header.classList.contains('sort-asc');
    
    header.parentNode.querySelectorAll('th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    header.classList.add(isAscending ? 'sort-desc' : 'sort-asc');
    
    rows.sort((a, b) => {
        const aText = a.children[columnIndex].textContent.trim();
        const bText = b.children[columnIndex].textContent.trim();
        
        const aNum = parseFloat(aText.replace(/,/g, ''));
        const bNum = parseFloat(bText.replace(/,/g, ''));
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAscending ? bNum - aNum : aNum - bNum;
        }
        
        return isAscending ? bText.localeCompare(aText) : aText.localeCompare(bText);
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

async function apiCall(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    const response = await fetch(url, { ...defaultOptions, ...options });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        showAddChannelForm,
        hideAddChannelForm,
        confirmScan,
        confirmDelete,
        setLoading,
        apiCall
    };
}
