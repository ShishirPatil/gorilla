function createHistogram(containerId, data, category) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container with id "${containerId}" not found.`);
        return;
    }

    const layout = {
        title: `Distribution of ${category}`,
        height: 450,
        width: 550,
        barmode: 'overlay',
        xaxis: { title: category, range: [0, 100]},
        yaxis: { title: 'Frequency' },
        margin: { l: 100, r: 100, b: 50, t: 80, pad: 4 },
        legend: { // Adjust legend position
            x: 0.1, // Positioning the legend to the left of the plot
            y: 1,
            xanchor: 'left',
            yanchor: 'top'
        },
    };

    // Convert percentage strings to numbers
    const plotData = data.slice(0, 2).map(trace => ({
        ...trace,
        x: trace.x.map(x => parseFloat(x)),
        opacity: 0.7,
        xbins: {
            start: 0,
            end: 100,
            size: 10
        },
    }));

    Plotly.newPlot(containerId, plotData, layout, { responsive: true });
}

function createScatterPlot(containerId, data, category) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container with id "${containerId}" not found.`);
        return;
    }

    const layout = {
        title: `Comparison of ${category}`,
        height: 450,
        width: 450,
        xaxis: { title: `${category} (BFCL)`, range: [0, 100] },
        yaxis: { title: `${category} (BFCL Live)`, range: [0, 100] },
        margin: { l: 50, r: 50, b: 50, t: 80, pad: 4 } // Increased top margin
    };

    // Convert percentage strings to numbers
    const scatterData = {
        ...data[2],
        x: data[2].x.map(x => parseFloat(x)),
        y: data[2].y.map(y => parseFloat(y)),
        marker: {
            size: 8, // Adjust size here
            opacity: 0.6
        }
    };

    const plotData = [
        scatterData,
        {
            x: [0, 100],
            y: [0, 100],
            mode: 'lines',
            name: 'y=x',
            line: { color: 'red', dash: 'dash' }
        }
    ];

    Plotly.newPlot(containerId, plotData, layout, { responsive: true });
}

// Make functions available globally
window.createHistogram = createHistogram;
window.createScatterPlot = createScatterPlot;