// Account Settings JavaScript
// Uses utilities from utils.js

document.addEventListener('DOMContentLoaded', function () {
    // Initialize delete user account modal
    initializeModal(
        'open-delete-user-account-modal-button',
        'close-delete-user-account-modal-button',
        'cancel-delete-user-account-button',
        'delete-user-account-modal-content'
    );

    // Initialize student organization field toggling
    toggleMultipleConditionalFields(
        'users-role',
        [
            { containerId: 'users-student-organization-container', inputId: 'users-student-organization' },
            { containerId: 'users-student-organization-position-container', inputId: 'users-student-organization-position' }
        ],
        'Student Council Officer'
    );

    // Set up file name display for signature upload
    setupFileNameDisplay('users-signature', 'file-name');
});