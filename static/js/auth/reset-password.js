// Reset Password JavaScript
// Uses utilities from utils.js

document.addEventListener('DOMContentLoaded', function () {
    // Initialize password toggle buttons
    const togglePasswordButtons = document.querySelectorAll('.show-password-button');
    togglePasswordButtons.forEach(button => {
        button.addEventListener('click', function () {
            const inputId = this.getAttribute('data-target');
            togglePasswordVisibility(inputId);
        });
    });

    // Initialize password validation
    initializePasswordValidation();
});

function togglePasswordVisibility(id) {
    const input = document.getElementById(id);
    if (input) {
        if (input.type === 'password') {
            input.type = 'text';
        } else {
            input.type = 'password';
        }
    }
}

function initializePasswordValidation() {
    // Password requirement icons
    const lengthIcon = document.getElementById('length-icon');
    const uppercaseIcon = document.getElementById('uppercase-icon');
    const lowercaseIcon = document.getElementById('lowercase-icon');
    const numberIcon = document.getElementById('number-icon');
    const specialIcon = document.getElementById('special-icon');

    // Initial color of password requirement icons
    if (lengthIcon) lengthIcon.style.color = 'red';
    if (uppercaseIcon) uppercaseIcon.style.color = 'red';
    if (lowercaseIcon) lowercaseIcon.style.color = 'red';
    if (numberIcon) numberIcon.style.color = 'red';
    if (specialIcon) specialIcon.style.color = 'red';

    const passwordInput = document.getElementById('users-password');
    if (passwordInput) {
        passwordInput.addEventListener('input', function () {
            const password = this.value;
            const strengthBarContainer = document.getElementById('password-strength');
            const strengthBar = document.getElementById('password-strength-bar');
            const strengthText = document.getElementById('password-strength-text');
            const strengthColors = ['#ff4b4b', '#ff7f50', '#ffd700', '#9acd32', '#00c853'];
            const strengthDescriptions = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];

            // Check password requirements
            const lengthValid = password.length >= 8;
            const uppercaseValid = /[A-Z]/.test(password);
            const lowercaseValid = /[a-z]/.test(password);
            const numberValid = /[0-9]/.test(password);
            const specialValid = /[!@#$%^&*(),.?":{}|<>]/.test(password);

            // Update requirement compliance
            if (lengthIcon) {
                lengthIcon.style.color = lengthValid ? 'green' : 'red';
                lengthIcon.className = lengthValid ? 'bi bi-check-circle' : 'bi bi-x-circle';
            }

            if (uppercaseIcon) {
                uppercaseIcon.style.color = uppercaseValid ? 'green' : 'red';
                uppercaseIcon.className = uppercaseValid ? 'bi bi-check-circle' : 'bi bi-x-circle';
            }

            if (lowercaseIcon) {
                lowercaseIcon.style.color = lowercaseValid ? 'green' : 'red';
                lowercaseIcon.className = lowercaseValid ? 'bi bi-check-circle' : 'bi bi-x-circle';
            }

            if (numberIcon) {
                numberIcon.style.color = numberValid ? 'green' : 'red';
                numberIcon.className = numberValid ? 'bi bi-check-circle' : 'bi bi-x-circle';
            }

            if (specialIcon) {
                specialIcon.style.color = specialValid ? 'green' : 'red';
                specialIcon.className = specialValid ? 'bi bi-check-circle' : 'bi bi-x-circle';
            }

            if (password === '') {
                if (strengthBarContainer) strengthBarContainer.style.display = 'none';
                if (strengthBar) {
                    strengthBar.style.width = '0%';
                    strengthBar.style.backgroundColor = '#e0e0e0';
                }
                if (strengthText) strengthText.textContent = '';
            } else {
                const result = zxcvbn(password);
                if (strengthBarContainer) strengthBarContainer.style.display = 'block';
                if (strengthBar) {
                    strengthBar.style.width = (result.score + 1) * 20 + '%';
                    strengthBar.style.backgroundColor = strengthColors[result.score];
                }
                if (strengthText) strengthText.textContent = 'Password Strength: ' + strengthDescriptions[result.score];
            }
        });
    }

    const repeatPasswordInput = document.getElementById('users-repeat-password');
    if (repeatPasswordInput) {
        repeatPasswordInput.addEventListener('input', function () {
            const password = document.getElementById('users-password').value;
            const repeatPassword = this.value;
            const passwordMatch = document.getElementById('password-match');
            if (password !== repeatPassword) {
                if (passwordMatch) {
                    passwordMatch.style.display = 'block';
                    passwordMatch.style.color = 'red';
                    passwordMatch.textContent = 'Passwords do not match';
                }
            } else {
                if (passwordMatch) passwordMatch.style.display = 'none';
            }
        });
    }

    const passwordResetForm = document.getElementById('password-reset-form');
    if (passwordResetForm) {
        passwordResetForm.addEventListener('submit', function (event) {
            const password = document.getElementById('users-password').value;
            const repeatPassword = document.getElementById('users-repeat-password').value;

            // Check password requirements
            const lengthValid = password.length >= 8;
            const uppercaseValid = /[A-Z]/.test(password);
            const lowercaseValid = /[a-z]/.test(password);
            const numberValid = /[0-9]/.test(password);
            const specialValid = /[!@#$%^&*(),.?":{}|<>]/.test(password);

            // Prevent form submission if requirements are not met
            if (!lengthValid || !uppercaseValid || !lowercaseValid || !numberValid || !specialValid || password !== repeatPassword) {
                event.preventDefault();
                alert('Please ensure the password meets all requirements and both passwords match.');
            }
        });
    }
}
