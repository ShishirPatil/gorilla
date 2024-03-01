EXAMPLES = [
    { "name": "requests.get", "description": "Sends a GET request to the specified URL.", "parameters": { "type": "dict", "properties": { "url": { "type": "string", "description": "The Open-Meteo API provides detailed weather forecasts for any location worldwide. It offers forecasts up to 16 days in advance and also provide past data. The API's response gives weather variables on an hourly basis, such as temperature, humidity, precipitation, wind speed and direction, etc. More information can be found in https://open-meteo.com/en/docs/", "default": "https://api.open-meteo.com/v1/forecast" }, "headers": {}, "timeout": { "type": ["number", "tuple"], "description": "How many seconds to wait for the server to send data before giving up.", "required": false }, "params": { "latitude": { "type": "string", "description": "Geographical WGS84 coordinates of the location. Multiple coordinates can be comma separated. E.g., &latitude=52.52,48.85&longitude=13.41,2.35. To return data for multiple locations the JSON output changes to a list of structures. CSV and XLSX formats add a column location_id. N is positive, S is negative", "required": true }, "longitude": { "type": "string", "description": "Geographical WGS84 coordinates of the location. Multiple coordinates can be comma separated. E is positive, W is negative", "required": true }, "elevation": { "type": "string", "description": "The elevation used for statistical downscaling. Per default, a 90 meter digital elevation model is used. You can manually set the elevation to correctly match mountain peaks. If &elevation=nan is specified, downscaling will be disabled and the API uses the average grid-cell height. For multiple locations, elevation can also be comma separated.", "required": false }, "hourly": { "type": "string", "description": "A list of weather variables which should be returned. Values can be comma separated, or multiple &hourly= parameters in the URL can be used. Support parameters: temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,pressure_msl,cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,wind_speed_10m,wind_speed_80m,wind_speed_120m,wind_speed_180m,wind_direction_10m,wind_direction_80m,wind_direction_120m,wind_direction_180m,wind_gusts_10m,shortwave_radiation,direct_radiation,direct_normal_irradiance,diffuse_radiation,global_tilted_irradiance,vapour_pressure_deficit,cape,evapotranspiration,et0_fao_evapotranspiration,precipitation,snowfall,precipitation_probability,rain,showers,weather_code,snow_depth,freezing_level_height,visibility,soil_temperature_0cm,soil_temperature_6cm,soil_temperature_18cm,soil_temperature_54cm,soil_moisture_0_to_1cm,soil_moisture_1_to_3cm,soil_moisture_3_to_9cm,soil_moisture_9_to_27cm,soil_moisture_27_to_81cm", "required": false }, "daily": { "type": "string", "description": "A list of daily weather variable aggregations which should be returned. Values can be comma separated, or multiple &daily= parameters in the URL can be used. If daily weather variables are specified, parameter timezone is required. Possible values supported temperature_2m_max, temperature_2m_min, apparent_temperature_max, apparent_temperature_min, precipitation_sum, rain_sum, showers_sum, snowfall_sum, precipitation_hours, ,precipitation_probability_max, precipitation_probability_min, precipitation_probability_mean, weather_code,sunrise,sunset,sunshine_duration, daylight_duration, wind_speed_10m_max, wind_gusts_10m_max, wind_direction_10m_dominant,shortwave_radiation_sum,et0_fao_evapotranspiration,uv_index_maxuv_index_clear_sky_max", "required": false }, "temperature_unit": { "type": "string", "description": "If fahrenheit is set, all temperature values are converted to Fahrenheit.", "required": false, "default": "celsius" }, "wind_speed_unit": { "type": "string", "description": "Other wind speed units: ms, mph, and kn.", "required": false, "default": "kmh" }, "precipitation_unit": { "type": "string", "description": "Other precipitation amount units: inch.", "required": false, "default": "mm" }, "timeformat": { "type": "string", "description": "If format unixtime is selected, all time values are returned in UNIX epoch time in seconds. Please note that all timestamps are in GMT+0! For daily values with unix timestamps, please apply utc_offset_seconds again to get the correct date.", "required": false, "default": "iso8601" }, "timezone": { "type": "string", "description": "If timezone is set, all timestamps are returned as local-time and data is returned starting at 00:00 local-time. Any time zone name from the time zone database is supported. If auto is set as a time zone, the coordinates will be automatically resolved to the local time zone. For multiple coordinates, a comma separated list of timezones can be specified.", "required": false, "default": "GMT" }, "past_days": { "type": "integer", "description": "If past_days is set, yesterday or the day before yesterday data are also returned.", "required": false, "default": 0 }, "forecast_days": { "type": "integer", "description": "Per default, only 7 days are returned. Up to 16 days of forecast are possible.", "required": false, "default": 7 }, "forecast_hours": { "type": "integer", "description": "Similar to forecast_days, the number of timesteps of hourly data can be controlled.", "required": false }, "forecast_minutely_15": { "type": "integer", "description": "The number of timesteps of 15-minutely data can be controlled.", "required": false }, "past_hours": { "type": "integer", "description": "the number of timesteps of hourly data controlled", "required": false }, "past_minutely_15": { "type": "integer", "description": "the number of timesteps of 15 minute data controlled", "required": false }, "start_date": { "type": "string", "description": "The time interval to get weather data. A day must be specified as an ISO8601 date (e.g. 2022-06-30).", "required": false }, "end_date": { "type": "string", "description": "", "required": false }, "start_hour": { "type": "string", "description": "The time interval to get weather data for hourly data. Time must be specified as an ISO8601 date and time (e.g. 2022-06-30T12:00).", "required": false }, "end_hour": { "type": "string", "description": "", "required": false }, "start_minutely_15": { "type": "string", "description": "", "required": false }, "end_minutely_15": { "type": "string", "description": "", "required": false }, "models": { "type": "list", "items": { "type": "string" }, "description": "A list of string, manually select one or more weather models. Per default, the best suitable weather models will be combined.", "required": false }, "cell_selection": { "type": "string", "description": "Set a preference how grid-cells are selected. The default land finds a suitable grid-cell on land with similar elevation to the requested coordinates using a 90-meter digital elevation model. sea prefers grid-cells on sea. nearest selects the nearest possible grid-cell.", "required": false }, "apikey": { "type": "string", "description": "Only required to commercial use to access reserved API resources for customers. The server URL requires the prefix customer-. See pricing for more information.", "required": false } }, "allow_redirects": { "type": "boolean", "description": "A Boolean to enable/disable redirection.", "default": true, "required": false }, "auth": { "type": "tuple", "description": "A tuple to enable a certain HTTP authentication.", "default": "None", "required": false }, "cert": { "type": ["string", "tuple"], "description": "A String or Tuple specifying a cert file or key.", "default": "None", "required": false }, "cookies": { "type": "dict", "additionalProperties": { "type": "string" }, "description": "Dictionary of cookies to send with the request.", "required": false }, "proxies": { "type": "dict", "additionalProperties": { "type": "string" }, "description": "Dictionary of the protocol to the proxy url.", "required": false }, "stream": { "type": "boolean", "description": "A Boolean indication if the response should be immediately downloaded (False) or streamed (True).", "default": false, "required": false }, "verify": { "type": ["boolean", "string"], "description": "A Boolean or a String indication to verify the servers TLS certificate or not.", "default": true, "required": false } } } },
    { "name": "requests.get", "description": "Sends a GET request to the specified URL.", "parameters": { "type": "dict", "properties": { "url": { "type": "string", "description": "Geocoding API converting a a pair of latitude and longitude coordinates to human readable addresses", "default": "https://geocode.maps.co/reverse" }, "headers": {}, "timeout": { "type": ["number", "tuple"], "description": "How many seconds to wait for the server to send data before giving up.", "required": false }, "params": { "lat": { "type": "number", "description": "Latitude of the location to reverse geocode.", "required": true }, "lon": { "type": "number", "description": "Longitude of the location to reverse geocode.", "required": true }, "format": { "type": "string", "description": "The desired response format. Options include 'xml', 'json', 'jsonv2', 'geojson', 'geocodejson'. Default is 'json'.", "required": false } }, "allow_redirects": { "type": "boolean", "description": "A Boolean to enable/disable redirection.", "default": true, "required": false }, "auth": { "type": "tuple", "description": "A tuple to enable a certain HTTP authentication.", "default": "None", "required": false }, "cert": { "type": ["string", "tuple"], "description": "A String or Tuple specifying a cert file or key.", "default": "None", "required": false }, "cookies": { "type": "dict", "additionalProperties": { "type": "string" }, "description": "Dictionary of cookies to send with the request.", "required": false }, "proxies": { "type": "dict", "additionalProperties": { "type": "string" }, "description": "Dictionary of the protocol to the proxy url.", "required": false }, "stream": { "type": "boolean", "description": "A Boolean indication if the response should be immediately downloaded (False) or streamed (True).", "default": false, "required": false }, "verify": { "type": ["boolean", "string"], "description": "A Boolean or a String indication to verify the servers TLS certificate or not.", "default": true, "required": false } } } },
    { "name": "requests.get", "description": "Sends a GET request to the specified URL.", "parameters": { "type": "dict", "properties": { "url": { "type": "string", "description": "The Date Nager API provides access holiday information for over 100 countries, including the ability to query for long weekends. It leverages ISO 3166-1 alpha-2 country codes to tailor the search to your specific region of interest. More information can be found in https://date.nager.at/Api", "default": "https://date.nager.at/api/v3/LongWeekend/{year}/{countryCode}" }, "headers": {}, "timeout": { "type": ["number", "tuple"], "description": "How many seconds to wait for the server to send data before giving up.", "required": false }, "params": {}, "auth": { "type": "tuple", "description": "A tuple to enable a certain HTTP authentication.", "default": "None", "required": false }, "cert": { "type": ["string", "tuple"], "description": "A String or Tuple specifying a cert file or key.", "default": "None", "required": false }, "cookies": { "type": "dict", "additionalProperties": { "type": "string" }, "description": "Dictionary of cookies to send with the request.", "required": false }, "proxies": { "type": "dict", "additionalProperties": { "type": "string" }, "description": "Dictionary of the protocol to the proxy url.", "required": false }, "stream": { "type": "boolean", "description": "A Boolean indication if the response should be immediately downloaded (False) or streamed (True).", "default": false, "required": false }, "verify": { "type": ["boolean", "string"], "description": "A Boolean or a String indication to verify the servers TLS certificate or not.", "default": true, "required": false } } } }
]

