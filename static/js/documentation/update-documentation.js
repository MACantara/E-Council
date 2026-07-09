// Update Documentation JavaScript
// Uses utilities from utils.js

document.addEventListener('DOMContentLoaded', function () {
    initializeEventSelect();
    initializeFileUploads();
    initializeTallySystem();
    initializeDynamicLists();
    initializeAcademicYearToggle();

    // Initialize add field buttons
    document.getElementById('add-strength-btn')?.addEventListener('click', function () {
        addNewField('strengths', 'activity-strengths', 'strength');
    });
    document.getElementById('add-weakness-btn')?.addEventListener('click', function () {
        addNewField('weaknesses', 'activity-weaknesses', 'weakness');
    });
    document.getElementById('add-recommendation-btn')?.addEventListener('click', function () {
        addNewField('recommendations', 'activity-recommendations', 'recommendation');
    });
    document.getElementById('add-learning-btn')?.addEventListener('click', function () {
        addNewField('learnings', 'learnings', 'learning');
    });
    document.getElementById('add-observation-btn')?.addEventListener('click', function () {
        addNewField('observations', 'observations', 'observation');
    });
    document.getElementById('add-tally-item-btn')?.addEventListener('click', addNewTallyItem);
    document.getElementById('add-student-btn')?.addEventListener('click', addNewStudent);

    // Initialize remove buttons for existing items
    initializeRemoveButtons();
});

function initializeEventSelect() {
    const eventsSelect = document.getElementById('documentation-events-id');

    eventsSelect.addEventListener('change', function () {
        const eventId = this.value;
        fetchRelatedForms(
            eventId,
            'documentation-activity-report-forms-id',
            'documentation-learning-journal-forms-id',
            document.getElementById('learning-journal-forms-checked-by')
        );
    });
}

async function fetchRelatedForms(eventId, activityReportSelectId, learningJournalSelectId, learningJournalCheckedBySelect) {
    try {
        const response = await fetch(`/get-related-forms/${eventId}`);
        const data = await response.json();

        updateSelectOptions(activityReportSelectId, data.activity_reports, 'activity_report_forms_id', 'events_name', 'Select activity report forms');
        updateSelectOptions(learningJournalSelectId, data.learning_journals, 'learning_journal_forms_id', 'events_name', 'Select learning journal forms');
        updateSignatoryOptions(learningJournalCheckedBySelect, data.signatories);
    } catch (error) {
        console.error('Error fetching related forms:', error);
    }
}

function updateSignatoryOptions(select, signatories) {
    select.innerHTML = '<option value="" disabled selected>Select Signatory</option>';
    signatories.forEach(signatory => {
        const option = document.createElement('option');
        option.value = signatory.signatory_id;
        option.textContent = `${signatory.signatory_first_name} ${signatory.signatory_last_name} - ${signatory.signatory_position}`;
        option.selected = true;
        select.appendChild(option);
    });
}

function updateSelectOptions(selectId, data, valueField, textField, defaultText) {
    const select = document.getElementById(selectId);
    select.innerHTML = `<option value="" disabled ${!select.value ? 'selected' : ''}>${defaultText}</option>`;
    data.forEach(item => {
        const option = document.createElement('option');
        option.value = item[valueField];
        option.textContent = item[textField];
        if (select.value == item[valueField]) {
            option.selected = true;
        }
        select.appendChild(option);
    });
}

function addNewField(containerId, name, placeholder) {
    const container = document.getElementById(containerId + '-list');
    const newItem = document.createElement('div');
    newItem.className = 'dynamic-item flex items-center gap-2';
    newItem.innerHTML = `
        <input type="text" name="${name}[]" class="w-full rounded-lg border border-edge bg-surface px-3.5 py-2.5 text-sm text-ink placeholder:text-ink-3 transition-colors focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent" placeholder="Enter ${placeholder}" required>
        <button type="button" class="remove-item-btn inline-flex shrink-0 items-center justify-center rounded-lg border border-danger px-3 py-2.5 text-sm font-medium text-danger transition-colors hover:bg-danger hover:text-white">&times;</button>
    `;
    container.appendChild(newItem);

    // Add event listener to the remove button
    const removeBtn = newItem.querySelector('.remove-item-btn');
    removeBtn.addEventListener('click', function () {
        removeItem(this);
    });
}

function removeItem(button) {
    button.parentElement.remove();
}

function initializeDynamicLists() {
    // Add event listeners to existing remove buttons
    const removeButtons = document.querySelectorAll('.remove-item-btn');
    removeButtons.forEach(button => {
        button.addEventListener('click', function () {
            removeItem(this);
        });
    });
}

