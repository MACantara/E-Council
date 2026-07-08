/**
 * Events Overview Page JavaScript
 * Handles event status updates and budget chart visualization
 */

document.addEventListener('DOMContentLoaded', function () {
    initializeEventStatusUpdates();
    initializeBudgetCharts();
});

// ============================================
// Event Status Updates
// ============================================

function initializeEventStatusUpdates() {
    const selects = document.querySelectorAll('select[name="event-status-select-button"]');
    selects.forEach(select => {
        select.addEventListener('change', function () {
            const eventId = this.getAttribute('data-event-id');
            const newStatus = this.value;
            const eventName = this.getAttribute('data-event-name');

            fetch(`/events/update-event-status/${eventId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ status: newStatus, name: eventName })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(`Event status for "${eventName}" updated successfully.`);
                    } else {
                        alert(`Failed to update event status for "${eventName}".`);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert(`An error occurred while updating the event status for "${eventName}".`);
                });
        });
    });
}

// ============================================
// Budget Chart Visualization
// ============================================

function initializeBudgetCharts() {
    // Get event data from global variable (set by template)
    const eventData = window.eventData || [];
    console.log("Event Data:", eventData);

    const canvasElements = document.querySelectorAll('[id^="budget-chart-"]');
    const charts = [];

    canvasElements.forEach((canvasElement, index) => {
        const ctx = canvasElement.getContext('2d');
        if (ctx) {
            const eventId = canvasElement.getAttribute('data-event-id');
            const event = eventData.find(e => e.event_id == eventId);

            if (!event) {
                console.error(`Event with ID ${eventId} not found in eventData`);
                return;
            }

            // Always use green color for remaining budget
            const remainingBudgetColor = getCssVariable('--remaining-budget-color');
            const expensesWithinBudgetColor = getCssVariable('--expenses-within-budget-color');
            const expensesOverBudgetColor = getCssVariable('--expenses-over-budget-color');
            const remainingBudget = event.remaining_budget > 0 ? event.remaining_budget : 0;

            // Datasets array
            const datasets = [
                {
                    label: 'Remaining Budget',
                    data: [remainingBudget],
                    backgroundColor: remainingBudgetColor,
                    borderColor: remainingBudgetColor,
                    borderWidth: 1,
                    stack: 'Stack 0'
                }
            ];

            // Calculate expenses within budget and over budget
            const expensesWithinBudget = event.total_expense > event.events_budget ? event.events_budget : event.total_expense;
            const expensesOverBudget = event.total_expense > remainingBudget ? event.total_expense - event.events_budget : 0;

            // If remaining budget is 0 or less, add the "Expenses (over budget)" dataset
            if (remainingBudget <= 0) {
                datasets.push({
                    label: 'Expenses (Within Budget)',
                    data: [expensesWithinBudget],
                    backgroundColor: expensesWithinBudgetColor,
                    borderColor: expensesWithinBudgetColor,
                    borderWidth: 1,
                    stack: 'Stack 1'
                }, {
                    label: 'Expenses (Over Budget)',
                    data: [expensesOverBudget],
                    backgroundColor: expensesOverBudgetColor,
                    borderColor: expensesOverBudgetColor,
                    borderWidth: 1,
                    stack: 'Stack 1'
                });
            } else {
                datasets.push({
                    label: 'Expenses',
                    data: [event.total_expense],
                    backgroundColor: expensesWithinBudgetColor,
                    borderColor: expensesWithinBudgetColor,
                    borderWidth: 1,
                    stack: 'Stack 1'
                });
            }

            // Destroy existing chart instance if it exists
            if (canvasElement.chartInstance) {
                canvasElement.chartInstance.destroy();
            }

            const budgetChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Budget Overview'],
                    datasets: datasets
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            display: false
                        },
                        x: {
                            stacked: true,
                            beginAtZero: true,
                            ticks: {
                                color: getCssVariable('--primary-text-color')
                            },
                            title: {
                                display: true,
                                color: getCssVariable('--primary-text-color')
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: true,
                            labels: {
                                color: getLabelColor(),
                                font: {
                                    family: getFontFamily(),
                                    size: getFontSize(),
                                    weight: getFontWeight()
                                }
                            }
                        },
                    },
                }
            });

            // Store the chart instance on the canvas element
            canvasElement.chartInstance = budgetChart;
            charts.push(budgetChart);
        }
    });

    // Update charts when theme changes
    document.addEventListener('themeChanged', function () {
        updateChartColors(charts);
    });
}

// Function to update chart colors dynamically
function updateChartColors(charts) {
    const labelColor = getLabelColor();
    const rangeColor = getRangeColor();

    charts.forEach(chart => {
        // Update legend label colors
        chart.options.plugins.legend.labels.color = labelColor;
        chart.options.scales.x.title.color = rangeColor;
        chart.options.scales.x.ticks.color = rangeColor;
        chart.update();
    });
}

// ============================================
// Chart Color Utilities
// ============================================

function getCssVariable(variable) {
    return getComputedStyle(document.documentElement).getPropertyValue(variable).trim();
}

function getLabelColor() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
        ? getCssVariable('--primary-text-color')
        : getCssVariable('--primary-text-color');
}

function getRangeColor() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
        ? getCssVariable('--primary-text-color')
        : getCssVariable('--primary-text-color');
}

function getFontFamily() {
    chartFontFamily = getCssVariable('--chart-font-family');
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
        ? chartFontFamily
        : chartFontFamily;
}

function getFontSize() {
    chartFontSize = getCssVariable('--chart-font-size');
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
        ? chartFontSize
        : chartFontSize;
}

function getFontWeight() {
    chartFontWeight = getCssVariable('--chart-font-weight');
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
        ? chartFontWeight
        : chartFontWeight;
}
