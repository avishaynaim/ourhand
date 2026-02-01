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
        /* Table styles */
        .apt-table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 13px; }
        .apt-table th { position: sticky; top: 0; z-index: 10; cursor: pointer; user-select: none;
            padding: 8px 6px; text-align: right; font-weight: 600; white-space: nowrap;
            border-bottom: 2px solid #667eea; }
        .apt-table th:hover { background: #667eea20; }
        .apt-table th .sort-icon { font-size: 10px; margin-right: 2px; opacity: 0.4; }
        .apt-table th.sorted .sort-icon { opacity: 1; color: #667eea; }
        .apt-table td { padding: 6px 6px; border-bottom: 1px solid #e5e7eb; vertical-align: middle; }
        .dark .apt-table td { border-bottom-color: #374151; }
        .apt-table tr:hover td { background: #667eea10; }
        .apt-table .col-filter { width: 100%; margin-top: 4px; padding: 3px 5px; font-size: 11px;
            border: 1px solid #d1d5db; border-radius: 4px; background: inherit; color: inherit; }
        .dark .apt-table .col-filter { border-color: #4b5563; }
        .table-wrapper { overflow-x: auto; border-radius: 12px; }
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

    <!-- View Title + View Toggle -->
    <div class="flex items-center justify-between mb-4">
        <h2 id="view-title" class="text-lg sm:text-xl font-bold text-brand">🏢 כל הדירות</h2>
        <div class="flex items-center gap-3">
            <span id="view-count" class="text-sm text-gray-500 dark:text-gray-400"></span>
            <div class="flex rounded-lg overflow-hidden border border-gray-300 dark:border-gray-600">
                <button onclick="setViewMode('cards')" id="btn-cards"
                    class="px-3 py-1.5 text-sm font-medium bg-brand text-white">🃏 כרטיסים</button>
                <button onclick="setViewMode('table')" id="btn-table"
                    class="px-3 py-1.5 text-sm font-medium bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600">📊 טבלה</button>
            </div>
        </div>
    </div>

    <!-- Apartment List -->
    <div id="apt-container">
        <div class="text-center py-12 text-gray-400">טוען נתונים...</div>
    </div>

    <!-- Pagination -->
    <div id="pagination" class="hidden flex items-center justify-center gap-2 mt-6 mb-8 flex-wrap">
        <button onclick="changePage(-1)" id="prev-page"
            class="px-3 py-2 text-sm font-medium bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed">
            → הקודם
        </button>
        <div id="page-numbers" class="flex items-center gap-1"></div>
        <button onclick="changePage(1)" id="next-page"
            class="px-3 py-2 text-sm font-medium bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed">
            הבא ←
        </button>
        <select id="page-size" onchange="changePageSize()"
            class="px-2 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800">
            <option value="25">25</option>
            <option value="50" selected>50</option>
            <option value="100">100</option>
            <option value="250">250</option>
        </select>
    </div>

</div>

<script>
let allApts = [];
let removedApts = [];
let currentFilter = 'all';
let healthData = null;
let viewMode = localStorage.getItem('viewMode') || 'cards';
let currentPage = 1;
let pageSize = parseInt(localStorage.getItem('pageSize')) || 50;
let filteredAptsCache = [];
let tableSortCol = 'first_seen';
let tableSortDir = 'desc';
let tableColFilters = {};

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

function setViewMode(mode) {
    viewMode = mode;
    localStorage.setItem('viewMode', mode);
    const bc = document.getElementById('btn-cards');
    const bt = document.getElementById('btn-table');
    if (mode === 'cards') {
        bc.className = 'px-3 py-1.5 text-sm font-medium bg-brand text-white';
        bt.className = 'px-3 py-1.5 text-sm font-medium bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600';
    } else {
        bt.className = 'px-3 py-1.5 text-sm font-medium bg-brand text-white';
        bc.className = 'px-3 py-1.5 text-sm font-medium bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600';
    }
    currentPage = 1;
    document.getElementById('apt-container').innerHTML = '';
    renderCurrentView();
}

async function loadAll() {
    try {
        const [healthRes, aptsRes] = await Promise.all([
            fetch('/health'),
            fetch('/api/apartments?limit=50000&include_inactive=1')
        ]);
        healthData = await healthRes.json();
        const aptsData = await aptsRes.json();
        allApts = Array.isArray(aptsData.apartments) ? aptsData.apartments :
                  Array.isArray(aptsData) ? aptsData : [];
        // Pre-compute extracted fields for each apartment
        allApts.forEach(a => {
            const allText = Object.values(a).filter(v => typeof v === 'string').join(' ')
                .replace(/[\\u200e\\u200f\\u200b\\u200c\\u200d\\u202a-\\u202e\\u2066-\\u2069]/g, '');
            let fn = (a.floor != null && a.floor !== '') ? parseInt(a.floor) : null;
            if (fn == null || isNaN(fn)) {
                fn = null;
                const fm = allText.match(/קומה\\s*(\\d+)/);
                if (fm) fn = parseInt(fm[1]);
                else if (/קומת\\s*קרקע|קומת\\s*כניסה/.test(allText)) fn = 0;
            }
            a._floor = fn;
            if (!a.sqm) {
                const sm = allText.match(/(\\d+)\\s*(?:מ"ר|מ״ר)/);
                if (sm) a._sqm = parseInt(sm[1]);
            } else {
                a._sqm = parseInt(a.sqm);
            }
        });
        removedApts = allApts.filter(a => !a.is_active);
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
    const todayStart = new Date(); todayStart.setHours(0,0,0,0);
    const todayEnd = new Date(todayStart); todayEnd.setDate(todayEnd.getDate()+1);
    const todayApts = allApts.filter(a => {
        const fs = new Date(a.first_seen).getTime();
        const ls = a.last_seen ? new Date(a.last_seen).getTime() : fs;
        return (fs >= todayStart.getTime() && fs < todayEnd.getTime()) ||
               (ls >= todayStart.getTime() && ls < todayEnd.getTime());
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
    currentPage = 1;
    // Reset table so header rebuilds for new data set
    document.getElementById('apt-container').innerHTML = '';
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
        'all': '🏢 כל הדירות', 'new': '🆕 דירות חדשות (48 שעות)',
        'today': '📅 דירות היום (24 שעות)', 'price-drop': '📉 ירידות מחיר',
        'removed': '🚫 דירות שהוסרו', 'avg': '💰 כל הדירות (לפי מחיר)'
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
            const ts = new Date(); ts.setHours(0,0,0,0);
            const te = new Date(ts); te.setDate(te.getDate()+1);
            return allApts.filter(a => {
                const fs = new Date(a.first_seen).getTime();
                const ls = a.last_seen ? new Date(a.last_seen).getTime() : fs;
                return (fs >= ts.getTime() && fs < te.getTime()) || (ls >= ts.getTime() && ls < te.getTime());
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
    filteredAptsCache = apts;
    renderCurrentView();
}

function clearFilters() {
    document.getElementById('f-search').value = '';
    document.getElementById('f-min-price').value = '';
    document.getElementById('f-max-price').value = '';
    document.getElementById('f-sort').value = 'date';
    tableColFilters = {};
    applyFilters();
}

function renderCurrentView() {
    if (viewMode === 'table') {
        // Table: header stays, only body updates
        renderTable();
        const total = getTableFilteredCount();
        document.getElementById('view-count').textContent = total + ' דירות';
        renderPagination(total);
    } else {
        // Cards: paginate from filteredAptsCache
        const apts = filteredAptsCache;
        const totalPages = Math.max(1, Math.ceil(apts.length / pageSize));
        if (currentPage > totalPages) currentPage = totalPages;
        const start = (currentPage - 1) * pageSize;
        const pageApts = apts.slice(start, start + pageSize);
        document.getElementById('view-count').textContent = apts.length + ' דירות';
        // Clear table structure if switching from table
        const container = document.getElementById('apt-container');
        if (container.querySelector('.apt-table')) container.innerHTML = '';
        renderCards(pageApts);
        renderPagination(apts.length);
    }
}

// Pagination
function renderPagination(total) {
    const pg = document.getElementById('pagination');
    const totalPages = Math.max(1, Math.ceil(total / pageSize));
    if (totalPages <= 1) { pg.classList.add('hidden'); return; }
    pg.classList.remove('hidden');
    document.getElementById('prev-page').disabled = currentPage <= 1;
    document.getElementById('next-page').disabled = currentPage >= totalPages;
    document.getElementById('page-size').value = pageSize;

    // Page numbers
    const pn = document.getElementById('page-numbers');
    let pages = [];
    const maxBtns = 7;
    if (totalPages <= maxBtns) {
        for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
        pages.push(1);
        let s = Math.max(2, currentPage - 2);
        let e = Math.min(totalPages - 1, currentPage + 2);
        if (s > 2) pages.push('...');
        for (let i = s; i <= e; i++) pages.push(i);
        if (e < totalPages - 1) pages.push('...');
        pages.push(totalPages);
    }
    pn.innerHTML = pages.map(p => {
        if (p === '...') return '<span class="px-2 text-gray-400">...</span>';
        const active = p === currentPage ? 'bg-brand text-white' : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700';
        return '<button onclick="goToPage(' + p + ')" class="w-9 h-9 text-sm font-medium border border-gray-300 dark:border-gray-600 rounded-lg ' + active + '">' + p + '</button>';
    }).join('');
}

function changePage(delta) { goToPage(currentPage + delta); }
function goToPage(p) {
    const total = viewMode === 'table' ? getTableFilteredCount() : filteredAptsCache.length;
    const totalPages = Math.max(1, Math.ceil(total / pageSize));
    currentPage = Math.max(1, Math.min(p, totalPages));
    if (viewMode === 'table') {
        renderTableBody();
        renderPagination(total);
    } else {
        renderCurrentView();
    }
    document.getElementById('apt-container').scrollIntoView({behavior:'smooth', block:'start'});
}
function changePageSize() {
    pageSize = parseInt(document.getElementById('page-size').value) || 50;
    localStorage.setItem('pageSize', pageSize);
    currentPage = 1;
    if (viewMode === 'table') {
        const total = getTableFilteredCount();
        renderTableBody();
        renderPagination(total);
    } else {
        renderCurrentView();
    }
}

function roomColor(rooms) {
    if (!rooms) return null;
    const r = parseFloat(rooms);
    if (r <= 1.5) return { bg: '#6b7280', text: '#fff' };
    if (r <= 2)   return { bg: '#8b5cf6', text: '#fff' };
    if (r <= 2.5) return { bg: '#a78bfa', text: '#fff' };
    if (r <= 3)   return { bg: '#3b82f6', text: '#fff' };
    if (r <= 3.5) return { bg: '#06b6d4', text: '#fff' };
    if (r <= 4)   return { bg: '#10b981', text: '#fff' };
    if (r <= 4.5) return { bg: '#f59e0b', text: '#fff' };
    if (r <= 5)   return { bg: '#ef4444', text: '#fff' };
    if (r <= 5.5) return { bg: '#ec4899', text: '#fff' };
    return              { bg: '#dc2626', text: '#fff' };
}

function buildingViz(floor, totalFloors) {
    if (floor == null || floor < 0) return '';
    const total = Math.max(totalFloors || 9, floor + 1, 3);
    const maxShow = 12;
    const W = 56, FH = 12, GH = 14;
    let floorsToShow = [];
    if (total + 1 <= maxShow) {
        for (let f = total; f >= 0; f--) floorsToShow.push(f);
    } else {
        const keep = new Set();
        keep.add(total); keep.add(total - 1); keep.add(0); keep.add(1);
        for (let f = Math.max(0, floor - 1); f <= Math.min(total, floor + 1); f++) keep.add(f);
        const sorted = [...keep].sort((a, b) => b - a);
        for (let i = 0; i < sorted.length; i++) {
            floorsToShow.push(sorted[i]);
            if (i < sorted.length - 1 && sorted[i] - sorted[i + 1] > 1) floorsToShow.push('dots');
        }
    }
    let html = '<div style="display:flex;flex-direction:column;align-items:center;flex-shrink:0;min-width:' + (W+30) + 'px" title="קומה ' + floor + ' מתוך ' + total + '">';
    html += '<div style="width:0;height:0;border-left:' + (W/2) + 'px solid transparent;border-right:' + (W/2) + 'px solid transparent;border-bottom:10px solid #6b7280;margin-bottom:1px"></div>';
    for (const f of floorsToShow) {
        if (f === 'dots') {
            html += '<div style="width:'+W+'px;height:12px;display:flex;justify-content:center;align-items:center;gap:3px"><div style="width:4px;height:4px;background:#9ca3af;border-radius:50%"></div><div style="width:4px;height:4px;background:#9ca3af;border-radius:50%"></div><div style="width:4px;height:4px;background:#9ca3af;border-radius:50%"></div></div>';
            continue;
        }
        const isTarget = f === floor;
        const bg = isTarget ? 'background:#667eea;' : 'background:#e5e7eb;';
        const border = isTarget ? 'border:2px solid #4f46e5;' : 'border:1px solid #d1d5db;';
        const h = f === 0 ? GH : FH;
        let inner = '';
        if (f > 0) {
            const wc = isTarget ? '#fff' : '#9ca3af';
            inner = '<div style="display:flex;gap:3px;justify-content:center;align-items:center;height:100%"><div style="width:7px;height:6px;background:'+wc+';border-radius:1px"></div><div style="width:7px;height:6px;background:'+wc+';border-radius:1px"></div><div style="width:7px;height:6px;background:'+wc+';border-radius:1px"></div></div>';
        } else {
            const dc = isTarget ? '#fff' : '#9ca3af';
            inner = '<div style="display:flex;justify-content:center;align-items:end;height:100%"><div style="width:8px;height:8px;background:'+dc+';border-radius:1px 1px 0 0"></div></div>';
        }
        const label = isTarget ? '<span style="position:absolute;right:-24px;top:50%;transform:translateY(-50%);font-size:9px;font-weight:bold;color:#667eea;line-height:1">◄ '+floor+'</span>' : '';
        html += '<div style="position:relative;width:'+W+'px;height:'+h+'px;'+bg+border+'margin-bottom:-1px;border-radius:1px;">'+inner+label+'</div>';
    }
    html += '<div style="width:'+(W+8)+'px;height:2px;background:#6b7280;margin-top:1px"></div></div>';
    return html;
}

// Mini building for table rows - compact inline SVG-like visualization
function miniBuildingViz(floor) {
    if (floor == null || floor < 0) return '';
    const total = Math.max(floor + 1, 3);
    const maxF = Math.min(total, 8);
    const W = 18, FH = 3;
    const totalH = maxF * FH + 6;
    let html = '<span style="display:inline-block;vertical-align:middle;width:'+W+'px;height:'+totalH+'px;position:relative;margin-left:3px" title="' + (floor === 0 ? 'קרקע' : 'קומה '+floor) + '">';
    // Roof
    html += '<span style="position:absolute;top:0;left:50%;transform:translateX(-50%);width:0;height:0;border-left:'+(W/2)+'px solid transparent;border-right:'+(W/2)+'px solid transparent;border-bottom:4px solid #6b7280"></span>';
    for (let f = maxF - 1; f >= 0; f--) {
        const y = 4 + (maxF - 1 - f) * FH;
        const isTarget = f === floor;
        const bg = isTarget ? '#667eea' : '#d1d5db';
        html += '<span style="position:absolute;top:'+y+'px;left:0;width:'+W+'px;height:'+(FH-1)+'px;background:'+bg+';"></span>';
    }
    // Ground
    html += '<span style="position:absolute;bottom:0;left:-1px;width:'+(W+2)+'px;height:1px;background:#6b7280"></span>';
    html += '</span>';
    return html;
}

// ===== TABLE VIEW =====
let tableHeaderBuilt = false;
let uniqueRooms = [];

function buildRoomOptions() {
    const rooms = new Set();
    allApts.forEach(a => { if (a.rooms) rooms.add(parseFloat(a.rooms)); });
    uniqueRooms = [...rooms].sort((a,b) => a - b);
}

function tableSort(col) {
    if (tableSortCol === col) {
        tableSortDir = tableSortDir === 'asc' ? 'desc' : 'asc';
    } else {
        tableSortCol = col;
        tableSortDir = (col === 'price' || col === 'rooms' || col === 'sqm' || col === 'floor') ? 'asc' : 'desc';
    }
    updateSortIcons();
    renderTableBody();
    renderPagination(getTableFilteredCount());
}

function updateSortIcons() {
    document.querySelectorAll('.apt-table th').forEach(th => {
        const col = th.dataset.sortCol;
        if (!col) return;
        const icon = th.querySelector('.sort-icon');
        if (!icon) return;
        if (tableSortCol === col) {
            th.classList.add('sorted');
            icon.textContent = tableSortDir === 'asc' ? '▲' : '▼';
        } else {
            th.classList.remove('sorted');
            icon.textContent = '⇅';
        }
    });
}

let uniqueTypes = [];
let uniqueCities = [];
let uniqueNeighborhoods = [];

function buildDropdownOptions() {
    const types = new Set(), cities = new Set(), hoods = new Set();
    allApts.forEach(a => {
        if (a.apartment_type) types.add(a.apartment_type);
        if (a.city) cities.add(a.city);
        if (a.neighborhood) hoods.add(a.neighborhood);
    });
    uniqueTypes = [...types].sort((a,b) => a.localeCompare(b, 'he'));
    uniqueCities = [...cities].sort((a,b) => a.localeCompare(b, 'he'));
    uniqueNeighborhoods = [...hoods].sort((a,b) => a.localeCompare(b, 'he'));
}

function tableFilterChanged() {
    // Read all filter values from the DOM
    const rf = document.getElementById('tf-rooms');
    if (rf) tableColFilters.rooms = rf.value;
    ['title','address','date'].forEach(k => {
        const el = document.getElementById('tf-'+k);
        if (el) tableColFilters[k] = el.value;
    });
    ['price','sqm','floor'].forEach(k => {
        const mn = document.getElementById('tf-'+k+'-min');
        const mx = document.getElementById('tf-'+k+'-max');
        if (mn) tableColFilters[k+'_min'] = mn.value;
        if (mx) tableColFilters[k+'_max'] = mx.value;
    });
    // Dropdowns
    ['status','apt_type','city','neighborhood'].forEach(k => {
        const el = document.getElementById('tf-'+k);
        if (el) tableColFilters[k] = el.value;
    });
    // Cascade: update dropdown options based on currently matching data
    updateCascadingDropdowns();
    currentPage = 1;
    renderTableBody();
    renderPagination(getTableFilteredCount());
    document.getElementById('view-count').textContent = getTableFilteredCount() + ' דירות';
}

function updateCascadingDropdowns() {
    // Get the base dataset (main filter applied, before table column filters)
    let base = filteredAptsCache;
    const atv = tableColFilters.apt_type || '';
    const cv = tableColFilters.city || '';
    const nv = tableColFilters.neighborhood || '';

    // For each dropdown, compute available options from data filtered by OTHER dropdowns
    // Type options: filtered by city + neighborhood
    let forType = base;
    if (cv) forType = forType.filter(a => a.city === cv);
    if (nv) forType = forType.filter(a => a.neighborhood === nv);
    const typesSet = new Set();
    forType.forEach(a => { if (a.apartment_type) typesSet.add(a.apartment_type); });

    // City options: filtered by type + neighborhood
    let forCity = base;
    if (atv) forCity = forCity.filter(a => a.apartment_type === atv);
    if (nv) forCity = forCity.filter(a => a.neighborhood === nv);
    const citiesSet = new Set();
    forCity.forEach(a => { if (a.city) citiesSet.add(a.city); });

    // Neighborhood options: filtered by type + city
    let forHood = base;
    if (atv) forHood = forHood.filter(a => a.apartment_type === atv);
    if (cv) forHood = forHood.filter(a => a.city === cv);
    const hoodsSet = new Set();
    forHood.forEach(a => { if (a.neighborhood) hoodsSet.add(a.neighborhood); });

    // Rooms options: filtered by type + city + neighborhood
    let forRooms = base;
    if (atv) forRooms = forRooms.filter(a => a.apartment_type === atv);
    if (cv) forRooms = forRooms.filter(a => a.city === cv);
    if (nv) forRooms = forRooms.filter(a => a.neighborhood === nv);
    const roomsSet = new Set();
    forRooms.forEach(a => { if (a.rooms) roomsSet.add(parseFloat(a.rooms)); });

    // Update each dropdown in the DOM
    updateSelectOptions('tf-apt_type', [...typesSet].sort((a,b) => a.localeCompare(b,'he')), atv, v => v);
    updateSelectOptions('tf-city', [...citiesSet].sort((a,b) => a.localeCompare(b,'he')), cv, v => v);
    updateSelectOptions('tf-neighborhood', [...hoodsSet].sort((a,b) => a.localeCompare(b,'he')), nv, v => v);
    updateSelectOptions('tf-rooms', [...roomsSet].sort((a,b) => a-b), tableColFilters.rooms || '', v => v + " חד'");
}

function updateSelectOptions(elId, options, currentVal, labelFn) {
    const el = document.getElementById(elId);
    if (!el) return;
    // Remember if current value is still valid
    const stillValid = !currentVal || options.some(v => String(v) === currentVal);
    let html = '<option value="">הכל</option>';
    options.forEach(v => {
        const sv = String(v);
        const sel = sv === currentVal ? ' selected' : '';
        html += '<option value="'+esc(sv)+'"'+sel+'>'+esc(labelFn(v))+'</option>';
    });
    el.innerHTML = html;
    // If selected value no longer valid, reset it
    if (!stillValid) {
        el.value = '';
        tableColFilters[elId.replace('tf-','')] = '';
    }
}

function getTableFiltered() {
    let apts = filteredAptsCache;
    // Text filters
    ['title','address','date'].forEach(k => {
        const v = (tableColFilters[k] || '').trim().toLowerCase();
        if (!v) return;
        apts = apts.filter(a => {
            let val = '';
            switch(k) {
                case 'title': val = a.title || ''; break;
                case 'address': val = (a.street_address || a.location || ''); break;
                case 'date': val = a.first_seen ? new Date(a.first_seen).toLocaleDateString('he-IL') : ''; break;
            }
            return val.toLowerCase().includes(v);
        });
    });
    // Rooms dropdown
    const rv = tableColFilters.rooms || '';
    if (rv) {
        const rn = parseFloat(rv);
        apts = apts.filter(a => parseFloat(a.rooms) === rn);
    }
    // Status dropdown
    const sv = tableColFilters.status || '';
    if (sv === 'active') apts = apts.filter(a => a.is_active !== 0);
    else if (sv === 'removed') apts = apts.filter(a => a.is_active === 0);
    else if (sv === 'new') {
        const now = Date.now(); const td = 48*60*60*1000;
        apts = apts.filter(a => a.is_active !== 0 && (now - new Date(a.first_seen).getTime()) < td);
    }
    // Dropdown filters: apartment type, city, neighborhood
    const atv = tableColFilters.apt_type || '';
    if (atv) apts = apts.filter(a => a.apartment_type === atv);
    const cv = tableColFilters.city || '';
    if (cv) apts = apts.filter(a => a.city === cv);
    const nv = tableColFilters.neighborhood || '';
    if (nv) apts = apts.filter(a => a.neighborhood === nv);
    // Range filters: price, sqm, floor
    ['price','sqm','floor'].forEach(k => {
        const mn = parseFloat(tableColFilters[k+'_min']) || -Infinity;
        const mx = parseFloat(tableColFilters[k+'_max']) || Infinity;
        if (mn === -Infinity && mx === Infinity) return;
        apts = apts.filter(a => {
            let v;
            switch(k) {
                case 'price': v = a.price; break;
                case 'sqm': v = a._sqm || a.sqm; break;
                case 'floor': v = a._floor; break;
            }
            if (v == null) return false;
            return v >= mn && v <= mx;
        });
    });
    // Sort
    apts = [...apts];
    const dir = tableSortDir === 'asc' ? 1 : -1;
    apts.sort((a, b) => {
        let va, vb;
        switch(tableSortCol) {
            case 'price': va = a.price||0; vb = b.price||0; break;
            case 'rooms': va = parseFloat(a.rooms)||0; vb = parseFloat(b.rooms)||0; break;
            case 'sqm': va = a._sqm||0; vb = b._sqm||0; break;
            case 'floor': va = a._floor!=null?a._floor:-1; vb = b._floor!=null?b._floor:-1; break;
            case 'first_seen': va = new Date(a.first_seen||0).getTime(); vb = new Date(b.first_seen||0).getTime(); break;
            default: va = (a[tableSortCol]||'').toString(); vb = (b[tableSortCol]||'').toString();
                return dir * va.localeCompare(vb, 'he');
        }
        return dir * ((va > vb) - (va < vb));
    });
    return apts;
}

function getTableFilteredCount() {
    return getTableFiltered().length;
}

function makeDropdown(id, options, label) {
    return '<div><select class="col-filter" id="'+id+'" onchange="tableFilterChanged()" onclick="event.stopPropagation()">' +
        '<option value="">הכל</option>' +
        options.map(v => '<option value="'+esc(v)+'">'+esc(v)+'</option>').join('') +
        '</select></div>';
}

function ensureTableStructure() {
    const container = document.getElementById('apt-container');
    if (container.querySelector('.apt-table')) return; // already built
    if (!uniqueRooms.length) buildRoomOptions();
    if (!uniqueTypes.length) buildDropdownOptions();
    const cols = [
        {key:'status', sortKey:'status', label:'סטטוס', w:'80px', filter:'status'},
        {key:'apt_type', sortKey:'apartment_type', label:'🏠 סוג', w:'100px', filter:'dropdown', opts: uniqueTypes, tfId:'tf-apt_type'},
        {key:'city', sortKey:'city', label:'🏙️ עיר', w:'110px', filter:'dropdown', opts: uniqueCities, tfId:'tf-city'},
        {key:'neighborhood', sortKey:'neighborhood', label:'📍 שכונה', w:'110px', filter:'dropdown', opts: uniqueNeighborhoods, tfId:'tf-neighborhood'},
        {key:'address', sortKey:'street_address', label:'כתובת', w:'', filter:'text'},
        {key:'rooms', sortKey:'rooms', label:'🛏️ חדרים', w:'100px', filter:'rooms'},
        {key:'sqm', sortKey:'sqm', label:'📐 מ"ר', w:'100px', filter:'range'},
        {key:'floor', sortKey:'floor', label:'🏢 קומה', w:'100px', filter:'range'},
        {key:'price', sortKey:'price', label:'💰 מחיר', w:'130px', filter:'range'},
        {key:'date', sortKey:'first_seen', label:'📅 תאריך', w:'90px', filter:'text'},
        {key:'link', sortKey:'', label:'קישור', w:'55px', filter:'none'}
    ];
    let html = '<div class="table-wrapper bg-white dark:bg-gray-800 rounded-xl shadow"><table class="apt-table">';
    html += '<thead class="bg-gray-50 dark:bg-gray-700"><tr>';
    cols.forEach(c => {
        const w = c.w ? 'width:'+c.w+';' : '';
        const sorted = tableSortCol === c.sortKey ? ' sorted' : '';
        const sortIcon = tableSortCol === c.sortKey ? (tableSortDir === 'asc' ? '▲' : '▼') : '⇅';
        const sortClick = c.sortKey ? ' onclick="tableSort(\\''+c.sortKey+'\\')" data-sort-col="'+c.sortKey+'"' : '';
        let filterHtml = '';
        if (c.filter === 'text') {
            filterHtml = '<div><input class="col-filter" id="tf-'+c.key+'" placeholder="סנן..." ' +
                'oninput="tableFilterChanged()" onclick="event.stopPropagation()"></div>';
        } else if (c.filter === 'rooms') {
            filterHtml = '<div><select class="col-filter" id="tf-rooms" onchange="tableFilterChanged()" onclick="event.stopPropagation()">' +
                '<option value="">הכל</option>' +
                uniqueRooms.map(r => '<option value="'+r+'">'+r+' חד\\'</option>').join('') +
                '</select></div>';
        } else if (c.filter === 'range') {
            filterHtml = '<div style="display:flex;gap:2px;margin-top:4px" onclick="event.stopPropagation()">' +
                '<input type="number" class="col-filter" id="tf-'+c.key+'-min" placeholder="מ-" style="width:48%" oninput="tableFilterChanged()">' +
                '<input type="number" class="col-filter" id="tf-'+c.key+'-max" placeholder="עד" style="width:48%" oninput="tableFilterChanged()">' +
                '</div>';
        } else if (c.filter === 'status') {
            filterHtml = '<div><select class="col-filter" id="tf-status" onchange="tableFilterChanged()" onclick="event.stopPropagation()">' +
                '<option value="">הכל</option><option value="active">פעיל</option><option value="new">חדש</option><option value="removed">הוסר</option>' +
                '</select></div>';
        } else if (c.filter === 'dropdown') {
            filterHtml = makeDropdown(c.tfId, c.opts, 'הכל');
        }
        html += '<th'+sortClick+' style="'+w+'" class="'+sorted+'">' +
            (c.sortKey ? '<span class="sort-icon">'+sortIcon+'</span> ' : '') +
            esc(c.label) + filterHtml + '</th>';
    });
    html += '</tr></thead><tbody id="table-body"></tbody></table></div>';
    container.innerHTML = html;
}

function renderTableBody() {
    const allFiltered = getTableFiltered();
    const totalPages = Math.max(1, Math.ceil(allFiltered.length / pageSize));
    if (currentPage > totalPages) currentPage = totalPages;
    const start = (currentPage - 1) * pageSize;
    const apts = allFiltered.slice(start, start + pageSize);
    const tbody = document.getElementById('table-body');
    if (!tbody) return;

    if (!apts.length) {
        tbody.innerHTML = '<tr><td colspan="11" class="text-center py-8 text-gray-400">🤷 אין דירות להצגה</td></tr>';
        return;
    }
    const now = Date.now();
    const twoDays = 48 * 60 * 60 * 1000;
    let html = '';
    apts.forEach(apt => {
        const isNew = (now - new Date(apt.first_seen).getTime()) < twoDays;
        const isRemoved = apt.is_active === 0;
        const price = apt.price ? '₪' + apt.price.toLocaleString() : '-';
        const location = apt.street_address || apt.location || '';
        const mapQuery = encodeURIComponent((location || apt.title || '') + ' Israel');
        const floorNum = apt._floor;
        const sqmVal = apt._sqm || apt.sqm || '';
        const firstSeen = apt.first_seen ? new Date(apt.first_seen).toLocaleDateString('he-IL') : '';
        const link = apt.link || '';

        let statusBadge;
        if (isRemoved) statusBadge = '<span class="inline-block px-2 py-0.5 text-xs font-semibold rounded-full bg-gray-400 text-white">הוסר</span>';
        else if (isNew) statusBadge = '<span class="inline-block px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-500 text-white">חדש</span>';
        else statusBadge = '<span class="inline-block px-2 py-0.5 text-xs font-semibold rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300">פעיל</span>';

        const roomsBadge = apt.rooms ? (() => {
            const rc = roomColor(apt.rooms);
            return '<span style="background:'+rc.bg+';color:'+rc.text+';padding:1px 6px;border-radius:4px;font-weight:bold;font-size:12px">'+apt.rooms+'</span>';
        })() : '-';

        // Mini building viz for floor column
        const floorLabel = floorNum != null ? (floorNum === 0 ? 'קרקע' : floorNum) : '-';
        const miniBldg = floorNum != null ? miniBuildingViz(floorNum) : '';

        html += '<tr>' +
            '<td>'+statusBadge+'</td>' +
            '<td class="text-xs">'+esc(apt.apartment_type || '-')+'</td>' +
            '<td class="text-xs">'+esc(apt.city || '-')+'</td>' +
            '<td class="text-xs" style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="'+esc(apt.neighborhood||'')+'">'+esc(apt.neighborhood || '-')+'</td>' +
            '<td class="text-sm">' + (location ? esc(location) + ' <a href="https://www.google.com/maps/search/'+mapQuery+'" target="_blank" class="text-green-600 hover:text-green-800 text-xs">🗺️</a>' : '-') + '</td>' +
            '<td class="text-center">'+roomsBadge+'</td>' +
            '<td class="text-center">'+(sqmVal || '-')+'</td>' +
            '<td class="text-center" style="white-space:nowrap">'+miniBldg+' <span class="text-xs font-medium">'+floorLabel+'</span></td>' +
            '<td class="font-bold text-brand text-sm whitespace-nowrap">'+price+'</td>' +
            '<td class="text-xs whitespace-nowrap">'+firstSeen+'</td>' +
            '<td>'+(link ? '<a href="'+esc(link)+'" target="_blank" class="text-brand hover:underline text-xs font-medium">יד2</a>' : '-')+'</td>' +
            '</tr>';
    });
    tbody.innerHTML = html;
}

function renderTable() {
    ensureTableStructure();
    renderTableBody();
}

// ===== CARD VIEW =====
function renderCards(apts) {
    const container = document.getElementById('apt-container');
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
        const floorNum = apt._floor;
        const sqmVal = apt._sqm || apt.sqm;

        let badge = '';
        if (isRemoved) badge = '<span class="inline-block px-2 py-0.5 text-xs font-semibold rounded-full bg-gray-400 text-white mr-2">הוסר</span>';
        else if (isNew) badge = '<span class="inline-block px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-500 text-white mr-2">חדש</span>';

        const bldg = floorNum != null ? buildingViz(floorNum, null) : '';

        return '<div class="bg-white dark:bg-gray-800 rounded-xl shadow border-2 border-transparent hover:border-brand transition-all p-4">' +
            '<div class="flex flex-col sm:flex-row sm:items-center gap-3">' +
            (bldg ? '<div class="flex items-center justify-center px-2">'+bldg+'</div>' : '') +
            '<div class="flex-1 min-w-0">' +
            '<div class="font-semibold text-sm sm:text-base">'+badge+esc(apt.title || 'ללא כותרת')+'</div>' +
            (location ? '<div class="font-bold text-sm sm:text-base mt-1 text-emerald-600 dark:text-emerald-400">📍 '+location+' <a href="https://www.google.com/maps/search/'+mapQuery+'" target="_blank" class="inline-block text-xs font-medium text-white bg-green-600 hover:bg-green-700 rounded px-1.5 py-0.5 mr-1 align-middle no-underline">🗺️ מפה</a></div>' : '') +
            '<div class="flex flex-wrap gap-x-4 gap-y-1 mt-1.5 text-sm text-gray-600 dark:text-gray-300">' +
            (apt.rooms ? (() => { const rc = roomColor(apt.rooms); return '<span style="background:'+rc.bg+';color:'+rc.text+';padding:2px 8px;border-radius:6px;font-weight:bold;font-size:14px">🛏️ '+apt.rooms+' חד\\'</span>'; })() : '') +
            (sqmVal ? '<span>📐 '+sqmVal+' מ"ר</span>' : '') +
            (floorNum != null ? '<span>🏢 קומה '+floorNum+'</span>' : '') +
            (firstSeen ? '<span>📅 '+firstSeen+'</span>' : '') +
            '</div>' +
            (info ? '<div class="text-xs text-gray-400 dark:text-gray-500 mt-1">ℹ️ '+info+'</div>' : '') +
            '</div>' +
            '<div class="flex items-center gap-3 sm:flex-shrink-0">' +
            '<span class="text-lg sm:text-xl font-bold text-brand whitespace-nowrap">'+price+'</span>' +
            (link ? '<a href="'+link+'" target="_blank" class="px-4 py-2 bg-brand text-white text-sm font-semibold rounded-lg hover:opacity-80 whitespace-nowrap">צפייה ביד2</a>' : '') +
            '</div></div></div>';
    }).join('') + '</div>';
}

// Init theme
if (localStorage.getItem('theme') === 'dark' || (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark');
    document.getElementById('theme-btn').textContent = '☀️';
}

// Init view mode
if (viewMode === 'table') setViewMode('table');

loadAll();
setInterval(loadAll, 300000);
</script>
</body>
</html>'''
