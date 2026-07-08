// Password and Security Settings JavaScript
// Uses utilities from utils.js

document.addEventListener('DOMContentLoaded', function () {
    // Initialize password toggle buttons
    const togglePasswordButtons = document.querySelectorAll('.show-password-button');
    togglePasswordButtons.forEach(button => {
        button.addEventListener('click', function () {
            const inputId = this.getAttribute('data-target');
            togglePasswordVisibility(inputId, this);
        });
    });

    // Initialize password validation
    initializePasswordValidation();
});

function togglePasswordVisibility(id, button) {
    const input = document.getElementById(id);
    if (input) {
        if (input.type === 'password') {
            input.type = 'text';
            button.setAttribute('aria-pressed', 'true');
        } else {
            input.type = 'password';
            button.setAttribute('aria-pressed', 'false');
        }
    }
}

function setRequirementState(id, valid) {
    const xIcon = document.getElementById(id + '-icon-x');
    const checkIcon = document.getElementById(id + '-icon-check');
    const requirement = document.getElementById(id);
    if (!xIcon || !checkIcon || !requirement) return;

    if (valid) {
        xIcon.classList.add('hidden');
        checkIcon.classList.remove('hidden');
        requirement.classList.remove('text-ink-2');
        requirement.classList.add('text-success');
    } else {
        xIcon.classList.remove('hidden');
        checkIcon.classList.add('hidden');
        requirement.classList.remove('text-success');
        requirement.classList.add('text-ink-2');
    }
}

function initializePasswordValidation() {
    const passwordInput = document.getElementById('users-password');
    const strengthBarContainer = document.getElementById('password-strength');
    const strengthBar = document.getElementById('password-strength-bar');
    const strengthText = document.getElementById('password-strength-text');
    const strengthColors = ['#ff4b4b', '#ff7f50', '#ffd700', '#9acd32', '#00c853'];
    const strengthDescriptions = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];

    if (passwordInput) {
        passwordInput.addEventListener('input', function () {
            const password = this.value;

            const lengthValid = password.length >= 8;
            const uppercaseValid = /[A-Z]/.test(password);
            const lowercaseValid = /[a-z]/.test(password);
            const numberValid = /[0-9]/.test(password);
            const specialValid = /[!@#$%^&*(),.?":{}|<>]/.test(password);

            setRequirementState('length-requirement', lengthValid);
            setRequirementState('uppercase-requirement', uppercaseValid);
            setRequirementState('lowercase-requirement', lowercaseValid);
            setRequirementState('number-requirement', numberValid);
            setRequirementState('special-requirement', specialValid);

            if (password === '') {
                if (strengthBarContainer) strengthBarContainer.classList.add('hidden');
                if (strengthBar) {
                    strengthBar.style.width = '0%';
                    strengthBar.style.backgroundColor = '#e0e0e0';
                }
                if (strengthText) strengthText.textContent = '';
            } else {
                const result = zxcvbn(password);
                if (strengthBarContainer) strengthBarContainer.classList.remove('hidden');
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
                    passwordMatch.classList.remove('hidden');
                    passwordMatch.classList.remove('text-ink-2');
                    passwordMatch.classList.add('text-danger');
                    passwordMatch.textContent = 'Passwords do not match';
                }
            } else {
                if (passwordMatch) passwordMatch.classList.add('hidden');
            }
        });
    }

    const passwordSecurityForm = document.getElementById('password-security-form');
    if (passwordSecurityForm) {
        passwordSecurityForm.addEventListener('submit', function (event) {
            const password = document.getElementById('users-password').value;
            const repeatPassword = document.getElementById('users-repeat-password').value;

            const lengthValid = password.length >= 8;
            const uppercaseValid = /[A-Z]/.test(password);
            const lowercaseValid = /[a-z]/.test(password);
            const numberValid = /[0-9]/.test(password);
            const specialValid = /[!@#$%^&*(),.?":{}|<>]/.test(password);

            if (!lengthValid || !uppercaseValid || !lowercaseValid || !numberValid || !specialValid || password !== repeatPassword) {
                event.preventDefault();
                alert('Please ensure the password meets all requirements and both passwords match.');
            }
        });
    }
}