PROMPTS = [
    "I'm planning a camping trip and I need to know the weather forecast. Can you fetch me the weather data for the campsite located at latitude 35.68 and longitude -121.34 for the next 10 days including daily temperature and precipitation forecasts? Also, I prefer the temperature 2 minute max in Fahrenheit and sum of precipitation in inches.",
    "Can you provide the address for latitude 37.4224764 and longitude -122.0842499 using the Geocoding API?",
    "I'm planning a series of long weekend getaways for the upcoming year and I need to know when they'll occur in my country. Could you fetch me the list of long weekends for Canada in the year 2023? I'd like to integrate this information into my holiday planning app."
]
function populateInput(index) {
    document.getElementById('input-text').value = PROMPTS[index];
    document.getElementById('input-function').value = JSON.stringify(EXAMPLES[index], null, 2);
}


document.getElementById('example-btn-1').addEventListener('click', function () { populateInput(0) });
document.getElementById('example-btn-2').addEventListener('click', function () { populateInput(1) });
document.getElementById('example-btn-3').addEventListener('click', function () { populateInput(2) });


document.getElementById('submit-btn').addEventListener('click', async function () {
    var inputText = document.getElementById('input-text').value;
    var inputFunction = document.getElementById('input-function').value; // Assuming you have an input field with this id for the function
    var temperatureValue = document.getElementById('temperatureSlider').value;
    var model = document.getElementById("model-dropdown").value;

    if (inputText === "" || inputFunction === "") {
        alert("Please provide input and function definition.")
        return;
    }

    document.getElementById('code-output').innerText = 'Loading Model Response...';
    document.getElementById('json-output').innerText = 'Loading Model Response...';

    const requestData = {
        model: model,
        messages: [{ role: 'user', content: inputText }],
        functions: [inputFunction],
        temperature: parseFloat(temperatureValue),
    };

    const response = await fetch('https://luigi.millennium.berkeley.edu:443/v1/chat/completions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'EMPTY',
        },
        body: JSON.stringify(requestData)
    })

    if (!response.ok) {
        document.getElementById('code-output').innerText = 'Error: ' + response.status;
        return;
    }

    const jsonResponse = await response.json();

    if (model === "gorilla-openfunctions-v2") {
        directCode = jsonResponse.choices[0].message.content;
        jsonCode = jsonResponse.choices[0].message.function_call;
        document.getElementById('code-output').innerText = directCode;
        if (jsonCode) {
            jsonCode = JSON.stringify(jsonCode, null, 2); // Pretty print the JSON
            document.getElementById('json-output').innerText = jsonCode;
        } else {
            document.getElementById('json-output').innerText = 'Error parsing JSON output.';
        }
    } else {
        jsonCode = jsonResponse.choices[0].message.function_call;
        jsonCode = JSON.stringify(jsonResponse, null, 2); // Pretty print the JSON
        document.getElementById('json-output').innerText = jsonCode;
        document.getElementById('code-output').innerText = 'Model does not support direct code output.';
    }

    // const executeButton = document.getElementById('exec-btn');
    // executeButton.style.display = 'block'; // Ensure the button is visible after receiving a response
    // executeButton.addEventListener('click', function () {
    //     window.open("https://star-history.com/#ShishirPatil/gorilla&gorilla-llm/gorilla-cli")
    // });
    document.getElementById('thumbs-up-btn').style.display = 'block';
    document.getElementById('thumbs-down-btn').style.display = 'block';
    document.getElementById('report-issue-btn').style.display = 'block';
});


