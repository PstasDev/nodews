/**
 * Menu Management - Product editing with WebSocket support
 */

// Configuration
const WS_PROTOCOL = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_HOST = window.location.host;
const WS_URL = `${WS_PROTOCOL}//${WS_HOST}/ws/bufe/orders/`;

// State
let ws = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
let categories = window.CATEGORIES || [];

// DOM Elements
const addProductBtn = document.getElementById('addProductBtn');
const addProductModal = document.getElementById('addProductModal');
const addProductModalClose = document.getElementById('addProductModalClose');
const addProductForm = document.getElementById('addProductForm');
const addProductSubmit = document.getElementById('addProductSubmit');
const addProductCancel = document.getElementById('addProductCancel');
const connectionStatus = document.getElementById('connectionStatus');

document.addEventListener('DOMContentLoaded', () => {
    initWebSocket();
    setupProductEditing();
    setupAddProductModal();
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
        case 'product_update':
            if (data.action === 'add') {
                addProductToTable(data.product);
                showSuccessMessage('Új termék hozzáadva!');
            }
            break;
        case 'add_product_response':
            handleAddProductResponse(data);
            break;
        case 'pong':
            // Heartbeat response
            break;
        case 'error':
            console.error('WebSocket error:', data.message);
            break;
    }
}

