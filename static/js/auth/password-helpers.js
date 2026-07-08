// Shared password utilities for sign-up and password reset pages

function togglePasswordVisibility(id) {
    const input = document.getElementById(id);
    if (input) {
        input.type = input.type === 'password' ? 'text' : 'password';
    }
}

let iconRefreshPending = false;
function refreshIconsSoon() {
    if (iconRefreshPending) return;
    iconRefreshPending = true;
    setTimeout(function () {
        if (window.lucide) lucide.createIcons();
        iconRefreshPending = false;
    }, 0);
}

function setRequirementIcon(iconId, valid) {
    const el = document.getElementById(iconId);
    if (!el) return;
    const name = valid ? 'check-circle-2' : 'x';
    const colorClass = valid ? 'text-success' : 'text-danger';
    el.innerHTML = '<i data-lucide="' + name + '" width="16" height="16" class="w-4 h-4 ' + colorClass + '"></i>';
    refreshIconsSoon();
}

function initializePasswordValidation(formId) {
    const iconIds = {
        length: 'length-icon',
        uppercase: 'uppercase-icon',
        lowercase: 'lowercase-icon',
        number: 'number-icon',
        special: 'special-icon'
    };

    Object.values(iconIds).forEach(function (id) {
        setRequirementIcon(id, false);
    });

    const passwordInput = document.getElementById('users-password');
    if (passwordInput) {
        passwordInput.addEventListener('input', function () {
            const password = this.value;
            const strengthBarContainer = document.getElementById('password-strength');
            const strengthBar = document.getElementById('password-strength-bar');
            const strengthText = document.getElementById('password-strength-text');
            const strengthColors = ['#ff4b4b', '#ff7f50', '#ffd700', '#9acd32', '#00c853'];
            const strengthDescriptions = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];

            const lengthValid = password.length >= 8;
            const uppercaseValid = /[A-Z]/.test(password);
            const lowercaseValid = /[a-z]/.test(password);
            const numberValid = /[0-9]/.test(password);
            const specialValid = /[!@#$%^&*(),.?":{}|<>]/.test(password);

            setRequirementIcon(iconIds.length, lengthValid);
            setRequirementIcon(iconIds.uppercase, uppercaseValid);
            setRequirementIcon(iconIds.lowercase, lowercaseValid);
            setRequirementIcon(iconIds.number, numberValid);
            setRequirementIcon(iconIds.special, specialValid);

            if (password === '') {
                if (strengthBarContainer) strengthBarContainer.classList.add('hidden');
                if (strengthBar) strengthBar.style.width = '0%';
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
            if (passwordMatch) {
                if (repeatPassword === '') {
                    passwordMatch.classList.add('hidden');
                } else if (password !== repeatPassword) {
                    passwordMatch.classList.remove('hidden');
                    passwordMatch.className = 'mt-1 text-sm text-danger';
                    passwordMatch.textContent = 'Passwords do not match';
                } else {
                    passwordMatch.classList.remove('hidden');
                    passwordMatch.className = 'mt-1 text-sm text-success';
                    passwordMatch.textContent = 'Passwords match';
                }
            }
        });
    }

    if (formId) {
        const form = document.getElementById(formId);
        if (form) {
            form.addEventListener('submit', function (event) {
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
}
