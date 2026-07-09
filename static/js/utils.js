/**
 * E-Council JavaScript Utilities
 * Common utility functions for use across the application
 */

// ============================================
// Modal Handling
// ============================================

/**
 * Initialize a modal with open, close, and click-outside handlers
 * @param {string} openButtonId - ID of the button that opens the modal
 * @param {string} closeButtonId - ID of the button that closes the modal
 * @param {string} cancelButtonId - ID of the cancel button (optional)
 * @param {string} modalContentId - ID of the modal content element
 */
function initializeModal(openButtonId, closeButtonId, cancelButtonId, modalContentId) {
    const openButton = document.getElementById(openButtonId);
    const closeButton = document.getElementById(closeButtonId);
    const cancelButton = cancelButtonId ? document.getElementById(cancelButtonId) : null;
    const modalContent = document.getElementById(modalContentId);

    if (openButton && modalContent) {
        openButton.addEventListener('click', () => {
            modalContent.classList.remove('hidden');
        });
    }

    if (closeButton && modalContent) {
        closeButton.addEventListener('click', () => {
            modalContent.classList.add('hidden');
        });
    }

    if (cancelButton && modalContent) {
        cancelButton.addEventListener('click', () => {
            modalContent.classList.add('hidden');
        });
    }

    if (modalContent) {
        window.addEventListener('click', (event) => {
            if (event.target === modalContent) {
                modalContent.classList.add('hidden');
            }
        });
    }
}

// ============================================
// File Upload Handling
// ============================================

/**
 * Set up file input change event to display file name
 * @param {string} inputId - ID of the file input element
 * @param {string} fileNameSpanId - ID of the span to display the file name
 */
function setupFileNameDisplay(inputId, fileNameSpanId) {
    const input = document.getElementById(inputId);
    const fileNameSpan = document.getElementById(fileNameSpanId);

    if (input && fileNameSpan) {
        input.addEventListener('change', function () {
            const fileName = this.files[0] ? this.files[0].name : 'No file chosen';
            fileNameSpan.textContent = fileName;
        });
    }
}

/**
 * Validate image file type
 * @param {File} file - The file to validate
 * @param {string[]} validTypes - Array of valid MIME types
 * @returns {boolean} - True if file type is valid
 */
function isValidImageFile(file, validTypes = ['image/jpeg', 'image/png', 'image/jpg']) {
    return validTypes.includes(file.type);
}

/**
 * Preview an image file
 * @param {File} file - The image file to preview
 * @param {string} previewElementId - ID of the image preview element
 * @param {string} fileNameSpanId - ID of the span to display the file name
 */
function previewImageFile(file, previewElementId, fileNameSpanId) {
    const preview = document.getElementById(previewElementId);
    const fileNameSpan = document.getElementById(fileNameSpanId);
    const validImageTypes = ['image/jpeg', 'image/png', 'image/jpg'];

    if (file) {
        if (isValidImageFile(file, validImageTypes)) {
            if (fileNameSpan) {
                fileNameSpan.textContent = file.name;
            }
            const reader = new FileReader();
            reader.onload = function (e) {
                if (preview) {
                    preview.src = e.target.result;
                }
            };
            reader.readAsDataURL(file);
        } else {
            if (fileNameSpan) {
                fileNameSpan.textContent = 'No file chosen';
            }
            if (preview) {
                preview.src = '';
            }
        }
    }
}

// ============================================
// API Call Utilities
// ============================================

/**
 * Get CSRF token from the page
 * @returns {string|null} - The CSRF token or null if not found
 */
function getCSRFToken() {
    // Try meta tag first (preferred)
    const metaToken = document.querySelector('meta[name="csrf-token"]');
    if (metaToken) {
        return metaToken.getAttribute('content');
    }

    // Try input field (fallback)
    const inputToken = document.querySelector('input[name="csrf_token"]');
    if (inputToken) {
        return inputToken.value;
    }

    console.error('CSRF token not found');
    return null;
}

/**
 * Make an authenticated API call with CSRF token
 * @param {string} url - The API endpoint
 * @param {object} data - The data to send in the request body
 * @param {object} options - Additional fetch options
 * @returns {Promise<Response>} - The fetch response
 */
async function authenticatedFetch(url, data = {}, options = {}) {
    const csrfToken = getCSRFToken();
    if (!csrfToken) {
        throw new Error('CSRF token is missing. Please refresh the page.');
    }

    const defaultOptions = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(data),
        credentials: 'same-origin'
    };

    const mergedOptions = { ...defaultOptions, ...options };
    mergedOptions.headers = { ...defaultOptions.headers, ...options.headers };

    const response = await fetch(url, mergedOptions);
    return response;
}

