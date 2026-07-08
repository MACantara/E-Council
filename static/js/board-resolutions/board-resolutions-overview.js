/**
 * Board Resolutions Overview Page JavaScript
 * Handles board resolution status updates
 */

document.addEventListener('DOMContentLoaded', function () {
    initializeBoardResolutionStatusUpdates();
});

function initializeBoardResolutionStatusUpdates() {
    const selects = document.querySelectorAll('select[name="resolution-status-select-button"]');
    selects.forEach(select => {
        select.addEventListener('change', function () {
            const resolutionId = this.getAttribute('data-resolution-id');
            const newStatus = this.value;
            const resolutionName = this.getAttribute('data-resolution-name');

            fetch(`/board-resolutions/update-board-resolution-status/${resolutionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ status: newStatus, name: resolutionName })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(`Resolution status for "${resolutionName}" updated successfully.`);
                    } else {
                        alert(`Failed to update resolution status for "${resolutionName}".`);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert(`An error occurred while updating the resolution status for "${resolutionName}".`);
                });
        });
    });
}