function initializeRemoveButtons() {
    // Initialize remove buttons for existing images
    document.querySelectorAll('.remove-file-button').forEach(button => {
        button.addEventListener('click', function () {
            removeExistingImage(this);
        });
    });

    document.querySelectorAll('.remove-existing-attendance-btn').forEach(button => {
        button.addEventListener('click', function () {
            removeExistingAttendanceImage(this);
        });
    });

    document.querySelectorAll('.remove-existing-event-photo-doc-btn').forEach(button => {
        button.addEventListener('click', function () {
            removeExistingEventPhotoDocImage(this);
        });
    });
}

function removeExistingImage(button) {
    const imageItem = button.closest('.selected-file-item');
    const imageId = imageItem.getAttribute('data-image-id');
    const deletedImagesInput = document.getElementById('deleted-evaluation-images');
    const currentDeleted = deletedImagesInput.value ? deletedImagesInput.value.split(',') : [];
    currentDeleted.push(imageId);
    deletedImagesInput.value = currentDeleted.join(',');
    imageItem.remove();
}

function removeExistingAttendanceImage(button) {
    const imageItem = button.closest('.selected-file-item');
    const imageId = imageItem.getAttribute('data-image-id');
    const deletedImagesInput = document.getElementById('deleted-attendance-images');
    const currentDeleted = deletedImagesInput.value ? deletedImagesInput.value.split(',') : [];
    currentDeleted.push(imageId);
    deletedImagesInput.value = currentDeleted.join(',');
    imageItem.remove();
}

function removeExistingEventPhotoDocImage(button) {
    const imageItem = button.closest('.selected-file-item');
    const imageId = imageItem.getAttribute('data-image-id');
    const deletedImagesInput = document.getElementById('deleted-event-photo-doc-images');
    const currentDeleted = deletedImagesInput.value ? deletedImagesInput.value.split(',') : [];
    currentDeleted.push(imageId);
    deletedImagesInput.value = currentDeleted.join(',');
    imageItem.remove();
}

function addNewTallyItem() {
    const tallyItemsContainer = document.querySelector('.tally-table tbody');
    const nameRow = tallyItemsContainer.querySelector('.tally-item-name').cloneNode(true);
    const ratingsRow = tallyItemsContainer.querySelector('.tally-item-ratings').cloneNode(true);

    // Clear input values
    nameRow.querySelectorAll('input').forEach(input => input.value = '');
    ratingsRow.querySelectorAll('input').forEach(input => {
        if (input.type === 'number') input.value = '0';
    });

    tallyItemsContainer.appendChild(nameRow);
    tallyItemsContainer.appendChild(ratingsRow);
    syncTallyItems();
}

function addNewStudent() {
    const studentList = document.getElementById('evaluation-student-list');
    if (!studentList) return;
    const newStudent = document.createElement('div');
    newStudent.className = 'dynamic-item flex items-center gap-2';
    newStudent.innerHTML = `
        <input type="text" name="student-names[]" placeholder="Enter student name" class="w-full rounded-lg border border-edge bg-surface px-3.5 py-2.5 text-sm text-ink placeholder:text-ink-3 transition-colors focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent">
        <button type="button" class="remove-item-btn inline-flex shrink-0 items-center justify-center rounded-lg border border-danger px-3 py-2.5 text-sm font-medium text-danger transition-colors hover:bg-danger hover:text-white">×</button>
    `;
    studentList.appendChild(newStudent);

    // Add event listener to the remove button
    const removeBtn = newStudent.querySelector('.remove-item-btn');
    removeBtn.addEventListener('click', function () {
        removeItem(this);
    });
}

function initializeFileUploads() {
    setupFileUpload('evaluation-images', 'evaluation-files-name', 'evaluation-files-list');
    setupFileUpload('attendance-images', 'attendance-files-name', 'attendance-files-list');
    setupFileUpload('event-photo-documentation-images', 'event-photo-doc-files-name', 'event-photo-doc-files-list', true);
}

function setupFileUpload(inputId, nameSpanId, listId, includePreview = false) {
    const input = document.getElementById(inputId);
    const filesNameSpan = document.getElementById(nameSpanId);
    const filesList = document.getElementById(listId);

    if (!input) return;

    input.addEventListener('change', function() {
        updateFileList(this, filesNameSpan, filesList, includePreview);
    });
}

function updateFileList(input, filesNameSpan, filesList, includePreview) {
    filesList.innerHTML = '';

    if (input.files.length > 0) {
        filesNameSpan.textContent = `${input.files.length} file(s) selected`;

        Array.from(input.files).forEach((file, index) => {
            const fileItem = createFileItem(file, index, input, includePreview);
            filesList.appendChild(fileItem);
        });
    } else {
        filesNameSpan.textContent = 'No files chosen';
    }
}