/**
 * Handle API response with error checking
 * @param {Response} response - The fetch response
 * @returns {Promise<object>} - The parsed JSON data
 */
async function handleAPIResponse(response) {
    const contentType = response.headers.get('content-type');
    
    if (contentType && contentType.includes('application/json')) {
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || `Server error: ${response.status}`);
        }
        
        return data;
    } else {
        const responseText = await response.text();
        console.error('Non-JSON response:', responseText);
        throw new Error('Server returned non-JSON response');
    }
}

/**
 * Generate content using AI API
 * @param {string} endpoint - The API endpoint
 * @param {object} data - The data to send
 * @param {string} targetId - ID of the target element to update
 * @returns {Promise<void>}
 */
async function generateContent(endpoint, data, targetId) {
    try {
        const response = await authenticatedFetch(endpoint, data);
        const responseData = await handleAPIResponse(response);

        if (responseData.content) {
            document.getElementById(targetId).value = responseData.content;
        } else {
            throw new Error('No content in server response');
        }
    } catch (error) {
        console.error('Error in generateContent:', error);
        alert(`Error generating content: ${error.message}`);
    }
}

/**
 * Set button loading state
 * @param {HTMLElement} button - The button element
 * @param {string} loadingText - Text to show while loading
 * @param {boolean} isLoading - Whether to show loading state
 */
function setButtonLoading(button, loadingText, isLoading = true) {
    if (!button) return;

    if (isLoading) {
        button.dataset.originalText = button.textContent;
        button.textContent = loadingText;
        button.disabled = true;
    } else {
        button.textContent = button.dataset.originalText || button.textContent;
        button.disabled = false;
    }
}

// ============================================
// Form Field Utilities
// ============================================

/**
 * Toggle conditional form fields based on select value
 * @param {string} triggerSelectId - ID of the select that triggers the toggle
 * @param {string} targetContainerId - ID of the container to show/hide
 * @param {string} targetInputId - ID of the input to set required
 * @param {string} triggerValue - Value that should show the target
 * @param {boolean} showOnMatch - Whether to show when value matches (default: true)
 */
function toggleConditionalField(triggerSelectId, targetContainerId, targetInputId, triggerValue, showOnMatch = true) {
    const triggerSelect = document.getElementById(triggerSelectId);
    const targetContainer = document.getElementById(targetContainerId);
    const targetInput = document.getElementById(targetInputId);

    if (!triggerSelect || !targetContainer) return;

    function updateVisibility() {
        const shouldShow = triggerSelect.value === triggerValue;
        const display = showOnMatch ? shouldShow : !shouldShow;

        targetContainer.classList.toggle('hidden', !display);

        if (targetInput) {
            if (display) {
                targetInput.setAttribute('required', 'required');
            } else {
                targetInput.removeAttribute('required');
            }
        }
    }

    triggerSelect.addEventListener('change', updateVisibility);
    updateVisibility(); // Initial check
}

/**
 * Toggle multiple conditional fields based on select value
 * @param {string} triggerSelectId - ID of the select that triggers the toggle
 * @param {Array<{containerId: string, inputId: string}>} targets - Array of target configurations
 * @param {string} triggerValue - Value that should show the targets
 * @param {boolean} showOnMatch - Whether to show when value matches (default: true)
 */
function toggleMultipleConditionalFields(triggerSelectId, targets, triggerValue, showOnMatch = true) {
    const triggerSelect = document.getElementById(triggerSelectId);

    if (!triggerSelect) return;

    function updateVisibility() {
        const shouldShow = triggerSelect.value === triggerValue;
        const display = showOnMatch ? shouldShow : !shouldShow;

        targets.forEach(({ containerId, inputId }) => {
            const targetContainer = document.getElementById(containerId);
            const targetInput = inputId ? document.getElementById(inputId) : null;

            if (targetContainer) {
                targetContainer.classList.toggle('hidden', !display);

                if (targetInput) {
                    if (display) {
                        targetInput.setAttribute('required', 'required');
                    } else {
                        targetInput.removeAttribute('required');
                    }
                }
            }
        });
    }

    triggerSelect.addEventListener('change', updateVisibility);
    updateVisibility(); // Initial check
}

// ============================================
// Date/Time Utilities
// ============================================