function scheduleReconnect() {
    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
        console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts})`);
        
        setTimeout(() => {
            initWebSocket();
        }, delay);
    } else {
        console.error('Max reconnection attempts reached');
        updateConnectionStatus('error');
    }
}

function updateConnectionStatus(status) {
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
    }
}

// Product Management
function setupProductEditing() {
    // Handle inline text/number edits
    document.querySelectorAll('.inline-edit').forEach(input => {
        input.addEventListener('change', async (e) => {
            const productId = e.target.dataset.productId;
            const field = e.target.dataset.field;
            const value = e.target.value;
            
            await updateProduct(productId, { [field]: value });
        });
        
        // Auto-save on blur for better UX
        input.addEventListener('blur', (e) => {
            if (e.target.dataset.changed) {
                e.target.dispatchEvent(new Event('change'));
                delete e.target.dataset.changed;
            }
        });
        
        // Mark as changed on input
        input.addEventListener('input', (e) => {
            e.target.dataset.changed = 'true';
        });
    });
    
    // Handle checkbox toggles
    document.querySelectorAll('input[type="checkbox"][data-product-id]').forEach(checkbox => {
        checkbox.addEventListener('change', async (e) => {
            const productId = e.target.dataset.productId;
            const field = e.target.dataset.field;
            const value = e.target.checked;
            
            await updateProduct(productId, { [field]: value });
        });
    });
}

async function updateProduct(productId, data) {
    try {
        const response = await fetch('/bufe/admin/api/update-product/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                product_id: productId,
                ...data
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            showSuccessMessage('Mentve');
            
            // Update row styling if availability changed
            if ('elerheto' in data) {
                const row = document.querySelector(`[data-product-id="${productId}"]`);
                if (row) {
                    if (data.elerheto) {
                        row.classList.remove('product-unavailable');
                    } else {
                        row.classList.add('product-unavailable');
                    }
                }
            }
        } else {
            showErrorMessage('Hiba: ' + result.error);
        }
    } catch (error) {
        console.error('Failed to update product:', error);
        showErrorMessage('Hiba történt a termék frissítése során.');
    }
}

// Add Product Modal
function setupAddProductModal() {
    if (!addProductBtn) return;
    
    addProductBtn.addEventListener('click', () => {
        showAddProductModal();
    });
    
    addProductModalClose.addEventListener('click', () => {
        hideAddProductModal();
    });
    
    addProductCancel.addEventListener('click', () => {
        hideAddProductModal();
    });
    
    addProductSubmit.addEventListener('click', (e) => {
        e.preventDefault();
        submitAddProduct();
    });
    
    // Close modal on outside click
    addProductModal.addEventListener('click', (e) => {
        if (e.target === addProductModal) {
            hideAddProductModal();
        }
    });
    
    // Form validation
    const requiredFields = addProductForm.querySelectorAll('[required]');
    requiredFields.forEach(field => {
        field.addEventListener('input', validateForm);
    });
}

function showAddProductModal() {
    addProductModal.classList.add('show');
    
    // Focus on first input
    const firstInput = addProductForm.querySelector('input[type="text"]');
    if (firstInput) {
        setTimeout(() => firstInput.focus(), 100);
    }
}

function hideAddProductModal() {
    addProductModal.classList.remove('show');
    addProductForm.reset();
    clearFormErrors();
}

function validateForm() {
    const requiredFields = addProductForm.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
        }
    });
    
    addProductSubmit.disabled = !isValid;
    return isValid;
}

function clearFormErrors() {
    addProductForm.querySelectorAll('.form-error').forEach(error => {
        error.remove();
    });
    addProductForm.querySelectorAll('.error').forEach(field => {
        field.classList.remove('error');
    });
}

async function submitAddProduct() {
    if (!validateForm()) {
        showErrorMessage('Kérjük, töltse ki a kötelező mezőket!');
        return;
    }
    
    const formData = new FormData(addProductForm);
    const productData = {
        nev: formData.get('nev'),
        kategoria_id: parseInt(formData.get('kategoria_id')),
        ar: parseInt(formData.get('ar')),
        max_rendelesenkent: parseInt(formData.get('max_rendelesenkent')) || 1,
        hutve: formData.has('hutve'),
        elerheto: formData.has('elerheto'),
        kisult: formData.has('kisult')
    };
    
    // Disable submit button
    addProductSubmit.disabled = true;
    addProductSubmit.textContent = 'Hozzáadás...';
    
    try {
        if (ws && ws.readyState === WebSocket.OPEN) {
            // Use WebSocket for real-time update
            ws.send(JSON.stringify({
                type: 'add_product',
                ...productData
            }));
        } else {
            // Fallback to REST API
            await addProductViaAPI(productData);
        }
    } catch (error) {
        console.error('Error adding product:', error);
        showErrorMessage('Hiba történt a termék hozzáadása során.');
        
        // Re-enable submit button
        addProductSubmit.disabled = false;
        addProductSubmit.textContent = 'Termék hozzáadása';
    }
}

async function addProductViaAPI(productData) {
    const response = await fetch('/bufe/admin/api/add-product/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(productData)
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    if (result.success) {
        addProductToTable(result.product);
        hideAddProductModal();
        showSuccessMessage('Termék sikeresen hozzáadva!');
    } else {
        throw new Error(result.error);
    }
}

function handleAddProductResponse(data) {
    // Re-enable submit button
    addProductSubmit.disabled = false;
    addProductSubmit.textContent = 'Termék hozzáadása';
    
    if (data.success) {
        hideAddProductModal();
    } else {
        showErrorMessage(data.error);
    }
}

function addProductToTable(product) {
    const categoryId = product.kategoria_id;
    const tbody = document.getElementById(`products-tbody-${categoryId}`);
    
    if (!tbody) {
        console.warn('Category tbody not found for:', categoryId);
        // Refresh page if category not found
        setTimeout(() => location.reload(), 1000);
        return;
    }
    
    const row = createProductRow(product);
    tbody.appendChild(row);
    
    // Setup event listeners for the new row
    setupProductRowEvents(row);
    
    // Highlight new row
    row.classList.add('flash');
    setTimeout(() => row.classList.remove('flash'), 2000);
}

function createProductRow(product) {
    const row = document.createElement('tr');
    row.className = `product-row ${product.elerheto ? '' : 'product-unavailable'}`;
    row.dataset.productId = product.id;
    
    row.innerHTML = `
        <td class="product-name-cell">
            <span class="product-name-text">${escapeHtml(product.nev)}</span>
        </td>
        <td class="product-price-cell">
            <div class="input-wrapper">
                <input type="number" class="inline-edit price-input" 
                       data-product-id="${product.id}" 
                       data-field="ar" 
                       value="${product.ar}" 
                       min="0"
                       step="10">
                <span class="currency">Ft</span>
            </div>
        </td>
        <td class="product-max-cell">
            <div class="input-wrapper">
                <input type="number" class="inline-edit max-input" 
                       data-product-id="${product.id}" 
                       data-field="max_rendelesenkent" 
                       value="${product.max_rendelesenkent}" 
                       min="1"
                       max="10">
                <span class="unit">db</span>
            </div>
        </td>
        <td class="product-toggle-cell">
            <label class="switch">
                <input type="checkbox" 
                       data-product-id="${product.id}" 
                       data-field="elerheto"
                       ${product.elerheto ? 'checked' : ''}>
                <span class="slider"></span>
            </label>
        </td>
        <td class="product-toggle-cell">
            <label class="switch">
                <input type="checkbox" 
                       data-product-id="${product.id}" 
                       data-field="hutve"
                       ${product.hutve ? 'checked' : ''}>
                <span class="slider"></span>
            </label>
        </td>
        <td class="product-toggle-cell">
            <label class="switch">
                <input type="checkbox" 
                       data-product-id="${product.id}" 
                       data-field="kisult"
                       ${product.kisult ? 'checked' : ''}>
                <span class="slider"></span>
            </label>
        </td>
        <td class="product-actions-cell">
            <a href="/admin/bufe/termek/${product.id}/change/" 
               class="btn-action btn-edit" 
               target="_blank"
               title="Szerkesztés">
                ✏️
            </a>
        </td>
    `;
    
    return row;
}

function setupProductRowEvents(row) {
    // Setup inline editing
    row.querySelectorAll('.inline-edit').forEach(input => {
        input.addEventListener('change', async (e) => {
            const productId = e.target.dataset.productId;
            const field = e.target.dataset.field;
            const value = e.target.value;
            
            await updateProduct(productId, { [field]: value });
        });
        
        input.addEventListener('blur', (e) => {
            if (e.target.dataset.changed) {
                e.target.dispatchEvent(new Event('change'));
                delete e.target.dataset.changed;
            }
        });
        
        input.addEventListener('input', (e) => {
            e.target.dataset.changed = 'true';
        });
    });
    
    // Setup toggles
    row.querySelectorAll('input[type="checkbox"][data-product-id]').forEach(checkbox => {
        checkbox.addEventListener('change', async (e) => {
            const productId = e.target.dataset.productId;
            const field = e.target.dataset.field;
            const value = e.target.checked;
            
            await updateProduct(productId, { [field]: value });
        });
    });
}

// UI Helper Functions
function showSuccessMessage(message) {
    showToast(message, 'success');
}

function showErrorMessage(message) {
    showToast(message, 'error');
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, type === 'error' ? 4000 : 2000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Utility Functions
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function getCSRFToken() {
    let token = getCookie('csrftoken');
    if (!token) {
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) {
            token = csrfInput.value;
        }
    }
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
