/**
 * NEMIS - National Election Management Information System
 * Main JavaScript File
 * Handles form validation, confirmations, and UI interactions
 */

// ============================================================
// 1. CONFIRMATION DIALOGS
// ============================================================

/**
 * Confirm voting action
 * @param {string} candidateName - Name of the candidate
 * @returns {boolean} - User confirmation
 */
function confirmVote(candidateName) {
    return confirm(
        `Are you sure you want to vote for ${candidateName}?\n\n` +
        `⚠️ This action cannot be undone.`
    );
}

/**
 * Confirm candidate approval/rejection
 * @param {string} action - 'approve' or 'reject'
 * @param {string} name - Candidate name
 * @returns {boolean} - User confirmation
 */
function confirmCandidateAction(action, name) {
    const message = action === 'approve' 
        ? `Approve ${name} as a candidate?`
        : `Reject ${name}'s candidacy?`;
    
    return confirm(message);
}

/**
 * Confirm election deletion
 * @param {string} electionName - Name of the election
 * @returns {boolean} - User confirmation
 */
function confirmDeleteElection(electionName) {
    return confirm(
        `⚠️ WARNING: Delete election "${electionName}"?\n\n` +
        `This will permanently delete all associated data including:\n` +
        `• All candidates\n` +
        `• All votes\n` +
        `• All results\n\n` +
        `This action CANNOT be undone!`
    );
}

/**
 * Confirm user deletion
 * @param {string} userName - Name of the user
 * @returns {boolean} - User confirmation
 */
function confirmDeleteUser(userName) {
    return confirm(
        `Delete user "${userName}"?\n\n` +
        `This action cannot be undone.`
    );
}

// ============================================================
// 2. FORM VALIDATION
// ============================================================

/**
 * Validate CNIE format (2 letters + 6 digits)
 * @param {string} cnie - CNIE to validate
 * @returns {boolean} - Validation result
 */
function validateCNIE(cnie) {
    const pattern = /^[A-Z]{2}\d{6}$/;
    return pattern.test(cnie);
}

/**
 * Validate name (2-100 characters, letters only)
 * @param {string} name - Name to validate
 * @returns {boolean} - Validation result
 */
function validateName(name) {
    if (!name || name.trim().length < 2 || name.trim().length > 100) {
        return false;
    }
    const pattern = /^[a-zA-ZÀ-ÿ\s\'-]+$/;
    return pattern.test(name);
}

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean} - Validation result
 */
function validateEmail(email) {
    const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return pattern.test(email);
}

/**
 * Validate date range (start before end)
 * @param {string} startDate - Start date
 * @param {string} endDate - End date
 * @returns {boolean} - Validation result
 */
function validateDateRange(startDate, endDate) {
    const start = new Date(startDate);
    const end = new Date(endDate);
    return start < end;
}

/**
 * Validate form before submission
 * @param {HTMLFormElement} form - Form to validate
 * @returns {boolean} - Validation result
 */
function validateForm(form) {
    let isValid = true;
    const errors = [];
    
    // Check CNIE if present
    const cnieInput = form.querySelector('input[name="cnie"]');
    if (cnieInput && !validateCNIE(cnieInput.value.toUpperCase())) {
        errors.push('Invalid CNIE format. Expected: AA123456');
        isValid = false;
    }
    
    // Check name if present
    const nameInput = form.querySelector('input[name="name"]');
    if (nameInput && !validateName(nameInput.value)) {
        errors.push('Invalid name. Must be 2-100 characters, letters only.');
        isValid = false;
    }
    
    // Check date range if present
    const startDateInput = form.querySelector('input[name="start_date"]');
    const endDateInput = form.querySelector('input[name="end_date"]');
    if (startDateInput && endDateInput && !validateDateRange(startDateInput.value, endDateInput.value)) {
        errors.push('End date must be after start date.');
        isValid = false;
    }
    
    // Show errors if any
    if (!isValid) {
        alert('Please fix the following errors:\n\n' + errors.join('\n'));
    }
    
    return isValid;
}

// ============================================================
// 3. UI ENHANCEMENTS
// ============================================================

/**
 * Auto-dismiss alerts after a delay
 * @param {number} delay - Delay in milliseconds (default: 5000)
 */
function autoDismissAlerts(delay = 5000) {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, delay);
    });
}

/**
 * Add close button functionality to alerts
 */
function initAlertClose() {
    const closeButtons = document.querySelectorAll('.alert-close');
    closeButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const alert = this.parentElement;
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        });
    });
}

/**
 * Format CNIE input to uppercase automatically
 */
function initCNIEFormatter() {
    const cnieInputs = document.querySelectorAll('input[name="cnie"], input[name="CNIE"]');
    cnieInputs.forEach(input => {
        input.addEventListener('input', function() {
            this.value = this.value.toUpperCase();
        });
    });
}

