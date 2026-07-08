/**
 * Event Dashboard Page JavaScript
 * Handles chart visualization for top 5 expenses, top 5 income, and remaining budget
 */

document.addEventListener('DOMContentLoaded', function () {
    initializeEventDashboardCharts();
});

function initializeEventDashboardCharts() {
    // Data for top 5 expenses, top 5 income, and remaining budget
    let top5Expenses = window.top5Expenses || [];
    let top5Income = window.top5Income || [];
    let remainingBudget = window.remainingBudget || 0;
    let eventsBudget = window.eventsBudget || 0;

    // Extract data for charts
    let top5ExpensesData = top5Expenses.map(transaction => transaction.transaction_total);
    let top5IncomeData = top5Income.map(transaction => transaction.transaction_total);

    // Initialize the top 5 expenses chart
    const ctx1 = document.getElementById('top-5-expenses-chart');
    if (ctx1) {
        let top5ExpensesChart = new Chart(ctx1.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: top5Expenses.map(transaction => transaction.transaction_category),
                datasets: [
                    {
                        data: top5ExpensesData,
                        backgroundColor: [
                            getCssVariable('--expense-color-1'),
                            getCssVariable('--expense-color-2'),
                            getCssVariable('--expense-color-3'),
                            getCssVariable('--expense-color-4'),
                            getCssVariable('--expense-color-5')
                        ],
                        borderColor: [
                            getCssVariable('--expense-color-1'),
                            getCssVariable('--expense-color-2'),
                            getCssVariable('--expense-color-3'),
                            getCssVariable('--expense-color-4'),
                            getCssVariable('--expense-color-5')
                        ],
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
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
                    }
                }
            }
        });
    }

    // Initialize the top 5 income chart
    const ctx2 = document.getElementById('top-5-income-chart');
    if (ctx2) {
        let top5IncomeChart = new Chart(ctx2.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: top5Income.map(transaction => transaction.transaction_category),
                datasets: [
                    {
                        data: top5IncomeData,
                        backgroundColor: [
                            getCssVariable('--income-color-1'),
                            getCssVariable('--income-color-2'),
                            getCssVariable('--income-color-3'),
                            getCssVariable('--income-color-4'),
                            getCssVariable('--income-color-5')
                        ],
                        borderColor: [
                            getCssVariable('--income-color-1'),
                            getCssVariable('--income-color-2'),
                            getCssVariable('--income-color-3'),
                            getCssVariable('--income-color-4'),
                            getCssVariable('--income-color-5')
                        ],
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
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
                    }
                }
            }
        });
    }

    // Determine the color based on the remaining budget
    let remainingBudgetColor = getCssVariable('--remaining-budget-color');
    let expensesWithinBudgetColor = getCssVariable('--expenses-within-budget-color');
    let expensesOverBudgetColor = getCssVariable('--expenses-over-budget-color');

    // Data for expenses within and over budget
    let totalExpense = window.totalExpense || 0;
    let totalIncome = window.totalIncome || 0;
    let expensesWithinBudget = totalExpense <= eventsBudget ? totalExpense : eventsBudget;
    let expensesOverBudget = totalExpense > eventsBudget ? totalExpense - eventsBudget : 0;

    // Data and labels for the chart
    let chartData = [
        { label: 'Remaining Budget', value: remainingBudget, color: remainingBudgetColor },
        { label: 'Expenses Within Budget', value: expensesWithinBudget, color: expensesWithinBudgetColor },
        { label: 'Expenses Over Budget', value: expensesOverBudget, color: expensesOverBudgetColor }
    ];

    // Filter out data points with value 0
    chartData = chartData.filter(dataPoint => dataPoint.value > 0);

    // Extract labels, data, and colors for the chart
    let labels = chartData.map(dataPoint => dataPoint.label);
    let data = chartData.map(dataPoint => dataPoint.value);
    let backgroundColors = chartData.map(dataPoint => dataPoint.color);
    let borderColors = chartData.map(dataPoint => dataPoint.color);

    // Initialize the remaining budget chart
    const ctx3 = document.getElementById('remaining-budget-chart');
    if (ctx3) {
        let remainingBudgetChart = new Chart(ctx3.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [
                    {
                        data: data,
                        backgroundColor: backgroundColors,
                        borderColor: borderColors,
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: labels.length > 0,
                        labels: {
                            color: getCssVariable('--primary-text-color'),
                            font: {
                                family: getCssVariable('--chart-font-family'),
                                size: parseInt(getCssVariable('--chart-font-size')),
                                weight: getCssVariable('--chart-font-weight')
                            }
                        }
                    }
                }
            }
        });
    }

    // Update charts when color scheme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        updateChartColors(top5ExpensesChart, top5IncomeChart, remainingBudgetChart);
    });
}

// Function to update chart colors dynamically
function updateChartColors(top5ExpensesChart, top5IncomeChart, remainingBudgetChart) {
    const labelColor = getLabelColor();
    const rangeColor = getRangeColor();

    if (top5ExpensesChart) {
        top5ExpensesChart.options.plugins.legend.labels.color = labelColor;
        top5ExpensesChart.update();
    }

    if (top5IncomeChart) {
        top5IncomeChart.options.plugins.legend.labels.color = labelColor;
        top5IncomeChart.update();
    }

    if (remainingBudgetChart) {
        remainingBudgetChart.options.plugins.legend.labels.color = labelColor;
        remainingBudgetChart.update();
    }
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
