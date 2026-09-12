function renderTopicChart(chartData) {
    const canvas = document.getElementById('topicChart');
    if (!canvas) return;

    const labels = chartData.map(item => item.label || 'Topic');
    const values = chartData.map(item => Number(item.value) || 0);
    const context = canvas.getContext('2d');
    const fill = context.createLinearGradient(0, 0, canvas.width, 0);
    fill.addColorStop(0, '#2563eb');
    fill.addColorStop(1, '#14b8a6');

    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Topic Accuracy (%)',
                data: values,
                backgroundColor: fill,
                borderColor: '#1d4ed8',
                borderWidth: 1,
                borderRadius: 7,
                borderSkipped: false,
                barPercentage: 0.68,
                categoryPercentage: 0.78,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            animation: {
                duration: 850,
                easing: 'easeOutQuart',
            },
            interaction: {
                intersect: false,
                mode: 'index',
            },
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    displayColors: false,
                    padding: 12,
                    callbacks: {
                        label: function (context) {
                            return ` Accuracy: ${context.parsed.x}%`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    grid: {
                        display: false,
                        drawBorder: false,
                    },
                    ticks: {
                        color: '#475569',
                        font: {
                            family: 'Inter',
                            size: 11,
                            weight: '600',
                        },
                        padding: 8,
                    }
                },
                x: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: 'rgba(148, 163, 184, 0.16)',
                        drawBorder: false,
                    },
                    ticks: {
                        color: '#64748b',
                        stepSize: 20,
                        padding: 6,
                        callback: function (value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}