function createFileItem(file, index, input, includePreview) {
    const fileItem = document.createElement('div');
    fileItem.className = 'selected-file-item flex items-center justify-between gap-3 rounded-lg border border-edge bg-surface-lowered px-3.5 py-2.5';

    const fileInfo = document.createElement('div');
    fileInfo.className = 'flex items-center gap-3 min-w-0';

    if (includePreview && file.type.startsWith('image/')) {
        const preview = createImagePreview(file);
        fileInfo.appendChild(preview);
    }

    const fileName = document.createElement('span');
    fileName.textContent = file.name;
    fileName.className = 'truncate text-sm text-ink';
    fileInfo.appendChild(fileName);

    fileItem.appendChild(fileInfo);

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'remove-file-btn inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-danger text-sm font-medium text-danger transition-colors hover:bg-danger hover:text-white';
    removeBtn.textContent = '×';
    removeBtn.addEventListener('click', () => removeFile(index, input));

    fileItem.appendChild(removeBtn);
    return fileItem;
}

function createImagePreview(file) {
    const previewContainer = document.createElement('div');
    previewContainer.className = 'file-preview-container h-10 w-10 shrink-0 overflow-hidden rounded-lg';

    const preview = document.createElement('img');
    preview.className = 'file-preview h-full w-full object-cover';
    preview.src = URL.createObjectURL(file);

    previewContainer.appendChild(preview);
    return previewContainer;
}

function removeFile(index, input) {
    const dt = new DataTransfer();
    const { files } = input;

    for (let i = 0; i < files.length; i++) {
        if (i !== index) {
            dt.items.add(files[i]);
        }
    }

    input.files = dt.files;
    input.dispatchEvent(new Event('change'));
}

function initializeTallySystem() {
    const tallyTable = document.querySelector('.tally-table');

    syncTallyItems();

    tallyTable.addEventListener('input', e => {
        if (e.target.type === 'text') {
            syncTallyItems();
        }
    });

    document.querySelector('.evaluation-tally-table')?.addEventListener('change', e => {
        if (e.target.type === 'radio') {
            calculateOverallRating();
        }
    });
}

function syncTallyItems() {
    const tallyRows = document.querySelectorAll('.tally-table tbody tr');
    const evaluationTallyContainer = document.querySelector('.evaluation-tally-table tbody');
    if (!evaluationTallyContainer) return;

    evaluationTallyContainer.innerHTML = '';

    const radioClass = 'h-4 w-4 border-edge text-accent focus:ring-accent';
    tallyRows.forEach((row, index) => {
        const nameInput = row.querySelector('input[type="text"]');
        if (nameInput) {
            const newRow = document.createElement('tr');
            newRow.innerHTML = `
                <td class="border-b border-edge px-3 py-2 text-sm text-ink">${nameInput.value || `Item ${index + 1}`}</td>
                <td class="border-b border-edge px-3 py-2 text-center"><input type="radio" class="${radioClass}" name="rating-${index}" value="1" required></td>
                <td class="border-b border-edge px-3 py-2 text-center"><input type="radio" class="${radioClass}" name="rating-${index}" value="2"></td>
                <td class="border-b border-edge px-3 py-2 text-center"><input type="radio" class="${radioClass}" name="rating-${index}" value="3"></td>
                <td class="border-b border-edge px-3 py-2 text-center"><input type="radio" class="${radioClass}" name="rating-${index}" value="4"></td>
                <td class="border-b border-edge px-3 py-2 text-center"><input type="radio" class="${radioClass}" name="rating-${index}" value="5"></td>
            `;
            evaluationTallyContainer.appendChild(newRow);
        }
    });
}

function calculateOverallRating() {
    const ratingInputs = document.querySelectorAll('.evaluation-tally-table input[type="radio"]:checked');
    if (ratingInputs.length === 0) return;

    let total = 0;
    ratingInputs.forEach(input => {
        total += parseInt(input.value);
    });

    const average = (total / ratingInputs.length).toFixed(2);
    const ratingInput = document.getElementById('documentation-rating');
    const ratingValue = document.getElementById('calculated-rating-value');
    if (ratingInput) {
        ratingInput.value = average;
    }
    if (ratingValue) {
        ratingValue.textContent = average;
    }
}

function initializeAcademicYearToggle() {
    const academicYearSelect = document.getElementById('documentation-academic-year');
    const otherAcademicYearContainer = document.getElementById('other-academic-year-container');

    if (!academicYearSelect || !otherAcademicYearContainer) return;

    academicYearSelect.addEventListener('change', function () {
        if (academicYearSelect.value === 'Other') {
            otherAcademicYearContainer.style.display = 'flex';
        } else {
            otherAcademicYearContainer.style.display = 'none';
        }
    });

    // Initialize academic year toggle
    if (academicYearSelect.value === 'Other') {
        otherAcademicYearContainer.style.display = 'flex';
    }
}
