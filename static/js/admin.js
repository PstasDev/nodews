/**
 * Büfé Admin Dashboard - Real-time Order Management
 */

// Configuration
const WS_PROTOCOL = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_HOST = window.location.host;
const WS_URL = `${WS_PROTOCOL}//${WS_HOST}/ws/bufe/orders/`;

// State
let ws = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
let reconnectTimeout = null;
let orders = new Map();
let currentFilter = 'all';
let lastOrderCount = 0;

// DOM Elements
const ordersGrid = document.getElementById('ordersGrid');
const orderCount = document.getElementById('orderCount');
const connectionStatus = document.getElementById('connectionStatus');
const refreshBtn = document.getElementById('refreshBtn');
const archiveAllBtn = document.getElementById('archiveAllBtn');
const orderModal = document.getElementById('orderModal');
const archiveModal = document.getElementById('archiveModal');
const modalClose = document.getElementById('modalClose');
const archiveModalClose = document.getElementById('archiveModalClose');
const archiveCancelBtn = document.getElementById('archiveCancelBtn');
const archiveConfirmBtn = document.getElementById('archiveConfirmBtn');
const filterTabs = document.querySelectorAll('.filter-tab');
const notificationSound = document.getElementById('notificationSound');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initWebSocket();
    loadOrders();
    setupEventListeners();
    setupFilters();
});

// WebSocket Functions
function initWebSocket() {
    try {
        ws = new WebSocket(WS_URL);
        
        ws.onopen = () => {
            console.log('WebSocket connected');
            updateConnectionStatus('connected');
            reconnectAttempts = 0;
        };
        
        ws.onmessage = (event) => {
            handleWebSocketMessage(JSON.parse(event.data));
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            updateConnectionStatus('error');
        };
        
        ws.onclose = () => {
            console.log('WebSocket disconnected');
            updateConnectionStatus('disconnected');
            scheduleReconnect();
        };
    } catch (error) {
        console.error('Failed to initialize WebSocket:', error);
        updateConnectionStatus('error');
    }
}

function handleWebSocketMessage(data) {
    console.log('WebSocket message:', data);
    
    switch (data.type) {
        case 'order_update':
            handleOrderUpdate(data.action, data.order);
            break;
        case 'pong':
            // Heartbeat response
            break;
        case 'error':
            console.error('WebSocket error:', data.message);
            break;
    }
}

function handleOrderUpdate(action, order) {
    switch (action) {
        case 'new':
            addNewOrder(order);
            playNotificationSound();
            flashOrder(order.id);
            break;
        case 'update':
            updateOrder(order);
            break;
        case 'archive':
            removeOrder(order.id);
            break;
        case 'archive_all':
            loadOrders(); // Reload all orders
            break;
    }
    updateOrderCount();
}