document.getElementById('report-issue-btn').addEventListener('click', function () {
    var inputText = document.getElementById('input-text').value;
    var funcDef = document.getElementById('input-function').value;
    var temperatureValue = document.getElementById('temperatureSlider').value;
    var model = document.getElementById("model-dropdown").value;
    var codeOutputText = document.getElementById('code-output').innerText;
    var jsonOutputText = document.getElementById('json-output').innerText;
    if (inputText === "" || funcDef === "") {
        alert("Please provide input and function definition to send feedback.")
        return;
    }
    var issueTitle = "[bug] OpenFunctions-v2: "
    var issueBody = `**Issue Description**%0A%0APrompt: ${inputText}%0A%0AModel: ${model}%0A%0ATemperature: ${temperatureValue}%0A%0AOutput (or Error if request failed): ${codeOutputText} %0A%0A ${jsonOutputText}%0A%0A**Additional Information**\n`;
    window.open(`https://github.com/ShishirPatil/gorilla/issues/new?assignees=&labels=hosted-openfunctions-v2&projects=&template=hosted-openfunctions-v2.md&title=${issueTitle}&body=${issueBody}`, '_blank');
});



const scriptURL = 'https://script.google.com/macros/s/AKfycbxdAKyEA36HA_p0k3KwMzMigxgFCZ1XegRBPfjgxlNaOK2CsOnP9hrEV_6V1ARCAJw3vw/exec'
const form = document.forms['submit-to-google-sheet']
const msg = document.getElementById("msg")
form.addEventListener('submit', e => {
    e.preventDefault()  // Prevents default refresh by the browser
    fetch(scriptURL, { method: 'POST', body: new FormData(form) })
        .then(response => {
            console.log('Success!', response);
            msg.innerHTML = "<span style='color: black;'>Message Sent Successfully!</span>";
            setTimeout(function () {
                msg.innerHTML = ""
            }, 5000)
            // form.reset()
        })
        .catch(error => console.error('Error!', error.message))
})





