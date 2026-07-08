function toggleOtherAcademicYear() {
    const academicYearSelect = document.getElementById('board-resolutions-academic-year');
    const otherAcademicYearInput = document.getElementById('other-academic-year-input');
    const otherAcademicYearLabel = document.getElementById('other-academic-year-label');
    if (academicYearSelect.value === 'Other') {
        otherAcademicYearInput.style.display = 'block';
        otherAcademicYearInput.required = true;
        otherAcademicYearLabel.style.display = 'block';
        otherAcademicYearLabel.required = true;
    } else {
        otherAcademicYearInput.style.display = 'none';
        otherAcademicYearInput.required = false;
        otherAcademicYearLabel.style.display = 'none';
        otherAcademicYearLabel.required = false;
    }
}

function updateTitle() {
    const eventSelect = document.getElementById('board-resolutions-events-id');
    const selectedOption = eventSelect.options[eventSelect.selectedIndex];
    const eventName = selectedOption.getAttribute('data-event-name');
    const titleInput = document.getElementById('board-resolutions-title');
    const otherEventNameInput = document.getElementById('other-event-name-input');
    if (eventSelect.value === 'Other') {
        otherEventNameInput.style.display = 'block';
        otherEventNameInput.required = true;
        titleInput.value = `${otherEventNameInput.value} Board Resolution`;
    } else {
        otherEventNameInput.style.display = 'none';
        otherEventNameInput.required = false;
        if (eventName) {
            titleInput.value = `${eventName} Board Resolution`;
        } else {
            titleInput.value = '';
        }
    }
}

// Set the current date and time as the default value for the datetime-local input
document.addEventListener('DOMContentLoaded', function () {
    const dateInput = document.getElementById('board-resolutions-date');
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const formattedDate = `${year}-${month}-${day}T${hours}:${minutes}`;
    dateInput.value = formattedDate;
});

function generateDescription() {
    const eventSelect = document.getElementById('board-resolutions-events-id');
    const eventName = eventSelect.value === 'Other'
        ? document.getElementById('other-event-name-input').value
        : eventSelect.options[eventSelect.selectedIndex].text;
    const title = document.getElementById('board-resolutions-title').value;
    const date = document.getElementById('board-resolutions-date').value;
    const totalAmount = document.getElementById('board-resolutions-total-amount').value;

    if (!eventName || !title) {
        alert('Please select an event and provide a title first');
        return;
    }

    const generateButton = document.querySelector('[onclick="generateDescription()"]');
    const originalText = generateButton.textContent;
    generateButton.textContent = 'Generating...';
    generateButton.disabled = true;

    fetch('/board-resolutions/generate-description', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
        },
        body: JSON.stringify({
            event_name: eventName,
            title: title,
            date: date,
            total_amount: totalAmount
        }),
        credentials: 'same-origin'
    })
    .then(response => {
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return response.json();
        } else {
            throw new Error('Server returned non-JSON response');
        }
    })
    .then(data => {
        if (!data.description) {
            throw new Error('No description generated');
        }
        document.getElementById('board-resolutions-description').value = data.description;
    })
    .catch(error => {
        console.error('Error:', error);
        alert(`Error: ${error.message || 'Failed to generate description. Please try again.'}`);
    })
    .finally(() => {
        generateButton.textContent = originalText;
        generateButton.disabled = false;
    });
}