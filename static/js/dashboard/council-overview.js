/**
 * Council Overview Dashboard Page JavaScript
 * Handles chart visualization for financial bank book, activity completion rate, and activity evaluation
 */

document.addEventListener('DOMContentLoaded', function () {
    initializeCouncilOverviewCharts();
});

function initializeCouncilOverviewCharts() {
    // Data for the charts
    const financialBankBookData = {
        labels: ["Income", "Expenses", "Savings"],
        datasets: [{
            label: "Financial Bank Book",
            data: [12000, 8000, 4000],
            backgroundColor: [
                "rgba(0, 128, 0, 1)",
                "rgba(255, 0, 0, 1)",
                "rgba(255, 165, 0, 1)"
            ],
            borderColor: [
                "rgba(0, 128, 0, 1)",
                "rgba(255, 0, 0, 1)",
                "rgba(255, 165, 0, 1)"
            ],
            borderWidth: 1
        }]
    };

    const activityCompletionRateData = {
        labels: ["Completed", "In Progress", "Not Started"],
        datasets: [{
            label: "Activity Completion Rate",
            data: [80, 15, 5],
            backgroundColor: [
                "rgba(0, 128, 0, 1)",
                "rgba(255, 165, 0, 1)",
                "rgba(255, 0, 0, 1)"
            ],
            borderColor: [
                "rgba(0, 128, 0, 1)",
                "rgba(255, 165, 0, 1)",
                "rgba(255, 0, 0, 1)"
            ],
            borderWidth: 1
        }]
    };

    const activityEvaluationGraphData = {
        labels: ["Criteria 1", "Criteria 2", "Criteria 3"],
        datasets: [{
            label: "Activity Evaluation",
            data: [70, 85, 90],
            backgroundColor: "rgba(75, 192, 192, 1)",
            borderColor: "rgba(75, 192, 192, 1)",
            borderWidth: 1
        }]
    };

    // Create the charts
    const financialBankBookChart = new Chart(document.getElementById("financial-bank-book-chart"), {
        type: "doughnut",
        data: financialBankBookData,
        options: {
            title: {
                display: true,
                text: "Financial Bank Book",
                font: {
                    color: getLabelColor()
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
                }
            }
        }
    });

    const activityCompletionRateChart = new Chart(document.getElementById("activity-completion-rate-chart"), {
        type: "doughnut",
        data: activityCompletionRateData,
        options: {
            title: {
                display: true,
                text: "Activity Completion Rate",
                font: {
                    color: getLabelColor()
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
                }
            }
        }
    });

    const activityEvaluationGraphChart = new Chart(document.getElementById("activity-evaluation-graph-chart"), {
        type: 'bar',
        data: activityEvaluationGraphData,
        options: {
            title: {
                display: true,
                text: "Activity Evaluation",
                font: {
                    color: getLabelColor()
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
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: "Criteria",
                        color: getRangeColor(),
                        font: {
                            size: getFontSize()
                        }
                    },
                    ticks: {
                        color: getRangeColor(),
                        font: {
                            size: getFontSize()
                        }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: "Scores",
                        color: getRangeColor(),
                        font: {
                            size: getFontSize()
                        }
                    },
                    ticks: {
                        color: getRangeColor(),
                        font: {
                            size: getFontSize()
                        }
                    }
                }
            }
        }
    });

    // Update charts when color scheme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        updateChartColors(financialBankBookChart, activityCompletionRateChart, activityEvaluationGraphChart);
    });
}

// Function to update chart colors based on the prefers-color-scheme setting
function updateChartColors(financialBankBookChart, activityCompletionRateChart, activityEvaluationGraphChart) {
    const labelColor = getLabelColor();
    const rangeColor = getRangeColor();

    financialBankBookChart.options.plugins.legend.labels.color = labelColor;
    financialBankBookChart.options.title.font.color = labelColor;
    financialBankBookChart.update();

    activityCompletionRateChart.options.plugins.legend.labels.color = labelColor;
    activityCompletionRateChart.options.title.font.color = labelColor;
    activityCompletionRateChart.update();

    activityEvaluationGraphChart.options.plugins.legend.labels.color = labelColor;
    activityEvaluationGraphChart.options.scales.y.title.color = rangeColor;
    activityEvaluationGraphChart.options.scales.y.ticks.color = rangeColor;
    activityEvaluationGraphChart.options.scales.x.title.color = rangeColor;
    activityEvaluationGraphChart.options.scales.x.ticks.color = rangeColor;
    activityEvaluationGraphChart.options.title.font.color = labelColor;
    activityEvaluationGraphChart.update();
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
