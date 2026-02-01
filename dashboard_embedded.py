"""
Embedded dashboard HTML - full-featured single-page app with Tailwind CSS
"""

def get_dashboard_html():
    return '''<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Yad2 Monitor Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
    tailwind.config = {
        darkMode: 'class',
        theme: {
            extend: {
                colors: { brand: '#667eea' }
            }
        }
    }
    </script>
    <style>
        /* Custom scrollbar */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #667eea40; border-radius: 3px; }
        /* Smooth transitions for dark mode */
        * { transition: background-color 0.2s, border-color 0.2s, color 0.2s; }
    </style>
</head>
<body class="bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-200 min-h-screen">

<div class="max-w-6xl mx-auto px-4 py-6 sm:px-6 lg:px-8">

    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl sm:text-3xl font-bold text-brand">🏠 Yad2 Monitor</h1>
        <button onclick="toggleTheme()" id="theme-btn"
            class="w-10 h-10 rounded-full bg-brand text-white flex items-center justify-center text-lg shadow-lg hover:opacity-80">
            🌙
        </button>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4 mb-6" id="stats-grid">
        <button onclick="filterBy('all')" id="stat-all"
            class="stat-card bg-white dark:bg-gray-800 rounded-xl shadow p-4 text-center border-2 border-transparent hover:border-brand hover:shadow-lg transition-all">
            <div class="text-2xl mb-1">🏢</div>
            <div class="text-2xl sm:text-3xl font-bold text-brand" id="v-total">-</div>
            <div class="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-1">כל הדירות</div>
        </button>
        <button onclick="filterBy('new')" id="stat-new"
            class="stat-card bg-white dark:bg-gray-800 rounded-xl shadow p-4 text-center border-2 border-transparent hover:border-brand hover:shadow-lg transition-all">
            <div class="text-2xl mb-1">🆕</div>
            <div class="text-2xl sm:text-3xl font-bold text-brand" id="v-new">-</div>
            <div class="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-1">חדשות (48 שעות)</div>
        </button>
        <button onclick="filterBy('today')" id="stat-today"
            class="stat-card bg-white dark:bg-gray-800 rounded-xl shadow p-4 text-center border-2 border-transparent hover:border-brand hover:shadow-lg transition-all">
            <div class="text-2xl mb-1">📅</div>
            <div class="text-2xl sm:text-3xl font-bold text-brand" id="v-today">-</div>
            <div class="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-1">היום (24 שעות)</div>
        </button>
        <button onclick="filterBy('price-drop')" id="stat-price-drop"
            class="stat-card bg-white dark:bg-gray-800 rounded-xl shadow p-4 text-center border-2 border-transparent hover:border-brand hover:shadow-lg transition-all">
            <div class="text-2xl mb-1">📉</div>
            <div class="text-2xl sm:text-3xl font-bold text-brand" id="v-drops">-</div>
            <div class="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-1">ירידות מחיר</div>
        </button>
        <button onclick="filterBy('removed')" id="stat-removed"
            class="stat-card bg-white dark:bg-gray-800 rounded-xl shadow p-4 text-center border-2 border-transparent hover:border-brand hover:shadow-lg transition-all">
            <div class="text-2xl mb-1">🚫</div>
            <div class="text-2xl sm:text-3xl font-bold text-brand" id="v-removed">-</div>
            <div class="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-1">הוסרו</div>
        </button>
        <button onclick="filterBy('avg')" id="stat-avg"
            class="stat-card bg-white dark:bg-gray-800 rounded-xl shadow p-4 text-center border-2 border-transparent hover:border-brand hover:shadow-lg transition-all col-span-2 sm:col-span-1">
            <div class="text-2xl mb-1">💰</div>
            <div class="text-xl sm:text-2xl font-bold text-brand" id="v-avg">-</div>
            <div class="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-1">מחיר ממוצע</div>
        </button>
    </div>

    <!-- Filter Bar -->
    <div id="filter-bar" class="hidden bg-white dark:bg-gray-800 rounded-xl shadow p-3 sm:p-4 mb-5">
        <div class="flex flex-wrap items-center gap-2 sm:gap-3">
            <span class="text-brand font-semibold text-sm whitespace-nowrap">🔍 סינון:</span>
            <input type="text" id="f-search" placeholder="חיפוש חופשי..."
                oninput="applyFilters()"
                class="flex-1 min-w-[120px] max-w-[200px] px-3 py-2 text-sm border-2 border-gray-200 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700 focus:border-brand focus:outline-none">
            <input type="number" id="f-min-price" placeholder="מחיר מינ'"
                oninput="applyFilters()"
                class="w-24 sm:w-28 px-3 py-2 text-sm border-2 border-gray-200 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700 focus:border-brand focus:outline-none">
            <input type="number" id="f-max-price" placeholder="מחיר מקס'"
                oninput="applyFilters()"
                class="w-24 sm:w-28 px-3 py-2 text-sm border-2 border-gray-200 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700 focus:border-brand focus:outline-none">
            <select id="f-sort" onchange="applyFilters()"
                class="px-3 py-2 text-sm border-2 border-gray-200 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700 focus:border-brand focus:outline-none">
                <option value="date">חדשים ראשון</option>
                <option value="price-asc">מחיר ↑</option>
                <option value="price-desc">מחיר ↓</option>
            </select>
            <button onclick="clearFilters()"
                class="px-3 py-2 text-sm bg-gray-200 dark:bg-gray-600 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500 font-medium">
                נקה
            </button>
        </div>
    </div>

    <!-- View Title -->
    <div class="flex items-center justify-between mb-4">
        <h2 id="view-title" class="text-lg sm:text-xl font-bold text-brand">🏢 כל הדירות</h2>
        <span id="view-count" class="text-sm text-gray-500 dark:text-gray-400"></span>
    </div>

    <!-- Apartment List -->
    <div id="apt-container">
        <div class="text-center py-12 text-gray-400">טוען נתונים...</div>
    </div>

</div>

<script>
let allApts = [];
let removedApts = [];
let currentFilter = 'all';
let healthData = null;

function esc(t) {
    if (!t) return '';
    const d = document.createElement('div');
    d.textContent = t;
    return d.innerHTML;
}

function toggleTheme() {
    const isDark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    document.getElementById('theme-btn').textContent = isDark ? '☀️' : '🌙';
}

async function loadAll() {
    try {
        const [healthRes, aptsRes] = await Promise.all([
            fetch('/health'),
            fetch('/api/apartments?limit=500&include_inactive=1')
        ]);
        healthData = await healthRes.json();
        const aptsData = await aptsRes.json();
        allApts = aptsData.apartments || aptsData || [];
        removedApts = allApts.filter(a => !a.is_active);

        // Debug: log all text fields for first 3 apartments
        console.log('=== FLOOR DEBUG ===');
        console.log('Total apartments:', allApts.length);
        allApts.slice(0, 3).forEach((a, i) => {
            console.log('Apt ' + i + ':', JSON.stringify({
                floor: a.floor, rooms: a.rooms, sqm: a.sqm,
                title: a.title, item_info: a.item_info,
                location: a.location, street_address: a.street_address,
                price_text: a.price_text
            }));
            // Search ALL string values for קומה
            Object.entries(a).forEach(([k,v]) => {
                if (typeof v === 'string' && /קומה/.test(v)) {
                    console.log('  FOUND קומה in field "' + k + '":', v);
                }
            });
        });

        updateStats();
        filterBy(currentFilter);
        document.getElementById('filter-bar').classList.remove('hidden');
    } catch(e) {
        console.error(e);
        document.getElementById('apt-container').innerHTML =
            '<div class="text-center py-16 text-gray-400"><div class="text-4xl mb-3">❌</div><p>שגיאה בטעינת נתונים</p></div>';
    }
}

function updateStats() {
    const now = Date.now();
    const twoDays = 48 * 60 * 60 * 1000;
    const activeApts = allApts.filter(a => a.is_active !== 0);
    const newApts = activeApts.filter(a => (now - new Date(a.first_seen).getTime()) < twoDays);
    const prices = activeApts.map(a => a.price).filter(p => p > 0);
    const avg = prices.length ? Math.round(prices.reduce((a,b) => a+b, 0) / prices.length) : 0;

    // Calculate today's apartments (midnight to midnight)
    const todayStart = new Date();
    todayStart.setHours(0, 0, 0, 0);
    const todayEnd = new Date(todayStart);
    todayEnd.setDate(todayEnd.getDate() + 1);
    const todayApts = allApts.filter(a => {
        const firstSeen = new Date(a.first_seen).getTime();
        const lastSeen = a.last_seen ? new Date(a.last_seen).getTime() : firstSeen;
        return (firstSeen >= todayStart.getTime() && firstSeen < todayEnd.getTime()) ||
               (lastSeen >= todayStart.getTime() && lastSeen < todayEnd.getTime());
    });

    document.getElementById('v-total').textContent = allApts.length;
    document.getElementById('v-new').textContent = newApts.length;
    document.getElementById('v-today').textContent = todayApts.length;
    document.getElementById('v-drops').textContent = healthData?.today?.price_drops || 0;
    document.getElementById('v-removed').textContent = removedApts.length;
    document.getElementById('v-avg').textContent = avg ? avg.toLocaleString() + ' ₪' : '-';
}

function filterBy(type) {
    currentFilter = type;
    document.querySelectorAll('.stat-card').forEach(s => {
        s.classList.remove('border-brand', 'bg-indigo-50', 'dark:bg-indigo-900/20');
        s.classList.add('border-transparent');
    });
    const el = document.getElementById('stat-' + type);
    if (el) {
        el.classList.add('border-brand', 'bg-indigo-50', 'dark:bg-indigo-900/20');
        el.classList.remove('border-transparent');
    }

    const titles = {
        'all': '🏢 כל הדירות',
        'new': '🆕 דירות חדשות (48 שעות)',
        'today': '📅 דירות היום (24 שעות)',
        'price-drop': '📉 ירידות מחיר',
        'removed': '🚫 דירות שהוסרו',
        'avg': '💰 כל הדירות (לפי מחיר)'
    };
    document.getElementById('view-title').textContent = titles[type] || titles['all'];
    applyFilters();
}

function getFilteredApts() {
    const now = Date.now();
    const twoDays = 48 * 60 * 60 * 1000;
    switch (currentFilter) {
        case 'new':
            return allApts.filter(a => a.is_active !== 0 && (now - new Date(a.first_seen).getTime()) < twoDays);
        case 'today':
            const todayStart = new Date();
            todayStart.setHours(0, 0, 0, 0);
            const todayEnd = new Date(todayStart);
            todayEnd.setDate(todayEnd.getDate() + 1);
            return allApts.filter(a => {
                const firstSeen = new Date(a.first_seen).getTime();
                const lastSeen = a.last_seen ? new Date(a.last_seen).getTime() : firstSeen;
                return (firstSeen >= todayStart.getTime() && firstSeen < todayEnd.getTime()) ||
                       (lastSeen >= todayStart.getTime() && lastSeen < todayEnd.getTime());
            });
        case 'removed':
            return removedApts.length ? removedApts : allApts.filter(a => a.is_active === 0);
        case 'price-drop':
            return allApts.filter(a => a.is_active !== 0);
        case 'avg':
            return [...allApts.filter(a => a.is_active !== 0)].sort((a,b) => (a.price||0) - (b.price||0));
        default:
            return allApts;
    }
}

function applyFilters() {
    let apts = getFilteredApts();
    const search = (document.getElementById('f-search').value || '').trim().toLowerCase();
    if (search) {
        apts = apts.filter(a => {
            const text = [a.title, a.street_address, a.location, a.item_info].filter(Boolean).join(' ').toLowerCase();
            return text.includes(search);
        });
    }
    const minP = parseInt(document.getElementById('f-min-price').value) || 0;
    const maxP = parseInt(document.getElementById('f-max-price').value) || Infinity;
    if (minP > 0 || maxP < Infinity) {
        apts = apts.filter(a => (a.price||0) >= minP && (a.price||0) <= maxP);
    }
    const sort = document.getElementById('f-sort').value;
    if (sort === 'price-asc') apts.sort((a,b) => (a.price||0) - (b.price||0));
    else if (sort === 'price-desc') apts.sort((a,b) => (b.price||0) - (a.price||0));
    else apts.sort((a,b) => new Date(b.first_seen||0) - new Date(a.first_seen||0));
    renderApts(apts);
}

function clearFilters() {
    document.getElementById('f-search').value = '';
    document.getElementById('f-min-price').value = '';
    document.getElementById('f-max-price').value = '';
    document.getElementById('f-sort').value = 'date';
    applyFilters();
}

function roomColor(rooms) {
    if (!rooms) return null;
    const r = parseFloat(rooms);
    if (r <= 1.5) return { bg: '#6b7280', text: '#fff' };     // gray
    if (r <= 2)   return { bg: '#8b5cf6', text: '#fff' };     // purple
    if (r <= 2.5) return { bg: '#a78bfa', text: '#fff' };     // light purple
    if (r <= 3)   return { bg: '#3b82f6', text: '#fff' };     // blue
    if (r <= 3.5) return { bg: '#06b6d4', text: '#fff' };     // cyan
    if (r <= 4)   return { bg: '#10b981', text: '#fff' };     // green
    if (r <= 4.5) return { bg: '#f59e0b', text: '#fff' };     // amber
    if (r <= 5)   return { bg: '#ef4444', text: '#fff' };     // red
    if (r <= 5.5) return { bg: '#ec4899', text: '#fff' };     // pink
    return              { bg: '#dc2626', text: '#fff' };       // dark red 6+
}

function buildingViz(floor, totalFloors) {
    if (floor == null || floor < 0) return '';
    const total = Math.max(totalFloors || 9, floor + 1, 3);
    const maxShow = 12;
    const W = 56; // building width
    const FH = 12; // floor height
    const GH = 14; // ground floor height
    // Decide which floors to show vs collapse
    let floorsToShow = [];
    if (total + 1 <= maxShow) {
        for (let f = total; f >= 0; f--) floorsToShow.push(f);
    } else {
        const keep = new Set();
        keep.add(total); keep.add(total - 1);
        keep.add(0); keep.add(1);
        for (let f = Math.max(0, floor - 1); f <= Math.min(total, floor + 1); f++) keep.add(f);
        const sorted = [...keep].sort((a, b) => b - a);
        for (let i = 0; i < sorted.length; i++) {
            floorsToShow.push(sorted[i]);
            if (i < sorted.length - 1 && sorted[i] - sorted[i + 1] > 1) {
                floorsToShow.push('dots');
            }
        }
    }
    let html = '<div style="display:flex;flex-direction:column;align-items:center;flex-shrink:0;min-width:' + (W+30) + 'px" title="קומה ' + floor + ' מתוך ' + total + '">';
    // Roof
    html += '<div style="width:0;height:0;border-left:' + (W/2) + 'px solid transparent;border-right:' + (W/2) + 'px solid transparent;border-bottom:10px solid #6b7280;margin-bottom:1px"></div>';
    for (const f of floorsToShow) {
        if (f === 'dots') {
            html += '<div style="width:' + W + 'px;height:12px;display:flex;justify-content:center;align-items:center;gap:3px">' +
                '<div style="width:4px;height:4px;background:#9ca3af;border-radius:50%"></div>' +
                '<div style="width:4px;height:4px;background:#9ca3af;border-radius:50%"></div>' +
                '<div style="width:4px;height:4px;background:#9ca3af;border-radius:50%"></div></div>';
            continue;
        }
        const isTarget = f === floor;
        const bg = isTarget ? 'background:#667eea;' : 'background:#e5e7eb;';
        const border = isTarget ? 'border:2px solid #4f46e5;' : 'border:1px solid #d1d5db;';
        const h = f === 0 ? GH : FH;
        let inner = '';
        if (f > 0) {
            const wc = isTarget ? '#fff' : '#9ca3af';
            inner = '<div style="display:flex;gap:3px;justify-content:center;align-items:center;height:100%">' +
                '<div style="width:7px;height:6px;background:' + wc + ';border-radius:1px"></div>' +
                '<div style="width:7px;height:6px;background:' + wc + ';border-radius:1px"></div>' +
                '<div style="width:7px;height:6px;background:' + wc + ';border-radius:1px"></div></div>';
        } else {
            const dc = isTarget ? '#fff' : '#9ca3af';
            inner = '<div style="display:flex;justify-content:center;align-items:end;height:100%">' +
                '<div style="width:8px;height:8px;background:' + dc + ';border-radius:1px 1px 0 0"></div></div>';
        }
        const label = isTarget ? '<span style="position:absolute;right:-24px;top:50%;transform:translateY(-50%);font-size:9px;font-weight:bold;color:#667eea;line-height:1">◄ ' + floor + '</span>' : '';
        html += '<div style="position:relative;width:' + W + 'px;height:' + h + 'px;' + bg + border + 'margin-bottom:-1px;border-radius:1px;">' + inner + label + '</div>';
    }
    // Ground line
    html += '<div style="width:' + (W+8) + 'px;height:2px;background:#6b7280;margin-top:1px"></div>';
    html += '</div>';
    return html;
}

function renderApts(apts) {
    const container = document.getElementById('apt-container');
    document.getElementById('view-count').textContent = apts.length + ' דירות';

    if (!apts.length) {
        container.innerHTML = '<div class="text-center py-16 text-gray-400"><div class="text-4xl mb-3">🤷</div><p>אין דירות להצגה</p></div>';
        return;
    }

    const now = Date.now();
    const twoDays = 48 * 60 * 60 * 1000;

    container.innerHTML = '<div class="space-y-3">' + apts.map(apt => {
        const isNew = (now - new Date(apt.first_seen).getTime()) < twoDays;
        const isRemoved = apt.is_active === 0;
        const price = apt.price ? '₪' + apt.price.toLocaleString() : 'לא ידוע';
        const location = esc(apt.street_address || apt.location || '');
        const mapQuery = encodeURIComponent((apt.street_address || apt.location || apt.title || '') + ' Israel');
        const info = esc(apt.item_info || '');
        const firstSeen = apt.first_seen ? new Date(apt.first_seen).toLocaleDateString('he-IL') : '';
        const link = esc(apt.link || '');

        let badge = '';
        if (isRemoved) badge = '<span class="inline-block px-2 py-0.5 text-xs font-semibold rounded-full bg-gray-400 text-white mr-2">הוסר</span>';
        else if (isNew) badge = '<span class="inline-block px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-500 text-white mr-2">חדש</span>';

        // Get floor/sqm - search all text fields
        // Strip RTL/LTR Unicode marks so \d+ works: \u200e \u200f etc.
        const allText = Object.values(apt).filter(v => typeof v === 'string').join(' ')
            .replace(/[\u200e\u200f\u200b\u200c\u200d\u202a-\u202e\u2066-\u2069]/g, '');
        let floorNum = (apt.floor != null && apt.floor !== '') ? parseInt(apt.floor) : null;
        if (floorNum == null || isNaN(floorNum)) {
            floorNum = null;
            const fm = allText.match(/קומה\s*(\d+)/);
            if (fm) { floorNum = parseInt(fm[1]); }
            else if (/קומת\s*קרקע|קומת\s*כניסה/.test(allText)) { floorNum = 0; }
        }
        let sqmVal = apt.sqm;
        if (!sqmVal) {
            const sm = allText.match(/(\d+)\s*(?:מ"ר|מ״ר)/);
            if (sm) sqmVal = parseInt(sm[1]);
        }
        const bldg = floorNum != null ? buildingViz(floorNum, null) : '';

        return `
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow border-2 border-transparent hover:border-brand transition-all p-4">
            <!-- Mobile: stacked, Desktop: row -->
            <div class="flex flex-col sm:flex-row sm:items-center gap-3">

                <!-- Building visualization -->
                ${bldg ? '<div class="flex items-center justify-center px-2">' + bldg + '</div>' : ''}

                <!-- Info -->
                <div class="flex-1 min-w-0">
                    <div class="font-semibold text-sm sm:text-base">
                        ${badge}${esc(apt.title) || 'ללא כותרת'}
                    </div>
                    ${location ? '<div class="font-bold text-sm sm:text-base mt-1 text-emerald-600 dark:text-emerald-400">📍 ' + location + ' <a href="https://www.google.com/maps/search/' + mapQuery + '" target="_blank" class="inline-block text-xs font-medium text-white bg-green-600 hover:bg-green-700 rounded px-1.5 py-0.5 mr-1 align-middle no-underline">🗺️ מפה</a></div>' : ''}
                    <div class="flex flex-wrap gap-x-4 gap-y-1 mt-1.5 text-sm text-gray-600 dark:text-gray-300">
                        ${apt.rooms ? (() => { const rc = roomColor(apt.rooms); return '<span style="background:' + rc.bg + ';color:' + rc.text + ';padding:2px 8px;border-radius:6px;font-weight:bold;font-size:14px">🛏️ ' + apt.rooms + ' חד\\'</span>'; })() : ''}
                        ${sqmVal ? '<span>📐 ' + sqmVal + ' מ"ר</span>' : ''}
                        ${floorNum != null ? '<span>🏢 קומה ' + floorNum + '</span>' : ''}
                        ${firstSeen ? '<span>📅 ' + firstSeen + '</span>' : ''}
                    </div>
                    ${info ? '<div class="text-xs text-gray-400 dark:text-gray-500 mt-1">ℹ️ ' + info + '</div>' : ''}
                </div>

                <!-- Price + Link -->
                <div class="flex items-center gap-3 sm:flex-shrink-0">
                    <span class="text-lg sm:text-xl font-bold text-brand whitespace-nowrap">${price}</span>
                    ${link ? '<a href="' + link + '" target="_blank" class="px-4 py-2 bg-brand text-white text-sm font-semibold rounded-lg hover:opacity-80 whitespace-nowrap">צפייה ביד2</a>' : ''}
                </div>

            </div>
        </div>`;
    }).join('') + '</div>';
}

// Init theme
if (localStorage.getItem('theme') === 'dark' || (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark');
    document.getElementById('theme-btn').textContent = '☀️';
}

loadAll();
setInterval(loadAll, 300000);
</script>
</body>
</html>'''
