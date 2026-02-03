// Yad2 Monitor Dashboard JavaScript

const API_BASE = '/api';
let allApartments = [];
let searchTimeout = null;
let currentSearchQuery = '';
let currentStatFilter = 'all'; // Track which stat card filter is active

// XSS Protection: Escape HTML special characters
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function fetchData(endpoint) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching data:', error);
        showToast('שגיאה בטעינת נתונים מהשרת', 'error', 3000);
        return null;
    }
}

async function loadStats() {
    const data = await fetchData('/stats');
    if (data) {
        document.getElementById('total-apartments').textContent = data.total_listings || 0;
        document.getElementById('avg-price').textContent =
            data.avg_price ? `₪${data.avg_price.toLocaleString()}` : '-';
        document.getElementById('new-today').textContent = data.new_this_week || 0;
        document.getElementById('price-changes').textContent = data.price_changes_this_week || 0;
    }
}

async function loadApartments() {
    const data = await fetchData('/apartments?include_price_history=1');
    if (data && data.apartments) {
        allApartments = data.apartments;
        populateAutocomplete();
        filterApartments();
    }
}

// Calculate price change percentage for an apartment
function getPriceChangePercent(apt) {
    if (!apt.price_history || apt.price_history.length < 2) {
        return null;
    }
    const oldPrice = apt.price_history[0].price;
    const newPrice = apt.price_history[apt.price_history.length - 1].price;
    if (oldPrice === 0) return null;
    return ((newPrice - oldPrice) / oldPrice * 100);
}

function renderApartments(apartments) {
    const tbody = document.getElementById('apartment-list');
    if (!apartments.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-state">אין דירות להצגה</td></tr>';
        return;
    }
    tbody.innerHTML = apartments.map(apt => {
        // Calculate price change
        const changePercent = getPriceChangePercent(apt);
        let changeDisplay = '-';
        let changeClass = '';
        if (changePercent !== null) {
            if (changePercent < 0) {
                changeDisplay = `📉 ${Math.abs(changePercent).toFixed(1)}%-`;
                changeClass = 'down';
            } else if (changePercent > 0) {
                changeDisplay = `📈 ${changePercent.toFixed(1)}%+`;
                changeClass = 'up';
            } else {
                changeDisplay = '0%';
            }
        }

        // Room color class (more rooms = better = green)
        let roomsClass = '';
        const rooms = apt.rooms || 0;
        if (rooms > 0 && rooms <= 2.5) {
            roomsClass = 'rooms-xlarge'; // Red - small apartments
        } else if (rooms >= 3 && rooms <= 3.5) {
            roomsClass = 'rooms-large'; // Orange
        } else if (rooms >= 4 && rooms <= 4.5) {
            roomsClass = 'rooms-medium'; // Yellow
        } else if (rooms >= 5) {
            roomsClass = 'rooms-small'; // Green - large apartments
        }

        return `
            <tr>
                <td class="col-title" title="${escapeHtml(apt.title)}">${escapeHtml(apt.title) || 'ללא כותרת'}</td>
                <td class="col-location" title="${escapeHtml(apt.street_address || apt.location || '')}">${escapeHtml(apt.street_address || apt.location || '-')}</td>
                <td class="col-rooms ${roomsClass}">${apt.rooms || '-'}</td>
                <td>${apt.sqm || '-'}</td>
                <td class="col-price">₪${(apt.price || 0).toLocaleString()}</td>
                <td class="col-change ${changeClass}">${changeDisplay}</td>
                <td class="col-actions">
                    <a href="${escapeHtml(apt.link)}" target="_blank" class="btn">צפייה</a>
                    <button class="btn btn-fav" onclick="toggleFavorite('${escapeHtml(apt.id)}')">⭐</button>
                </td>
            </tr>
        `;
    }).join('');
}