function scheduleReconnect() {
    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
        console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts})`);
        
        reconnectTimeout = setTimeout(() => {
            initWebSocket();
        }, delay);
    } else {
        console.error('Max reconnection attempts reached');
        updateConnectionStatus('failed');
    }
}

function updateConnectionStatus(status) {
    const statusDot = connectionStatus.querySelector('.status-dot');
    const statusText = connectionStatus.querySelector('.status-text');
    
    connectionStatus.className = 'connection-status';
    
    switch (status) {
        case 'connected':
            connectionStatus.classList.add('connected');
            statusText.textContent = 'Kapcsolódva';
            break;
        case 'disconnected':
            connectionStatus.classList.add('disconnected');
            statusText.textContent = 'Kapcsolat megszakadt';
            break;
        case 'error':
            connectionStatus.classList.add('error');
            statusText.textContent = 'Kapcsolódási hiba';
            break;
        case 'failed':
            connectionStatus.classList.add('error');
            statusText.textContent = 'Sikertelen kapcsolódás';
            break;
    }
}

// API Functions
async function loadOrders() {
    try {
        const response = await fetch('/bufe/admin/api/orders/');
        const data = await response.json();
        
        if (data.success) {
            orders.clear();
            data.orders.forEach(order => {
                orders.set(order.id, order);
            });
            renderOrders();
            updateOrderCount();
        }
    } catch (error) {
        console.error('Failed to load orders:', error);
    }
}

async function updateOrderStatus(orderId, status) {
    try {
        const response = await fetch('/bufe/admin/api/update-order/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                order_id: orderId,
                status: status
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            updateOrder(data.order);
        } else {
            alert('Hiba: ' + data.error);
        }
    } catch (error) {
        console.error('Failed to update order:', error);
        alert('Hiba történt a rendelés frissítése során.');
    }
}

async function archiveOrder(orderId) {
    try {
        const response = await fetch('/bufe/admin/api/archive-order/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                order_id: orderId
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            removeOrder(orderId);
        } else {
            alert('Hiba: ' + data.error);
        }
    } catch (error) {
        console.error('Failed to archive order:', error);
        alert('Hiba történt a rendelés archiválása során.');
    }
}

async function archiveAllDone() {
    try {
        const response = await fetch('/bufe/admin/api/archive-all-done/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            alert(`${data.archived_count} rendelés archiválva.`);
            loadOrders();
        } else {
            alert('Hiba: ' + data.error);
        }
    } catch (error) {
        console.error('Failed to archive all orders:', error);
        alert('Hiba történt a rendelések archiválása során.');
    }
}

// UI Functions
function renderOrders() {
    const filteredOrders = Array.from(orders.values()).filter(order => {
        if (currentFilter === 'all') return true;
        return order.allapot === currentFilter;
    });
    
    if (filteredOrders.length === 0) {
        ordersGrid.innerHTML = '<div class="no-orders"><p>📭 Nincsenek rendelések</p></div>';
        return;
    }
    
    ordersGrid.innerHTML = filteredOrders.map(order => createOrderCard(order)).join('');
    
    // Attach event listeners
    document.querySelectorAll('.order-card').forEach(card => {
        let tapCount = 0;
        let tapTimer = null;
        
        card.addEventListener('click', (e) => {
            if (e.target.closest('.btn-action')) return;
            
            tapCount++;
            
            if (tapCount === 1) {
                tapTimer = setTimeout(() => {
                    // Single tap - show details
                    showOrderDetails(card.dataset.orderId);
                    tapCount = 0;
                }, 300);
            } else if (tapCount === 2) {
                // Double tap - mark as next status
                clearTimeout(tapTimer);
                const orderId = parseInt(card.dataset.orderId);
                const order = orders.get(orderId);
                
                if (order) {
                    // Double tap transitions:
                    // leadva -> visszaigasolva
                    // visszaigasolva -> atadva
                    if (order.allapot === 'leadva') {
                        updateOrderStatus(orderId, 'visszaigasolva');
                    } else if (order.allapot === 'visszaigasolva') {
                        updateOrderStatus(orderId, 'atadva');
                    }
                }
                
                tapCount = 0;
            }
        });
    });
    
    // Attach button event listeners
    document.querySelectorAll('.btn-action').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const card = e.target.closest('.order-card');
            const orderId = parseInt(card.dataset.orderId);
            const action = e.target.dataset.action;
            
            if (action === 'archive') {
                archiveOrder(orderId);
            } else {
                updateOrderStatus(orderId, action);
            }
        });
    });
}

function createOrderCard(order) {
    const statusClass = `status-${order.allapot}`;
    const itemsPreview = order.items.slice(0, 3).map(item => 
        `<span class="item-badge">${item.mennyiseg}x ${item.termek_nev}</span>`
    ).join('');
    const moreItems = order.items.length > 3 ? 
        `<span class="item-badge">+${order.items.length - 3} további</span>` : '';
    
    let actions = '';
    if (order.allapot === 'leadva') {
        actions = `
            <button class="btn-action btn-confirm" data-action="visszaigasolva">✓ Visszaigazol</button>
            <button class="btn-action btn-delete" data-action="torolve">✕ Töröl</button>
        `;
    } else if (order.allapot === 'visszaigasolva') {
        actions = `
            <button class="btn-action btn-done" data-action="atadva">✓✓ Kész</button>
            <button class="btn-action btn-delete" data-action="torolve">✕ Töröl</button>
        `;
    } else if (order.allapot === 'atadva') {
        actions = `
            <button class="btn-action btn-undo" data-action="visszaigasolva">↶ Visszavon</button>
            <button class="btn-action btn-archive" data-action="archive">📦 Archivál</button>
        `;
    } else if (order.allapot === 'torolve') {
        actions = `
            <button class="btn-action btn-undo" data-action="visszaigasolva">↶ Visszaállít</button>
            <button class="btn-action btn-archive" data-action="archive">📦 Archivál</button>
        `;
    } else if (order.allapot === 'visszavonva') {
        actions = `
            <button class="btn-action btn-undo" data-action="visszaigasolva">↶ Visszaállít</button>
            <button class="btn-action btn-archive" data-action="archive">📦 Archivál</button>
        `;
    }
    
    return `
        <div class="order-card" data-order-id="${order.id}" data-status="${order.allapot}">
            <div class="order-header">
                <div class="order-number">#${order.id}</div>
                <div class="order-status ${statusClass}">${order.allapot_display}</div>
            </div>
            <div class="order-body">
                <div class="order-user"><strong>${order.user.full_name}</strong></div>
                <div class="order-time">${formatDateTime(order.leadva)}</div>
                <div class="order-items-preview">${itemsPreview}${moreItems}</div>
                <div class="order-total">${order.vegosszeg} Ft</div>
                ${order.megjegyzes ? `<div class="order-note">💬 ${order.megjegyzes}</div>` : ''}
            </div>
            <div class="order-actions">${actions}</div>
        </div>
    `;
}

function addNewOrder(order) {
    orders.set(order.id, order);
    renderOrders();
}

function updateOrder(order) {
    orders.set(order.id, order);
    renderOrders();
}

function removeOrder(orderId) {
    orders.delete(orderId);
    renderOrders();
    updateOrderCount();
}

function flashOrder(orderId) {
    setTimeout(() => {
        const card = document.querySelector(`[data-order-id="${orderId}"]`);
        if (card) {
            card.classList.add('flash');
            setTimeout(() => card.classList.remove('flash'), 2000);
        }
    }, 100);
}

function showOrderDetails(orderId) {
    const order = orders.get(parseInt(orderId));
    if (!order) return;
    
    const itemsList = order.items.map(item => `
        <tr>
            <td>${item.termek_nev}</td>
            <td class="text-center">${item.mennyiseg} db</td>
            <td class="text-right">${item.termek_ar} Ft</td>
            <td class="text-right">${item.osszeg} Ft</td>
        </tr>
    `).join('');
    
    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `
        <div class="order-detail">
            <div class="detail-row">
                <span class="detail-label">Rendelésszám:</span>
                <span class="detail-value">#${order.id}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Vásárló:</span>
                <span class="detail-value">${order.user.full_name}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Email:</span>
                <span class="detail-value">${order.user.email}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Leadva:</span>
                <span class="detail-value">${formatDateTime(order.leadva)}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Állapot:</span>
                <span class="detail-value status-${order.allapot}">${order.allapot_display}</span>
            </div>
            ${order.megjegyzes ? `
            <div class="detail-row">
                <span class="detail-label">Megjegyzés:</span>
                <span class="detail-value">${order.megjegyzes}</span>
            </div>
            ` : ''}
            <h4>Tételek:</h4>
            <table class="items-table">
                <thead>
                    <tr>
                        <th>Termék</th>
                        <th class="text-center">Mennyiség</th>
                        <th class="text-right">Egységár</th>
                        <th class="text-right">Összeg</th>
                    </tr>
                </thead>
                <tbody>${itemsList}</tbody>
                <tfoot>
                    <tr>
                        <td colspan="3" class="text-right"><strong>Végösszeg:</strong></td>
                        <td class="text-right"><strong>${order.vegosszeg} Ft</strong></td>
                    </tr>
                </tfoot>
            </table>
        </div>
    `;
    
    orderModal.style.display = 'flex';
}

function updateOrderCount() {
    const count = orders.size;
    orderCount.textContent = `${count} rendelés`;
    
    // Update document title if count changed
    if (count !== lastOrderCount) {
        document.title = `(${count}) Büfé Admin - Rendelések`;
        lastOrderCount = count;
    }
}

function setupFilters() {
    filterTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            filterTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentFilter = tab.dataset.filter;
            renderOrders();
        });
    });
}

function setupEventListeners() {
    refreshBtn.addEventListener('click', () => {
        loadOrders();
    });
    
    archiveAllBtn.addEventListener('click', () => {
        archiveModal.style.display = 'flex';
    });
    
    modalClose.addEventListener('click', () => {
        orderModal.style.display = 'none';
    });
    
    archiveModalClose.addEventListener('click', () => {
        archiveModal.style.display = 'none';
    });
    
    archiveCancelBtn.addEventListener('click', () => {
        archiveModal.style.display = 'none';
    });
    
    archiveConfirmBtn.addEventListener('click', () => {
        archiveModal.style.display = 'none';
        archiveAllDone();
    });
    
    // Close modals on outside click
    window.addEventListener('click', (e) => {
        if (e.target === orderModal) {
            orderModal.style.display = 'none';
        }
        if (e.target === archiveModal) {
            archiveModal.style.display = 'none';
        }
    });
}

// Notification Sound
function playNotificationSound() {
    try {
        // Reset audio to beginning if it's already playing
        notificationSound.currentTime = 0;
        
        // Try to play the audio file
        const playPromise = notificationSound.play();
        
        if (playPromise !== undefined) {
            playPromise.catch((error) => {
                console.warn('Audio playback failed:', error);
                // Fallback to Web Audio API if playback fails
                playBeep();
            });
        }
    } catch (error) {
        console.error('Error playing notification sound:', error);
        // Fallback to Web Audio API
        playBeep();
    }
}

function playBeep() {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
    } catch (error) {
        console.error('Failed to play notification sound:', error);
    }
}

// Utility Functions
function formatDateTime(dateString) {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}.${month}.${day} ${hours}:${minutes}`;
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Get CSRF token - try multiple possible names
function getCSRFToken() {
    // Try to get from cookie
    let token = getCookie('csrftoken');
    
    // If not found, try to get from hidden input
    if (!token) {
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) {
            token = csrfInput.value;
        }
    }
    
    // If still not found, try meta tag
    if (!token) {
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (csrfMeta) {
            token = csrfMeta.content;
        }
    }
    
    return token;
}

// Heartbeat to keep connection alive
setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
    }
}, 30000); // Every 30 seconds
