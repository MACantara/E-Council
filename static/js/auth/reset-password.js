// Reset Password JavaScript
// Uses utilities from utils.js

document.addEventListener('DOMContentLoaded', function () {
    // Initialize password toggle buttons
    document.querySelectorAll('.show-password-button').forEach(function (button) {
        button.addEventListener('click', function () {
            togglePasswordVisibility(this.getAttribute('data-target'));
        });
    });

    initializePasswordValidation('password-reset-form');
});
