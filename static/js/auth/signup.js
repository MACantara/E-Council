// Sign Up JavaScript
// Uses utilities from utils.js

document.addEventListener('DOMContentLoaded', function () {
    // Initialize password toggle buttons
    document.querySelectorAll('.show-password-button').forEach(function (button) {
        button.addEventListener('click', function () {
            togglePasswordVisibility(this.getAttribute('data-target'));
        });
    });

    // Initialize role-based field toggling
    const roleSelect = document.getElementById('users-role');
    if (roleSelect) {
        roleSelect.addEventListener('change', toggleStudentOrganizationFields);
        toggleStudentOrganizationFields();
    }

    initializePasswordValidation('signup-form');
});

function toggleStudentOrganizationFields() {
    const roleSelect = document.getElementById('users-role');
    const studentOrgContainer = document.getElementById('users-student-organization-container');
    const studentOrgSelect = document.getElementById('users-student-organization');
    const studentOrgPositionContainer = document.getElementById('users-student-organization-position-container');
    const studentOrgPositionSelect = document.getElementById('users-student-organization-position');

    if (roleSelect && studentOrgContainer && studentOrgSelect && studentOrgPositionContainer && studentOrgPositionSelect) {
        if (roleSelect.value === 'Student Council Officer') {
            studentOrgContainer.classList.remove('hidden');
            studentOrgSelect.setAttribute('required', 'required');
            studentOrgPositionContainer.classList.remove('hidden');
            studentOrgPositionSelect.setAttribute('required', 'required');
        } else {
            studentOrgContainer.classList.add('hidden');
            studentOrgSelect.removeAttribute('required');
            studentOrgPositionContainer.classList.add('hidden');
            studentOrgPositionSelect.removeAttribute('required');
        }
    }
}