const ctx = document.getElementById('myChart');


const data = {
    labels: [
        'Irrelevance Detection',
        'Simple (AST)',
        'Parallel (AST)',
        'Multiple (AST)',
        'Parallel Multiple (AST)',
        'Simple (Exec)',
        'Parallel (Exec)',
        'Multiple (Exec)',
        'Parallel Multiple (Exec)'
    ],
    datasets: [
        {
            label: 'GPT-4-0125',
            data: [87.50, 82.18, 90.00, 90.00, 91.00, 54.12, 76.00, 70.00, 55.00],
            fill: true,
            backgroundColor: 'rgba(255, 206, 86, 0.1)',
            borderColor: 'rgb(255, 206, 86)',
            pointBackgroundColor: 'rgb(255, 206, 86)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgb(255, 206, 86)'
        }, {
            label: 'GPT-4-1106',
            data: [88.75, 81.64, 92.00, 89.50, 92.00, 53.53, 72.00, 62.00, 50.00],
            fill: true,
            backgroundColor: 'rgba(75, 192, 192, 0.1)',
            borderColor: 'rgb(75, 192, 192)',
            pointBackgroundColor: 'rgb(75, 192, 192)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgb(75, 192, 192)',
            hidden: true
        }, {
            label: 'OpenFunctions-v2',
            data: [71.67, 88.73, 79.50, 89.50, 78.00, 78.82, 76.00, 74.00, 60.00],
            fill: true,
            backgroundColor: 'rgba(153, 102, 255, 0.1)',
            borderColor: 'rgb(153, 102, 255)',
            pointBackgroundColor: 'rgb(153, 102, 255)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgb(153, 102, 255)'
        }, {
            label: 'GPT-3.5-Turbo',
            data: [68.33, 81.27, 87.50, 88.00, 88.00, 74.12, 70.00, 74.00, 47.50],
            fill: true,
            backgroundColor: 'rgba(255, 159, 64, 0.1)',
            borderColor: 'rgb(255, 159, 64)',
            pointBackgroundColor: 'rgb(255, 159, 64)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgb(255, 159, 64)',
            hidden: true
        }, {
            label: 'Mistral-medium',
            data: [90.00, 80.18, 71.00, 84.50, 68.00, 75.88, 62.00, 72.00, 47.50],
            fill: true,
            backgroundColor: 'rgba(54, 162, 235, 0.1)',
            borderColor: 'rgb(54, 162, 235)',
            pointBackgroundColor: 'rgb(54, 162, 235)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgb(54, 162, 235)',
            hidden: true
        }, {
            label: 'Claude-2.1',
            data: [78.33, 85.64, 72.00, 83.00, 56.50, 61.18, 60.00, 48.00, 45.00],
            fill: true,
            backgroundColor: 'rgba(163, 73, 164, 0.1)',
            borderColor: 'rgb(163, 73, 164)',
            pointBackgroundColor: 'rgb(163, 73, 164)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgb(163, 73, 164)',
            hidden: true
        }, {
            label: 'Mistral-tiny',
            data: [77.08, 59.27, 53.50, 59.50, 41.50, 58.24, 42.00, 64.00, 40.00],
            fill: true,
            backgroundColor: 'rgba(255, 105, 180, 0.1)',
            borderColor: 'rgb(255, 105, 180)',
            pointBackgroundColor: 'rgb(255, 105, 180)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgb(255, 105, 180)',
            hidden: true
        }, {
            label: 'Claude-instant',
            data: [61.67, 68.73, 53.00, 59.00, 39.50, 51.76, 50.00, 52.00, 37.50],
            fill: true,
            backgroundColor: 'rgba(255, 165, 0, 0.1)',
            borderColor: 'rgb(255, 165, 0)',
            pointBackgroundColor: 'rgb(255, 165, 0)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgb(255, 165, 0)',
            hidden: true
        }, {
            label: 'Nexusflow-Raven-v2',
            data: [0.00, 76.55, 39.50, 83.50, 34.00, 45.88, 68.00, 78.00, 45.00],
            fill: true,
            backgroundColor: 'rgba(60, 179, 113, 0.1)',
            borderColor: 'rgb(60, 179, 113)',
            pointBackgroundColor: 'rgb(60, 179, 113)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgb(60, 179, 113)',
            hidden: true
        }, {
            label: 'Mistral-small',
            data: [89.58, 46.55, 48.50, 68.00, 58.00, 14.12, 40.00, 30.00, 37.50],
            fill: true,
            backgroundColor: 'rgba(0, 0, 255, 0.1)',
            borderColor: 'rgb(0, 0, 255)',
            pointBackgroundColor: 'rgb(0, 0, 255)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgb(0, 0, 255)',
            hidden: true
        }, {
            label: 'GPT-4-0613',
            data: [87.08, 74.55, 4.00, 86.00, 0.00, 37.65, 0.00, 50.00, 0.00],
            fill: true,
            backgroundColor: 'rgba(128, 0, 0, 0.1)',
            borderColor: 'rgb(128, 0, 0)',
            pointBackgroundColor: 'rgb(128, 0, 0)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgb(128, 0, 0)',
            hidden: true
        }, {
            label: 'Deepseek-v1.5',
            data: [66.25, 48.36, 35.00, 61.00, 43.50, 5.29, 0.00, 2.00, 7.50],
            fill: true,
            backgroundColor: 'rgba(255, 215, 0, 0.1)',
            borderColor: 'rgb(255, 215, 0)',
            pointBackgroundColor: 'rgb(255, 215, 0)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgb(255, 215, 0)',
            hidden: true
        }, {
            label: 'Glaive-v1',
            data: [46.25, 34.55, 2.00, 26.00, 0.00, 21.18, 0.00, 34.00, 2.50],
            fill: true,
            backgroundColor: 'rgba(64, 224, 208, 0.1)',
            borderColor: 'rgb(64, 224, 208)',
            pointBackgroundColor: 'rgb(64, 224, 208)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgb(64, 224, 208)',
            hidden: true
        }, {
            label: 'OpenFunctions-v0',
            data: [4.58, 60.00, 1.00, 56.00, 2.50, 39.41, 0.00, 62.00, 0.00],
            fill: true,
            backgroundColor: 'rgba(255, 99, 132, 0.1)',
            borderColor: 'rgb(255, 99, 132)',
            pointBackgroundColor: 'rgb(255, 99, 132)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgb(255, 99, 132)',
            hidden: true
        },

    ]
};


