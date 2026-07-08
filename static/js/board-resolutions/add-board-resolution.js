// Board Resolutions JavaScript
// Uses utilities from utils.js

document.addEventListener('DOMContentLoaded', function () {
    // Initialize conditional field toggling
    toggleConditionalField(
        'board-resolutions-academic-year',
        'other-academic-year-input',
        'other-academic-year-input',
        'Other'
    );

    toggleConditionalField(
        'board-resolutions-events-id',
        'other-event-name-input',
        'other-event-name-input',
        'Other'
    );

    // Set date to current time
    setDateTimeToNow('board-resolutions-date');
});

function updateTitle() {
    const eventSelect = document.getElementById('board-resolutions-events-id');
    const selectedOption = eventSelect.options[eventSelect.selectedIndex];
    const eventName = selectedOption.getAttribute('data-event-name');
    const titleInput = document.getElementById('board-resolutions-title');
    const otherEventNameInput = document.getElementById('other-event-name-input');
    
    if (eventSelect.value === 'Other') {
        titleInput.value = `${otherEventNameInput.value} Board Resolution`;
    } else {
        if (eventName) {
            titleInput.value = `${eventName} Board Resolution`;
        } else {
            titleInput.value = '';
        }
    }
}

async function generateDescription() {
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
    setButtonLoading(generateButton, 'Generating...');

    try {
        await generateContent('/board-resolutions/generate-description', {
            event_name: eventName,
            title: title,
            date: date,
            total_amount: totalAmount
        }, 'board-resolutions-description');
    } catch (error) {
        console.error('Error:', error);
        alert(`Error: ${error.message || 'Failed to generate description. Please try again.'}`);
    } finally {
        setButtonLoading(generateButton, 'Generating...', false);
    }
}