function filterApartments() {
    const minPrice = parseInt(document.getElementById('min-price').value) || 0;
    const maxPrice = parseInt(document.getElementById('max-price').value) || Infinity;
    const minRooms = parseFloat(document.getElementById('min-rooms').value) || 0;
    const maxRooms = parseFloat(document.getElementById('max-rooms').value) || Infinity;
    const minSqm = parseInt(document.getElementById('min-sqm').value) || 0;
    const maxSqm = parseInt(document.getElementById('max-sqm').value) || Infinity;
    const cityFilter = document.getElementById('city-filter').value.trim().toLowerCase();
    const neighborhoodFilter = document.getElementById('neighborhood-filter').value.trim().toLowerCase();
    const sortBy = document.getElementById('sort-by').value;

    let filtered = allApartments.filter(apt => {
        // Stat card filter
        if (currentStatFilter === 'price-drops') {
            // Only show apartments with price drops
            if (!apt.price_history || apt.price_history.length < 2) return false;
            const oldPrice = apt.price_history[0].price;
            const newPrice = apt.price_history[apt.price_history.length - 1].price;
            if (newPrice >= oldPrice) return false;
        } else if (currentStatFilter === 'new') {
            // Only show apartments from last 7 days
            const firstSeen = new Date(apt.first_seen);
            const weekAgo = new Date();
            weekAgo.setDate(weekAgo.getDate() - 7);
            if (firstSeen < weekAgo) return false;
        }

        // Price filter
        if (apt.price < minPrice || apt.price > maxPrice) return false;

        // Rooms filter
        const rooms = apt.rooms || 0;
        if (rooms < minRooms || rooms > maxRooms) return false;

        // Square meters filter
        const sqm = apt.sqm || 0;
        if (sqm > 0 && (sqm < minSqm || sqm > maxSqm)) return false;

        // City filter
        if (cityFilter && (!apt.city || !apt.city.toLowerCase().includes(cityFilter))) {
            return false;
        }

        // Neighborhood filter
        if (neighborhoodFilter && (!apt.neighborhood || !apt.neighborhood.toLowerCase().includes(neighborhoodFilter))) {
            return false;
        }

        // Search query filter
        if (currentSearchQuery) {
            const query = currentSearchQuery.toLowerCase();
            const searchableText = [
                apt.title,
                apt.street_address,
                apt.location,
                apt.city,
                apt.neighborhood
            ].filter(Boolean).join(' ').toLowerCase();

            if (!searchableText.includes(query)) return false;
        }

        return true;
    });

    // Apply sorting
    if (sortBy === 'price-asc') {
        filtered.sort((a, b) => (a.price || 0) - (b.price || 0));
    } else if (sortBy === 'price-desc') {
        filtered.sort((a, b) => (b.price || 0) - (a.price || 0));
    } else if (sortBy === 'rooms-asc') {
        filtered.sort((a, b) => (a.rooms || 0) - (b.rooms || 0));
    } else if (sortBy === 'rooms-desc') {
        filtered.sort((a, b) => (b.rooms || 0) - (a.rooms || 0));
    } else if (sortBy === 'sqm-desc') {
        filtered.sort((a, b) => (b.sqm || 0) - (a.sqm || 0));
    } else if (sortBy === 'price-change-desc') {
        // Sort by price drop (biggest drops first, nulls last)
        filtered.sort((a, b) => {
            const changeA = getPriceChangePercent(a);
            const changeB = getPriceChangePercent(b);
            if (changeA === null && changeB === null) return 0;
            if (changeA === null) return 1;
            if (changeB === null) return -1;
            return changeA - changeB; // More negative = bigger drop = first
        });
    } else if (sortBy === 'price-change-asc') {
        // Sort by price increase (biggest increases first, nulls last)
        filtered.sort((a, b) => {
            const changeA = getPriceChangePercent(a);
            const changeB = getPriceChangePercent(b);
            if (changeA === null && changeB === null) return 0;
            if (changeA === null) return 1;
            if (changeB === null) return -1;
            return changeB - changeA; // More positive = bigger increase = first
        });
    } else {
        // Default: sort by date (newest first)
        filtered.sort((a, b) => {
            const dateA = new Date(a.first_seen || 0);
            const dateB = new Date(b.first_seen || 0);
            return dateB - dateA;
        });
    }

    renderApartments(filtered);
    updateResultsCount(filtered.length);
}

async function loadFavorites() {
    const data = await fetchData('/favorites');
    const list = document.getElementById('favorites-list');
    if (data && data.favorites && data.favorites.length) {
        list.innerHTML = data.favorites.map(apt => `
            <li class="apartment-item">
                <div>
                    <div class="apartment-title">${escapeHtml(apt.title) || 'ללא כותרת'}</div>
                    <div class="apartment-location">${escapeHtml(apt.street_address)}</div>
                </div>
                <div>
                    <span class="apartment-price">₪${(apt.price || 0).toLocaleString()}</span>
                    <a href="${escapeHtml(apt.link)}" target="_blank" class="btn">צפייה</a>
                </div>
            </li>
        `).join('');
    } else {
        list.innerHTML = '<li class="empty-state">אין מועדפים</li>';
    }
}