/**
 * Format date to datetime-local input format (YYYY-MM-DDTHH:MM)
 * @param {Date} date - The date to format
 * @returns {string} - Formatted date string
 */
function formatDateTimeLocal(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
}

/**
 * Set datetime-local input to current date/time
 * @param {string} inputId - ID of the datetime-local input
 */
function setDateTimeToNow(inputId) {
    const dateInput = document.getElementById(inputId);
    if (dateInput) {
        const now = new Date();
        dateInput.value = formatDateTimeLocal(now);
    }
}

// ============================================
// Select Box Utilities
// ============================================

/**
 * Update select options dynamically
 * @param {string} selectId - ID of the select element
 * @param {Array} items - Array of items to populate the select
 * @param {string} valueKey - Key to use for option value
 * @param {string} textKey - Key to use for option text
 * @param {string} defaultText - Default option text
 */
function updateSelectOptions(selectId, items, valueKey, textKey, defaultText = 'Select an option') {
    const select = document.getElementById(selectId);
    if (!select) return;

    select.innerHTML = `<option value="" disabled selected>${defaultText}</option>`;
    items.forEach(item => {
        const option = document.createElement('option');
        option.value = item[valueKey];
        option.textContent = item[textKey];
        option.selected = true;
        select.appendChild(option);
    });
}

// ============================================
// Dynamic Form Fields
// ============================================

/**
 * Add a new dynamic input field to a container
 * @param {string} containerId - ID of the container
 * @param {string} name - Name attribute for the input
 * @param {string} placeholder - Placeholder text
 * @param {string} type - Input type (default: text)
 */
function addDynamicInput(containerId, name, placeholder, type = 'text') {
    const container = document.getElementById(containerId);
    if (!container) return;

    const div = document.createElement('div');
    div.className = 'flex items-center gap-2';

    const input = document.createElement('input');
    input.type = type;
    input.name = name;
    input.placeholder = placeholder;
    input.required = true;
    input.className = 'w-full rounded-lg border border-edge bg-surface px-3.5 py-2.5 text-sm text-ink placeholder:text-ink-3 transition-colors focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent';

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'inline-flex shrink-0 items-center rounded-lg border border-danger px-3 py-2.5 text-sm font-medium text-danger transition-colors hover:bg-danger hover:text-white';
    removeBtn.textContent = 'Delete';
    removeBtn.addEventListener('click', function () {
        div.remove();
    });

    div.appendChild(input);
    div.appendChild(removeBtn);
    container.appendChild(div);
}

/**
 * Clear dynamic fields except the first one
 * @param {string} containerId - ID of the container
 */
function clearDynamicFields(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    while (container.children.length > 1) {
        container.removeChild(container.lastChild);
    }
}

// ============================================
// Bullet Point Utilities
// ============================================

/**
 * Parse bullet points from text
 * @param {string} text - Text containing bullet points
 * @returns {Array<string>} - Array of bullet point text (without bullets)
 */
function parseBulletPoints(text) {
    return text
        .split('\n')
        .filter(line => line.trim())
        .map(line => line.replace(/^[•\-\*]\s*/, '')); // Remove bullet characters
}

/**
 * Populate dynamic fields from bullet points
 * @param {string} containerId - ID of the container
 * @param {Array<string>} items - Array of items to populate
 * @param {string} name - Name attribute for inputs
 */
function populateFieldsFromBulletPoints(containerId, items, name) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Clear existing fields except the first one
    clearDynamicFields(containerId);

    // Set first item in existing input
    const firstInput = container.querySelector('input');
    if (firstInput && items.length > 0) {
        firstInput.value = items[0];
    }

    // Add additional items
    for (let i = 1; i < items.length; i++) {
        const div = document.createElement('div');
        div.className = 'flex items-center gap-2';

        const input = document.createElement('input');
        input.type = 'text';
        input.name = name;
        input.value = items[i];
        input.required = true;
        input.className = 'w-full rounded-lg border border-edge bg-surface px-3.5 py-2.5 text-sm text-ink placeholder:text-ink-3 transition-colors focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent';

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'inline-flex shrink-0 items-center rounded-lg border border-danger px-3 py-2.5 text-sm font-medium text-danger transition-colors hover:bg-danger hover:text-white';
        removeBtn.textContent = 'Delete';
        removeBtn.addEventListener('click', function () {
            div.remove();
        });

        div.appendChild(input);
        div.appendChild(removeBtn);
        container.appendChild(div);
    }
}