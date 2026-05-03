let chart;

// -------------------------
// CALL FLASK API
// -------------------------
async function predictPatients() {

    const data = {
        exam_period: document.getElementById("exam_period").value,
        rainfall: document.getElementById("rainfall").value,
        temperature: document.getElementById("temperature").value
    };

    const response = await fetch("/predict", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    });

    const result = await response.json();

    // Show result
    document.getElementById("result").innerText =
        "Predicted Patients: " + result.predicted_patients;

    // Update chart
    updateChart(result.predicted_patients);
}


// -------------------------
// CHART VISUALIZATION
// -------------------------
function updateChart(predictedValue) {

    const ctx = document.getElementById("trendChart").getContext("2d");

    const labels = ["Low Demand", "Medium Demand", "High Demand"];

    const dataValues = [
        predictedValue * 0.6,
        predictedValue,
        predictedValue * 1.4
    ];

    if (chart) {
        chart.destroy();
    }

    chart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: "Patient Demand Trend",
                data: dataValues,
                borderWidth: 2,
                fill: false
            }]
        },
        options: {
            responsive: true
        }
    });
}