async function loadPriceDrops() {
    const data = await fetchData('/price-drops');
    const list = document.getElementById('price-drops-list');
    if (data && data.drops && data.drops.length) {
        list.innerHTML = data.drops.map(item => `
            <li class="apartment-item">
                <div>
                    <div class="apartment-title">${escapeHtml(item.title) || 'ללא כותרת'}</div>
                    <div class="price-change-down">
                        ₪${item.old_price.toLocaleString()} → ₪${item.new_price.toLocaleString()}
                        (${item.drop_pct}%-)
                    </div>
                </div>
                <div>
                    <a href="${escapeHtml(item.link)}" target="_blank" class="btn">צפייה</a>
                </div>
            </li>
        `).join('');
    } else {
        list.innerHTML = '<li class="empty-state">אין ירידות מחיר אחרונות</li>';
    }
}

async function loadAnalytics() {
    const data = await fetchData('/analytics');
    const content = document.getElementById('analytics-content');
    if (data) {
        let html = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">';

        if (data.overall) {
            html += `
                <div class="card" style="margin: 0;">
                    <h3>סיכום כללי</h3>
                    <p>סה"כ דירות: ${data.overall.total_listings}</p>
                    <p>מחיר ממוצע: ₪${data.overall.avg_price?.toLocaleString() || '-'}</p>
                    <p>מ"ר ממוצע: ${data.overall.avg_sqm || '-'}</p>
                </div>
            `;
        }

        if (data.price_distribution) {
            html += `
                <div class="card" style="margin: 0;">
                    <h3>התפלגות מחירים</h3>
                    ${data.price_distribution.map(d =>
                        `<p>${d.range}: ${d.count} דירות</p>`
                    ).join('')}
                </div>
            `;
        }

        if (data.top_neighborhoods) {
            html += `
                <div class="card" style="margin: 0;">
                    <h3>שכונות מובילות</h3>
                    ${data.top_neighborhoods.slice(0, 5).map(n =>
                        `<p>${n.name}: ${n.count} דירות</p>`
                    ).join('')}
                </div>
            `;
        }

        html += '</div>';
        content.innerHTML = html;

        // Render Chart.js visualizations
        if (typeof renderAllCharts === 'function') {
            renderAllCharts(data);
        }
    }
}

async function toggleFavorite(aptId) {
    try {
        const response = await fetch(`${API_BASE}/favorites/${aptId}`, { method: 'POST' });
        if (response.ok) {
            showToast('נוסף למועדפים!', 'success', 2000);
            loadFavorites();
        } else {
            showToast('שגיאה בהוספה למועדפים', 'error');
        }
    } catch (error) {
        console.error('Error toggling favorite:', error);
        showToast('שגיאה בתקשורת עם השרת', 'error');
    }
}

function showTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('[id$="-tab"]').forEach(t => t.classList.add('hidden'));

    event.target.classList.add('active');
    document.getElementById(`${tabName}-tab`).classList.remove('hidden');

    if (tabName === 'favorites') loadFavorites();
    else if (tabName === 'price-drops') loadPriceDrops();
    else if (tabName === 'analytics') loadAnalytics();
}

// Filter by stat card click
function filterByStatCard(filterType) {
    currentStatFilter = filterType;

    // Update active state on stat cards
    document.querySelectorAll('.stat-card.clickable').forEach(card => {
        card.classList.remove('active');
    });

    // Find and activate the clicked card
    const cards = document.querySelectorAll('.stat-card.clickable');
    cards.forEach(card => {
        const onclick = card.getAttribute('onclick');
        if (onclick && onclick.includes(`'${filterType}'`)) {
            card.classList.add('active');
        }
    });

    // Switch to apartments tab
    showTab('apartments');
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelector('.tab').classList.add('active'); // First tab is apartments

    // Apply filter
    filterApartments();

    // Show toast with filter info
    const filterNames = {
        'all': 'כל הדירות',
        'new': 'דירות חדשות (שבוע אחרון)',
        'price-drops': 'דירות עם ירידת מחיר'
    };
    showToast(`מציג: ${filterNames[filterType]}`, 'info', 2000);
}

