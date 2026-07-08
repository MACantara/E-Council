// Set the current date and time as the default value for the datetime-local input
document.addEventListener('DOMContentLoaded', function () {
    setDateTimeToNow('concept-paper-date-of-submission');
    
    // Initialize conditional field toggles
    toggleMultipleConditionalFields('concept-paper-academic-year', [
        { containerId: 'other-academic-year-input', inputId: 'other-academic-year-input' },
        { containerId: 'other-academic-year-label', inputId: 'other-academic-year-label' }
    ], 'Other');
});

async function generateBody() {
    const subject = document.getElementById('concept-paper-subject').value;
    const startDate = document.getElementById('concept-paper-event-start-date-and-time').value;
    const endDate = document.getElementById('concept-paper-event-end-date-and-time').value;
    const location = document.getElementById('concept-paper-location').value;

    await generateContent('/generate-concept-body', {
        subject,
        start_date: startDate,
        end_date: endDate,
        location
    }, 'concept-paper-body');
}

async function generateDescriptions() {
    const subject = document.getElementById('concept-paper-subject').value;
    await generateContent('/generate-concept-descriptions', {
        subject
    }, 'concept-paper-descriptions');
}

function addObjective() {
    const container = document.getElementById('concept-paper-objectives');
    const div = document.createElement('div');
    div.className = 'input-group';
    div.innerHTML = `
    <input type="text" name="concept-paper-objectives" placeholder="Enter Objective" required>
    <button type="button" class="delete-btn" onclick="this.parentElement.remove()">Delete</button>
`;
    container.appendChild(div);
}

async function generateObjectives() {
    const subject = document.getElementById('concept-paper-subject').value;
    const generateButton = event.target;
    
    setButtonLoading(generateButton, 'Generating...', true);

    try {
        const response = await authenticatedFetch('/generate-concept-objectives', { subject });
        const responseData = await handleAPIResponse(response);
        
        if (responseData.content) {
            const objectives = parseBulletPoints(responseData.content);
            populateFieldsFromBulletPoints('concept-paper-objectives', objectives, 'concept-paper-objectives');
        }
    } catch (error) {
        console.error('Error:', error);
        alert(`Error: ${error.message || 'Failed to generate objectives. Please try again.'}`);
    } finally {
        setButtonLoading(generateButton, '', false);
    }
}

async function generateLearningOutcomes() {
    const subject = document.getElementById('concept-paper-subject').value;
    const generateButton = event.target;
    
    setButtonLoading(generateButton, 'Generating...', true);

    try {
        const response = await authenticatedFetch('/generate-concept-learning-outcomes', { subject });
        const responseData = await handleAPIResponse(response);
        
        if (responseData.content) {
            const outcomes = parseBulletPoints(responseData.content);
            populateFieldsFromBulletPoints('concept-paper-learning-outcomes', outcomes, 'concept-paper-learning-outcomes');
        }
    } catch (error) {
        console.error('Error:', error);
        alert(`Error: ${error.message || 'Failed to generate learning outcomes. Please try again.'}`);
    } finally {
        setButtonLoading(generateButton, '', false);
    }
}

// Update the existing addLearningOutcome function
function addLearningOutcome() {
    const container = document.getElementById('concept-paper-learning-outcomes');
    const div = document.createElement('div');
    div.className = 'input-group';
    div.innerHTML = `
    <input type="text" name="concept-paper-learning-outcomes" placeholder="Enter Learning Outcome" required>
    <button type="button" class="delete-btn" onclick="this.parentElement.remove()">Delete</button>
`;
    container.appendChild(div);
}

async function generateExpectedParticipants() {
    const subject = document.getElementById('concept-paper-subject').value;
    await generateContent('/generate-concept-participants', {
        subject
    }, 'concept-paper-expected-number-of-participants');
}

async function generateConsentContent() {
    const subject = document.getElementById('concept-paper-subject').value;
    const startDate = document.getElementById('concept-paper-event-start-date-and-time').value;
    const endDate = document.getElementById('concept-paper-event-end-date-and-time').value;
    const location = document.getElementById('concept-paper-location').value;

    await generateContent('/generate-concept-consent', {
        subject,
        start_date: startDate,
        end_date: endDate,
        location
    }, 'parent-guardian-consent-content');
}