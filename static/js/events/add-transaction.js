/**
 * Add Transaction Page JavaScript
 * Handles date initialization, category toggle, total calculation, and file upload
 */

document.addEventListener('DOMContentLoaded', function () {
    initializeAddTransactionForm();
});

function initializeAddTransactionForm() {
    // Set default date to current date/time
    const transactionDateInput = document.getElementById('transaction-date');
    if (transactionDateInput) {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const formattedDate = `${year}-${month}-${day}T${hours}:${minutes}`;
        transactionDateInput.value = formattedDate;
    }

    // Transaction category toggle
    const transactionCategorySelect = document.getElementById('transaction-category');
    const otherTransactionCategoryContainer = document.getElementById('other-transaction-category-container');

    if (transactionCategorySelect) {
        transactionCategorySelect.addEventListener('change', function () {
            if (transactionCategorySelect.value === 'Other') {
                otherTransactionCategoryContainer.classList.remove('hidden');
            } else {
                otherTransactionCategoryContainer.classList.add('hidden');
            }
        });
    }

    // Total calculation
    const unitAmountInput = document.getElementById('transaction-unit-amount');
    const unitPriceInput = document.getElementById('transaction-unit-price');
    const totalInput = document.getElementById('transaction-total');

    if (unitAmountInput && unitPriceInput && totalInput) {
        function calculateTotal() {
            const unitAmount = parseFloat(unitAmountInput.value) || 0;
            const unitPrice = parseFloat(unitPriceInput.value) || 0;
            const total = unitAmount * unitPrice;
            totalInput.value = total.toFixed(2);
        }

        unitAmountInput.addEventListener('input', calculateTotal);
        unitPriceInput.addEventListener('input', calculateTotal);
    }

    // File upload handling
    const transactionReceipt = document.getElementById('transaction-receipt');
    if (transactionReceipt) {
        transactionReceipt.addEventListener('change', function () {
            const fileName = this.files[0] ? this.files[0].name : 'No file chosen';
            const fileNameElement = document.getElementById('file-name');
            if (fileNameElement) {
                fileNameElement.textContent = fileName;
            }
        });
    }
}
