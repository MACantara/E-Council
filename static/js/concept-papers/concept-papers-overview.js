/**
 * Concept Papers Overview Page JavaScript
 * Handles concept paper status updates
 */

document.addEventListener('DOMContentLoaded', function () {
    initializeConceptPaperStatusUpdates();
});

function initializeConceptPaperStatusUpdates() {
    const selects = document.querySelectorAll('select[name="concept-paper-status-select-button"]');
    selects.forEach(select => {
        select.addEventListener('change', function () {
            const paperId = this.getAttribute('data-paper-id');
            const newStatus = this.value;
            const paperName = this.getAttribute('data-paper-name');

            fetch(`/concept-papers/update-status/${paperId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ status: newStatus, name: paperName })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(`Concept paper status for "${paperName}" updated successfully.`);
                    } else {
                        alert(`Failed to update concept paper status for "${paperName}".`);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert(`An error occurred while updating the concept paper status for "${paperName}".`);
                });
        });
    });
}