new Chart(ctx, {
    type: 'radar',
    data: data,
    options: {
        elements: {
            line: {
                borderWidth: 3
            }
        }
    }
});

var expand = false;
function toggleExpand() {
    // Select all detail-row and detail-header elements
    var elements = document.querySelectorAll('.summary-row, .summary-small-header');

    // Toggle the visibility of each element
    elements.forEach(function (element) {
        if (expand) {
            // Apply the appropriate display style based on the element's tag
            if (element.tagName === 'TR') {
                element.style.display = 'table-row';
            } else if (element.tagName === 'TD' || element.tagName === 'TH') {
                element.style.display = 'table-cell';
            }
        } else {
            element.style.display = 'none'; // Hide element
        }
    });


    // Select all detail-row and detail-header elements
    var elements = document.querySelectorAll('.detail-row, .detail-header, .detail-small-header');

    // Toggle the visibility of each element
    elements.forEach(function (element) {
        if (!expand) {
            // Apply the appropriate display style based on the element's tag
            if (element.tagName === 'TR') {
                element.style.display = 'table-row';
            } else if (element.tagName === 'TD' || element.tagName === 'TH') {
                element.style.display = 'table-cell';
            }
        } else {
            element.style.display = 'none'; // Hide element
        }
    });

    expand = !expand;
}



