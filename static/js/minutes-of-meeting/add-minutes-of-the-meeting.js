/**
 * Add Minutes of the Meeting Page JavaScript
 * Handles academic year toggle, file name display, and signatory field toggling
 */

document.addEventListener('DOMContentLoaded', function () {
    initializeAddMinutesOfMeetingForm();
});

function initializeAddMinutesOfMeetingForm() {
    // Academic year toggle
    const academicYearSelect = document.getElementById('minutes-of-the-meeting-academic-year');
    const otherAcademicYearContainer = document.getElementById('other-academic-year-container');

    if (academicYearSelect) {
        academicYearSelect.addEventListener('change', function () {
            if (academicYearSelect.value === 'Other') {
                otherAcademicYearContainer.classList.remove('hidden');
            } else {
                otherAcademicYearContainer.classList.add('hidden');
            }
        });
    }

    // File name display for meeting recording
    const meetingRecording = document.getElementById('meeting-recording');
    if (meetingRecording) {
        meetingRecording.addEventListener('change', function () {
            const fileNames = Array.from(this.files).map(file => file.name).join(', ') || 'No files chosen';
            const fileNameElement = document.getElementById('meeting-recording-file-name');
            if (fileNameElement) {
                fileNameElement.textContent = fileNames;
            }
        });
    }

    // File name display for photo documentation
    const photoDocumentation = document.getElementById('photo-documentation');
    if (photoDocumentation) {
        photoDocumentation.addEventListener('change', function () {
            const fileNames = Array.from(this.files).map(file => file.name).join(', ') || 'No files chosen';
            const fileNameElement = document.getElementById('photo-documentation-file-name');
            if (fileNameElement) {
                fileNameElement.textContent = fileNames;
            }
        });
    }

    // Toggle for new signatory fields
    const notedBySelect = document.getElementById('minutes-of-the-meeting-noted-by');
    if (notedBySelect) {
        notedBySelect.addEventListener('change', function () {
            toggleNewSignatoryFields(notedBySelect, 'noted-by');
        });
    }
}

function toggleNewSignatoryFields(selectElement, prefix) {
    const fields = [
        'title', 'first-name', 'middle-name', 'last-name', 'suffix', 'position', 'department'
    ];
    fields.forEach(field => {
        const fieldElement = document.getElementById(`new-${prefix}-${field}`);
        if (fieldElement) {
            const wrapper = fieldElement.closest('.new-signatory-field');
            if (wrapper) {
                wrapper.classList.toggle('hidden', selectElement.value !== `add-new-${prefix}`);
            }
        }
    });
}
