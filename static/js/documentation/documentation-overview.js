/**
 * Documentation Overview Page JavaScript
 * Handles documentation status updates
 */

document.addEventListener('DOMContentLoaded', function () {
    initializeDocumentationStatusUpdates();
});

function initializeDocumentationStatusUpdates() {
    const selects = document.querySelectorAll('select[name="documentation-status-select-button"]');
    selects.forEach(select => {
        select.addEventListener('change', function () {
            const documentationId = this.getAttribute('data-documentation-id');
            const newStatus = this.value;
            const documentationName = this.getAttribute('data-documentation-name');

            fetch(`/update-documentation-status/${documentationId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ status: newStatus, name: documentationName })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(`Documentation status for "${documentationName}" updated successfully.`);
                    } else {
                        alert(`Failed to update documentation status for "${documentationName}".`);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert(`An error occurred while updating the documentation status for "${documentationName}".`);
                });
        });
    });
}
