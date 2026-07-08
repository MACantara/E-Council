// Account JavaScript - Profile Picture Modal Handling
// Uses utilities from utils.js

document.addEventListener('DOMContentLoaded', function () {
    // Initialize profile picture upload modal
    initializeModal(
        'open-upload-change-account-profile-picture-modal-button',
        'close-upload-change-account-profile-picture-modal-button',
        'cancel-upload-profile-picture',
        'upload-change-account-profile-picture-modal-content'
    );

    // Set up file name display
    setupFileNameDisplay('profile-picture', 'file-name');
});