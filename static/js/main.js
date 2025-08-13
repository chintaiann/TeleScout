// TeleScout GUI JavaScript

// Global utility functions
function showAlert(message, type, container = 'alertContainer') {
    const alertContainer = document.getElementById(container);
    if (!alertContainer) return;
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    alertContainer.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

function showLoading(element) {
    const originalContent = element.innerHTML;
    element.innerHTML = `
        <span class="spinner-border spinner-border-sm me-2" role="status"></span>
        Loading...
    `;
    element.disabled = true;
    
    return () => {
        element.innerHTML = originalContent;
        element.disabled = false;
    };
}

// API helper functions
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || `HTTP ${response.status}`);
        }
        
        return data;
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Form validation
function validateRequired(fields) {
    const errors = [];
    
    fields.forEach(field => {
        const element = document.getElementById(field.id);
        if (!element) return;
        
        const value = element.value.trim();
        if (field.required && !value) {
            errors.push(`${field.label} is required`);
            element.classList.add('is-invalid');
        } else {
            element.classList.remove('is-invalid');
        }
        
        // Custom validation
        if (value && field.validate && !field.validate(value)) {
            errors.push(`${field.label} is invalid`);
            element.classList.add('is-invalid');
        }
    });
    
    return errors;
}

// Initialize tooltips and other Bootstrap components
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-dismiss alerts after 10 seconds
    document.querySelectorAll('.alert:not(.alert-permanent)').forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 10000);
    });
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl+S to save configuration (if on config page)
    if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        if (typeof saveConfig === 'function') {
            saveConfig();
        }
    }
    
    // Escape to close modals or clear forms
    if (e.key === 'Escape') {
        // Clear any active form inputs
        const activeElement = document.activeElement;
        if (activeElement && activeElement.tagName === 'INPUT') {
            activeElement.blur();
        }
    }
});

// Auto-save form data to localStorage (for better UX)
function enableAutoSave(formId, storageKey) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    // Load saved data
    const savedData = localStorage.getItem(storageKey);
    if (savedData) {
        try {
            const data = JSON.parse(savedData);
            Object.keys(data).forEach(key => {
                const element = document.getElementById(key);
                if (element) {
                    element.value = data[key];
                }
            });
        } catch (e) {
            console.warn('Failed to load saved form data:', e);
        }
    }
    
    // Save data on change
    form.addEventListener('input', function(e) {
        const formData = {};
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (input.id) {
                formData[input.id] = input.value;
            }
        });
        localStorage.setItem(storageKey, JSON.stringify(formData));
    });
}

// Clear auto-saved data
function clearAutoSave(storageKey) {
    localStorage.removeItem(storageKey);
}

// Network status indicator
function updateNetworkStatus() {
    const isOnline = navigator.onLine;
    const statusElement = document.getElementById('networkStatus');
    
    if (statusElement) {
        statusElement.className = isOnline ? 'text-success' : 'text-danger';
        statusElement.textContent = isOnline ? 'Online' : 'Offline';
    }
}

window.addEventListener('online', updateNetworkStatus);
window.addEventListener('offline', updateNetworkStatus);

// Initialize network status on load
document.addEventListener('DOMContentLoaded', updateNetworkStatus);