/**
 * Opening Hours Management
 */

document.addEventListener('DOMContentLoaded', () => {
    setupEmergencyClose();
    setupInlineEditing();
});

function setupInlineEditing() {
    // Handle time input changes
    document.querySelectorAll('.inline-edit-time').forEach(input => {
        input.addEventListener('change', function() {
            const ohId = this.dataset.ohId;
            const field = this.dataset.field;
            const value = this.value;
            
            updateOpeningHours(ohId, field, value, this);
        });
    });
}

async function updateOpeningHours(ohId, field, value, inputElement) {
    const originalValue = inputElement.defaultValue;
    
    try {
        const response = await fetch('/bufe/admin/api/update-opening-hours/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                id: ohId,
                [field]: value
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Update the default value to the new value
            inputElement.defaultValue = value;
            
            // Visual feedback
            inputElement.style.backgroundColor = '#d4edda';
            setTimeout(() => {
                inputElement.style.backgroundColor = '';
            }, 1000);
            
            showSuccessMessage('Nyitvatartás frissítve');
        } else {
            alert('Hiba: ' + data.error);
            inputElement.value = originalValue; // Revert
        }
    } catch (error) {
        console.error('Failed to update opening hours:', error);
        alert('Hiba történt a frissítés során.');
        inputElement.value = originalValue; // Revert
    }
}

function setupEmergencyClose() {
    const checkbox = document.getElementById('rendkivuliZarva');
    
    if (checkbox) {
        checkbox.addEventListener('change', async (e) => {
            const isChecked = e.target.checked;
            
            try {
                const response = await fetch('/bufe/admin/api/update-bufe/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        rendkivuli_zarva: isChecked
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                
                if (data.success) {
                    showSuccessMessage(isChecked ? 'Büfé zárva jelölve' : 'Büfé nyitva jelölve');
                } else {
                    alert('Hiba: ' + data.error);
                    e.target.checked = !isChecked; // Revert
                }
            } catch (error) {
                console.error('Failed to update büfé status:', error);
                alert('Hiba történt a frissítés során.');
                e.target.checked = !isChecked; // Revert
            }
        });
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
