/**
 * Financial Reports Overview Page JavaScript
 * Handles financial report status updates
 */

document.addEventListener('DOMContentLoaded', function () {
    initializeFinancialReportStatusUpdates();
});

function initializeFinancialReportStatusUpdates() {
    const selects = document.querySelectorAll('select[name="meeting-status-select-button"]');
    selects.forEach(select => {
        select.addEventListener('change', function () {
            const meetingId = this.getAttribute('data-meeting-id');
            const newStatus = this.value;
            const meetingName = this.getAttribute('data-meeting-name');

            fetch(`/update-financial-report-status/${meetingId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ status: newStatus, name: meetingName })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(`Meeting status for "${meetingName}" updated successfully.`);
                    } else {
                        alert(`Failed to update meeting status for "${meetingName}".`);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert(`An error occurred while updating the meeting status for "${meetingName}".`);
                });
        });
    });
}