function sendFeedback(vote) {
    fetch('https://realm.mongodb.com/api/client/v2.0/app/data-onwzq/auth/providers/local-userpass/login', {
        method: 'POST', // Specifies the request method
        headers: {
            'Content-Type': 'application/json', // Sets header to indicate the media type of the resource
        },
        body: JSON.stringify({
            username: "website",
            password: "kl4hL0ZuQqjYOoSl"
        }) // Body of the request
    })
        .then(response => response.json()) // Parses the JSON response
        .then(data => {


            const url = 'https://us-west-2.aws.data.mongodb-api.com/app/data-onwzq/endpoint/data/v1/action/insertOne';
            const accessToken = data.access_token;

            const headers = {
                'Content-Type': 'application/json',
                'Access-Control-Request-Headers': '*',
                'Authorization': `Bearer ${accessToken}`
            };
            var inputText = document.getElementById('input-text').value;
            var funcDef = document.getElementById('input-function').value;
            var temperatureValue = document.getElementById('temperatureSlider').value;
            var model = document.getElementById("model-dropdown").value;
            var codeOutputText = document.getElementById('code-output').innerText;
            var jsonOutputText = document.getElementById('json-output').innerText;

            if (inputText === "" || funcDef === "") {
                alert("Please provide input and function definition to send feedback.")
                return;
            }

            const body = {
                collection: "vote",
                database: "gorilla-feedback",
                dataSource: "gorilla",
                document: {
                    // Define the document to insert
                    prompt: inputText,
                    funcDef: funcDef,
                    temperature: temperatureValue,
                    model: model,
                    codeOutput: codeOutputText,
                    jsonOutput: jsonOutputText,
                    result: vote
                }
            };

            fetch(url, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(body)
            })
                .then(response => response.json())
                .then(data => alert("Feedback Sent Successfully!"))
                .catch(error => console.error('Error:', error));
        })
        .catch(error => console.error('Error:', error)); // Catches and logs any errors

}

function sendFeedbackNegative() {
    sendFeedback("negative");
}

function sendFeedbackPositive() {
    sendFeedback("positive");
}