// Search with debouncing
function handleSearch() {
    const searchInput = document.getElementById('search-input');
    const clearBtn = document.getElementById('clear-search');

    currentSearchQuery = searchInput.value.trim();

    // Show/hide clear button
    clearBtn.style.display = currentSearchQuery ? 'flex' : 'none';

    // Debounce search
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        filterApartments();
    }, 300);
}

function clearSearch() {
    document.getElementById('search-input').value = '';
    currentSearchQuery = '';
    document.getElementById('clear-search').style.display = 'none';
    filterApartments();
}

// Update results count
function updateResultsCount(count) {
    const resultsCount = document.getElementById('results-count');
    if (resultsCount) {
        resultsCount.textContent = `${count} דירות`;
    }
}

// Populate autocomplete lists for cities and neighborhoods
function populateAutocomplete() {
    if (!allApartments.length) return;

    const cities = new Set();
    const neighborhoods = new Set();

    allApartments.forEach(apt => {
        if (apt.city) cities.add(apt.city);
        if (apt.neighborhood) neighborhoods.add(apt.neighborhood);
    });

    // Populate cities datalist
    const citiesList = document.getElementById('cities-list');
    citiesList.innerHTML = Array.from(cities).sort()
        .map(city => `<option value="${escapeHtml(city)}">`)
        .join('');

    // Populate neighborhoods datalist
    const neighborhoodsList = document.getElementById('neighborhoods-list');
    neighborhoodsList.innerHTML = Array.from(neighborhoods).sort()
        .map(neighborhood => `<option value="${escapeHtml(neighborhood)}">`)
        .join('');
}

// Helper to convert empty strings to null for API
function emptyToNull(value) {
    if (value === '' || value === undefined) return null;
    return value;
}

// Helper to convert empty strings to null for numeric fields
function emptyToNullNumber(value) {
    if (value === '' || value === undefined || value === null) return null;
    const num = parseFloat(value);
    return isNaN(num) ? null : num;
}

// Save filters to database
async function saveFilters() {
    const name = prompt('שם לפילטר:');
    if (!name) return;

    const filters = {
        name: name,
        minPrice: emptyToNullNumber(document.getElementById('min-price').value),
        maxPrice: emptyToNullNumber(document.getElementById('max-price').value),
        minRooms: emptyToNullNumber(document.getElementById('min-rooms').value),
        maxRooms: emptyToNullNumber(document.getElementById('max-rooms').value),
        minSqm: emptyToNullNumber(document.getElementById('min-sqm').value),
        maxSqm: emptyToNullNumber(document.getElementById('max-sqm').value),
        city: emptyToNull(document.getElementById('city-filter').value),
        neighborhood: emptyToNull(document.getElementById('neighborhood-filter').value),
        sortBy: emptyToNull(document.getElementById('sort-by').value)
    };

    try {
        const response = await fetch('/api/filter-presets', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(filters)
        });

        if (response.ok) {
            showToast('הפילטר נשמר בהצלחה!', 'success', 2000);
            await loadFilterPresets(); // Refresh the presets list
        } else {
            const data = await response.json();
            showToast(data.error || 'שגיאה בשמירת הפילטר', 'error');
        }
    } catch (e) {
        console.error('Error saving filters:', e);
        showToast('שגיאה בשמירת הפילטר', 'error');
    }
}

// Load filter presets from database
async function loadFilterPresets() {
    try {
        const response = await fetch('/api/filter-presets');
        if (!response.ok) {
            console.error('Failed to load filter presets');
            return;
        }

        const data = await response.json();
        displayFilterPresets(data.presets || []);
    } catch (e) {
        console.error('Error loading filter presets:', e);
    }
}

// Display filter presets in UI
function displayFilterPresets(presets) {
    const container = document.getElementById('saved-filters-container');
    if (!container) return;

    if (presets.length === 0) {
        container.innerHTML = '<p style="color: #888; font-size: 14px;">אין פילטרים שמורים</p>';
        return;
    }

    container.innerHTML = presets.map(preset => `
        <div class="filter-preset" style="display: inline-block; margin: 5px;">
            <button onclick="applyFilterPreset(${preset.id})" style="padding: 8px 12px; margin-right: 5px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                ${preset.name}
            </button>
            <button onclick="deleteFilterPreset(${preset.id})" style="padding: 8px 12px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">
                ✕
            </button>
        </div>
    `).join('');
}

