document.getElementById('profile-picture').addEventListener('change', function () {
    const fileName = this.files[0] ? this.files[0].name : 'No file chosen';
    document.getElementById('file-name').textContent = fileName;
});

// Upload/Change Account Profile Picture Modal
document.getElementById('open-upload-change-account-profile-picture-modal-button').addEventListener('click', function () {
    document.getElementById('upload-change-account-profile-picture-modal-content').style.display = 'block';
});

document.getElementById('close-upload-change-account-profile-picture-modal-button').addEventListener('click', function () {
    document.getElementById('upload-change-account-profile-picture-modal-content').style.display = 'none';
});

document.getElementById('cancel-upload-profile-picture').addEventListener('click', function () {
    document.getElementById('upload-change-account-profile-picture-modal-content').style.display = 'none';
});

window.addEventListener('click', function (event) {
    if (event.target == document.getElementById('upload-change-account-profile-picture-modal-content')) {
        document.getElementById('upload-change-account-profile-picture-modal-content').style.display = 'none';
    }
});