/**
 * Show loading spinner on form submission
 * @param {HTMLFormElement} form - Form element
 */
function showLoadingOnSubmit(form) {
    form.addEventListener('submit', function() {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span>⏳ Loading...</span>';
        }
    });
}

/**
 * Add table row highlighting
 */
function initTableRowHighlight() {
    const tables = document.querySelectorAll('.table');
    tables.forEach(table => {
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            row.addEventListener('mouseenter', function() {
                this.style.backgroundColor = 'rgba(52, 152, 219, 0.1)';
            });
            row.addEventListener('mouseleave', function() {
                this.style.backgroundColor = '';
            });
        });
    });
}

/**
 * Character counter for textareas
 * @param {HTMLTextAreaElement} textarea - Textarea element
 * @param {number} maxLength - Maximum character length
 */
function addCharacterCounter(textarea, maxLength) {
    const counter = document.createElement('div');
    counter.className = 'form-help';
    counter.style.textAlign = 'right';
    textarea.parentNode.appendChild(counter);
    
    function updateCounter() {
        const remaining = maxLength - textarea.value.length;
        counter.textContent = `${remaining} characters remaining`;
        counter.style.color = remaining < 50 ? 'var(--danger-color)' : 'var(--text-light)';
    }
    
    textarea.addEventListener('input', updateCounter);
    updateCounter();
}

/**
 * Initialize tooltips
 */
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', function() {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = this.getAttribute('data-tooltip');
            tooltip.style.position = 'absolute';
            tooltip.style.backgroundColor = 'var(--primary-color)';
            tooltip.style.color = 'var(--white)';
            tooltip.style.padding = 'var(--spacing-xs)';
            tooltip.style.borderRadius = 'var(--border-radius-sm)';
            tooltip.style.fontSize = '0.875rem';
            tooltip.style.zIndex = '1000';
            
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.top = (rect.top - tooltip.offsetHeight - 5) + 'px';
            tooltip.style.left = (rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2)) + 'px';
            
            this._tooltip = tooltip;
        });
        
        element.addEventListener('mouseleave', function() {
            if (this._tooltip) {
                this._tooltip.remove();
                delete this._tooltip;
            }
        });
    });
}

// ============================================================
// 4. SEARCH & FILTER
// ============================================================

/**
 * Table search functionality
 * @param {HTMLInputElement} searchInput - Search input element
 * @param {HTMLTableElement} table - Table to search
 */
function initTableSearch(searchInput, table) {
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(searchTerm) ? '' : 'none';
        });
    });
}

/**
 * Add search box to table
 * @param {HTMLTableElement} table - Table element
 */
function addTableSearch(table) {
    const searchBox = document.createElement('div');
    searchBox.className = 'mb-2';
    searchBox.innerHTML = `
        <input type="text" class="form-control" placeholder="🔍 Search..." id="table-search">
    `;
    
    table.parentNode.insertBefore(searchBox, table);
    
    const searchInput = searchBox.querySelector('#table-search');
    initTableSearch(searchInput, table);
}

// ============================================================
// 5. INITIALIZATION
// ============================================================

/**
 * Initialize all features on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize alerts
    autoDismissAlerts();
    initAlertClose();
    
    // Initialize form enhancements
    initCNIEFormatter();
    
    // Initialize table features
    initTableRowHighlight();
    
    // Initialize tooltips
    initTooltips();
    
    // Add form validation to all forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        showLoadingOnSubmit(form);
    });
    
    // Add character counters to textareas with maxlength
    const textareas = document.querySelectorAll('textarea[maxlength]');
    textareas.forEach(textarea => {
        const maxLength = parseInt(textarea.getAttribute('maxlength'));
        addCharacterCounter(textarea, maxLength);
    });
    
    console.log('✓ NEMIS JavaScript initialized');
});

// ============================================================
// 6. UTILITY FUNCTIONS
// ============================================================

/**
 * Format date to readable string
 * @param {string} dateString - Date string
 * @returns {string} - Formatted date
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

/**
 * Format datetime to readable string
 * @param {string} dateTimeString - Datetime string
 * @returns {string} - Formatted datetime
 */
function formatDateTime(dateTimeString) {
    const date = new Date(dateTimeString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert('Copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

/**
 * Print page
 */
function printPage() {
    window.print();
}

/**
 * Scroll to top smoothly
 */
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Export functions for use in inline scripts
window.NEMIS = {
    confirmVote,
    confirmCandidateAction,
    confirmDeleteElection,
    confirmDeleteUser,
    validateForm,
    formatDate,
    formatDateTime,
    copyToClipboard,
    printPage,
    scrollToTop
};
