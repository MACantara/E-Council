document.getElementById('users-signature').addEventListener('change', function () {
    const fileName = this.files[0] ? this.files[0].name : 'No file chosen';
    document.getElementById('file-name').textContent = fileName;
});

document.addEventListener('DOMContentLoaded', function () {
    const roleSelect = document.getElementById('users-role');
    const studentOrgContainer = document.getElementById('users-student-organization-container');
    const studentOrgSelect = document.getElementById('users-student-organization');
    const studentOrgPositionContainer = document.getElementById('users-student-organization-position-container');
    const studentOrgPositionSelect = document.getElementById('users-student-organization-position');

    function toggleStudentOrganizationFields() {
        if (roleSelect.value === 'Student Council Officer') {
            studentOrgContainer.style.display = 'flex';
            studentOrgSelect.setAttribute('required', 'required');
            studentOrgPositionContainer.style.display = 'flex';
            studentOrgPositionSelect.setAttribute('required', 'required');
        } else {
            studentOrgContainer.style.display = 'none';
            studentOrgSelect.removeAttribute('required');
            studentOrgPositionContainer.style.display = 'none';
            studentOrgPositionSelect.removeAttribute('required');
        }
    }

    roleSelect.addEventListener('change', toggleStudentOrganizationFields);

    // Initial check
    toggleStudentOrganizationFields();
});

function previewImage() {
    const fileInput = document.getElementById('users-signature');
    const fileName = document.getElementById('file-name');
    const file = fileInput.files[0];
    const preview = document.getElementById('signature-preview');
    const validImageTypes = ['image/jpeg', 'image/png', 'image/jpg'];

    if (file) {
        if (validImageTypes.includes(file.type)) {
            fileName.textContent = file.name;
            const reader = new FileReader();
            reader.onload = function (e) {
                preview.src = e.target.result;
            }
            reader.readAsDataURL(file);
        } else {
            fileName.textContent = 'No file chosen';
            fileInput.value = ''; // Clear the input
            preview.src = ''; // Clear the preview
        }
    }
}

// Delete User Account Modal
document.getElementById('open-delete-user-account-modal-button').addEventListener('click', function () {
    document.getElementById('delete-user-account-modal-content').style.display = 'block';
});

document.getElementById('close-delete-user-account-modal-button').addEventListener('click', function () {
    document.getElementById('delete-user-account-modal-content').style.display = 'none';
});

document.getElementById('cancel-delete-user-account-modal-button').addEventListener('click', function () {
    document.getElementById('delete-user-account-modal-content').style.display = 'none';
});

window.addEventListener('click', function (event) {
    if (event.target == document.getElementById('delete-user-account-modal-content')) {
        document.getElementById('delete-user-account-modal-content').style.display = 'none';
    }
});