// Apply a filter preset
async function applyFilterPreset(presetId) {
    try {
        const response = await fetch(`/api/filter-presets/${presetId}`);
        if (!response.ok) {
            showToast('שגיאה בטעינת הפילטר', 'error');
            return;
        }

        const preset = await response.json();
        document.getElementById('min-price').value = preset.min_price || '';
        document.getElementById('max-price').value = preset.max_price || '';
        document.getElementById('min-rooms').value = preset.min_rooms || '';
        document.getElementById('max-rooms').value = preset.max_rooms || '';
        document.getElementById('min-sqm').value = preset.min_sqm || '';
        document.getElementById('max-sqm').value = preset.max_sqm || '';
        document.getElementById('city-filter').value = preset.city || '';
        document.getElementById('neighborhood-filter').value = preset.neighborhood || '';
        document.getElementById('sort-by').value = preset.sort_by || 'date';

        filterApartments();
        showToast('הפילטר נטען בהצלחה!', 'success', 2000);
    } catch (e) {
        console.error('Error applying filter preset:', e);
        showToast('שגיאה בטעינת הפילטר', 'error');
    }
}

// Delete a filter preset
async function deleteFilterPreset(presetId) {
    if (!confirm('האם למחוק פילטר זה?')) return;

    try {
        const response = await fetch(`/api/filter-presets/${presetId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showToast('הפילטר נמחק בהצלחה!', 'success', 2000);
            await loadFilterPresets(); // Refresh the list
        } else {
            showToast('שגיאה במחיקת הפילטר', 'error');
        }
    } catch (e) {
        console.error('Error deleting filter preset:', e);
        showToast('שגיאה במחיקת הפילטר', 'error');
    }
}

// Legacy function for backward compatibility
function loadFilters() {
    showToast('בחר פילטר מהרשימה למטה', 'info', 2000);
}

// Clear all filters
function clearFilters() {
    document.getElementById('min-price').value = '';
    document.getElementById('max-price').value = '';
    document.getElementById('min-rooms').value = '';
    document.getElementById('max-rooms').value = '';
    document.getElementById('min-sqm').value = '';
    document.getElementById('max-sqm').value = '';
    document.getElementById('city-filter').value = '';
    document.getElementById('neighborhood-filter').value = '';
    document.getElementById('sort-by').value = 'date';
    document.getElementById('search-input').value = '';
    currentSearchQuery = '';
    currentStatFilter = 'all'; // Reset stat card filter
    document.getElementById('clear-search').style.display = 'none';

    // Remove active state from stat cards
    document.querySelectorAll('.stat-card.clickable').forEach(card => {
        card.classList.remove('active');
    });

    filterApartments();
    showToast('הפילטרים נוקו', 'info', 2000);
}

// Table header click sorting
function initTableSorting() {
    const headers = document.querySelectorAll('.apartment-table th.sortable');
    headers.forEach(header => {
        header.addEventListener('click', () => {
            const sortKey = header.dataset.sort;
            const sortSelect = document.getElementById('sort-by');

            // Map header sort keys to select values
            const sortMap = {
                'title': 'date', // No title sort, use date
                'location': 'date', // No location sort, use date
                'rooms': 'rooms-desc',
                'sqm': 'sqm-desc',
                'price': 'price-asc',
                'price-change': 'price-change-desc'
            };

            // Toggle between asc/desc if same column clicked
            const currentSort = sortSelect.value;
            let newSort = sortMap[sortKey];

            if (sortKey === 'price') {
                newSort = currentSort === 'price-asc' ? 'price-desc' : 'price-asc';
            } else if (sortKey === 'rooms') {
                newSort = currentSort === 'rooms-desc' ? 'rooms-asc' : 'rooms-desc';
            } else if (sortKey === 'price-change') {
                newSort = currentSort === 'price-change-desc' ? 'price-change-asc' : 'price-change-desc';
            }

            sortSelect.value = newSort;
            filterApartments();

            // Update header visual state
            headers.forEach(h => {
                h.classList.remove('active', 'asc', 'desc');
            });
            header.classList.add('active');
            if (newSort.includes('-asc')) {
                header.classList.add('asc');
            } else if (newSort.includes('-desc')) {
                header.classList.add('desc');
            }
        });
    });
}

// Initial load
loadStats();
loadApartments();
loadFilterPresets(); // Load saved filter presets from database
initTableSorting(); // Initialize table header sorting

// Refresh every 5 minutes
setInterval(() => {
    loadStats();
    loadApartments();
}, 300000);
