/**
 * Menu Management - Product editing
 */

document.addEventListener('DOMContentLoaded', () => {
    setupProductEditing();
});

function setupProductEditing() {
    // Handle inline text/number edits
    document.querySelectorAll('.inline-edit').forEach(input => {
        input.addEventListener('change', async (e) => {
            const productId = e.target.dataset.productId;
            const field = e.target.dataset.field;
            const value = e.target.value;
            
            await updateProduct(productId, { [field]: value });
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
                'Content-Type': 'application/json'
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
        } else {
            alert('Hiba: ' + result.error);
        }
    } catch (error) {
        console.error('Failed to update product:', error);
        alert('Hiba történt a termék frissítése során.');
    }
}

function showSuccessMessage(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 2000);
}

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
