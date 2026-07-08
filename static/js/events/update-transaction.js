/**
 * Update Transaction Page JavaScript
 * Handles category toggle, total calculation, and file upload
 */

document.addEventListener('DOMContentLoaded', function () {
    initializeUpdateTransactionForm();
});

function initializeUpdateTransactionForm() {
    // Transaction category toggle
    const transactionCategorySelect = document.getElementById('transaction-category');
    const otherTransactionCategoryContainer = document.getElementById('other-transaction-category-container');

    if (transactionCategorySelect) {
        transactionCategorySelect.addEventListener('change', function () {
            if (transactionCategorySelect.value === 'Other') {
                otherTransactionCategoryContainer.style.display = 'block';
            } else {
                otherTransactionCategoryContainer.style.display = 'none';
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
