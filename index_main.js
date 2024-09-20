EXAMPLES = [
    {
        name: "requests.get",
        description: "Sends a GET request to the specified URL.",
        parameters: {
            type: "dict",
            properties: {
                url: {
                    type: "string",
                    description:
                        "The Open-Meteo API provides detailed weather forecasts for any location worldwide. It offers forecasts up to 16 days in advance and also provide past data. The API's response gives weather variables on an hourly basis, such as temperature, humidity, precipitation, wind speed and direction, etc. More information can be found in https://open-meteo.com/en/docs/",
                    default: "https://api.open-meteo.com/v1/forecast",
                },
                headers: {},
                timeout: {
                    type: ["number", "tuple"],
                    description:
                        "How many seconds to wait for the server to send data before giving up.",
                    required: false,
                },
                params: {
                    latitude: {
                        type: "string",
                        description:
                            "Geographical WGS84 coordinates of the location. Multiple coordinates can be comma separated. E.g., &latitude=52.52,48.85&longitude=13.41,2.35. To return data for multiple locations the JSON output changes to a list of structures. CSV and XLSX formats add a column location_id. N is positive, S is negative",
                        required: true,
                    },
                    longitude: {
                        type: "string",
                        description:
                            "Geographical WGS84 coordinates of the location. Multiple coordinates can be comma separated. E is positive, W is negative",
                        required: true,
                    },
                    elevation: {
                        type: "string",
                        description:
                            "The elevation used for statistical downscaling. Per default, a 90 meter digital elevation model is used. You can manually set the elevation to correctly match mountain peaks. If &elevation=nan is specified, downscaling will be disabled and the API uses the average grid-cell height. For multiple locations, elevation can also be comma separated.",
                        required: false,
                    },
                    hourly: {
                        type: "string",
                        description:
                            "A list of weather variables which should be returned. Values can be comma separated, or multiple &hourly= parameters in the URL can be used. Support parameters: temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,pressure_msl,cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,wind_speed_10m,wind_speed_80m,wind_speed_120m,wind_speed_180m,wind_direction_10m,wind_direction_80m,wind_direction_120m,wind_direction_180m,wind_gusts_10m,shortwave_radiation,direct_radiation,direct_normal_irradiance,diffuse_radiation,global_tilted_irradiance,vapour_pressure_deficit,cape,evapotranspiration,et0_fao_evapotranspiration,precipitation,snowfall,precipitation_probability,rain,showers,weather_code,snow_depth,freezing_level_height,visibility,soil_temperature_0cm,soil_temperature_6cm,soil_temperature_18cm,soil_temperature_54cm,soil_moisture_0_to_1cm,soil_moisture_1_to_3cm,soil_moisture_3_to_9cm,soil_moisture_9_to_27cm,soil_moisture_27_to_81cm",
                        required: false,
                    },
                    daily: {
                        type: "string",
                        description:
                            "A list of daily weather variable aggregations which should be returned. Values can be comma separated, or multiple &daily= parameters in the URL can be used. If daily weather variables are specified, parameter timezone is required. Possible values supported temperature_2m_max, temperature_2m_min, apparent_temperature_max, apparent_temperature_min, precipitation_sum, rain_sum, showers_sum, snowfall_sum, precipitation_hours, ,precipitation_probability_max, precipitation_probability_min, precipitation_probability_mean, weather_code,sunrise,sunset,sunshine_duration, daylight_duration, wind_speed_10m_max, wind_gusts_10m_max, wind_direction_10m_dominant,shortwave_radiation_sum,et0_fao_evapotranspiration,uv_index_maxuv_index_clear_sky_max",
                        required: false,
                    },
                    temperature_unit: {
                        type: "string",
                        description:
                            "If fahrenheit is set, all temperature values are converted to Fahrenheit.",
                        required: false,
                        default: "celsius",
                    },
                    wind_speed_unit: {
                        type: "string",
                        description: "Other wind speed units: ms, mph, and kn.",
                        required: false,
                        default: "kmh",
                    },
                    precipitation_unit: {
                        type: "string",
                        description: "Other precipitation amount units: inch.",
                        required: false,
                        default: "mm",
                    },
                    timeformat: {
                        type: "string",
                        description:
                            "If format unixtime is selected, all time values are returned in UNIX epoch time in seconds. Please note that all timestamps are in GMT+0! For daily values with unix timestamps, please apply utc_offset_seconds again to get the correct date.",
                        required: false,
                        default: "iso8601",
                    },
                    timezone: {
                        type: "string",
                        description:
                            "If timezone is set, all timestamps are returned as local-time and data is returned starting at 00:00 local-time. Any time zone name from the time zone database is supported. If auto is set as a time zone, the coordinates will be automatically resolved to the local time zone. For multiple coordinates, a comma separated list of timezones can be specified.",
                        required: false,
                        default: "GMT",
                    },
                    past_days: {
                        type: "integer",
                        description:
                            "If past_days is set, yesterday or the day before yesterday data are also returned.",
                        required: false,
                        default: 0,
                    },
                    forecast_days: {
                        type: "integer",
                        description:
                            "Per default, only 7 days are returned. Up to 16 days of forecast are possible.",
                        required: false,
                        default: 7,
                    },
                    forecast_hours: {
                        type: "integer",
                        description:
                            "Similar to forecast_days, the number of timesteps of hourly data can be controlled.",
                        required: false,
                    },
                    forecast_minutely_15: {
                        type: "integer",
                        description:
                            "The number of timesteps of 15-minutely data can be controlled.",
                        required: false,
                    },
                    past_hours: {
                        type: "integer",
                        description: "the number of timesteps of hourly data controlled",
                        required: false,
                    },
                    past_minutely_15: {
                        type: "integer",
                        description: "the number of timesteps of 15 minute data controlled",
                        required: false,
                    },
                    start_date: {
                        type: "string",
                        description:
                            "The time interval to get weather data. A day must be specified as an ISO8601 date (e.g. 2022-06-30).",
                        required: false,
                    },
                    end_date: { type: "string", description: "", required: false },
                    start_hour: {
                        type: "string",
                        description:
                            "The time interval to get weather data for hourly data. Time must be specified as an ISO8601 date and time (e.g. 2022-06-30T12:00).",
                        required: false,
                    },
                    end_hour: { type: "string", description: "", required: false },
                    start_minutely_15: {
                        type: "string",
                        description: "",
                        required: false,
                    },
                    end_minutely_15: { type: "string", description: "", required: false },
                    models: {
                        type: "list",
                        items: { type: "string" },
                        description:
                            "A list of string, manually select one or more weather models. Per default, the best suitable weather models will be combined.",
                        required: false,
                    },
                    cell_selection: {
                        type: "string",
                        description:
                            "Set a preference how grid-cells are selected. The default land finds a suitable grid-cell on land with similar elevation to the requested coordinates using a 90-meter digital elevation model. sea prefers grid-cells on sea. nearest selects the nearest possible grid-cell.",
                        required: false,
                    },
                    apikey: {
                        type: "string",
                        description:
                            "Only required to commercial use to access reserved API resources for customers. The server URL requires the prefix customer-. See pricing for more information.",
                        required: false,
                    },
                },
                allow_redirects: {
                    type: "boolean",
                    description: "A Boolean to enable/disable redirection.",
                    default: true,
                    required: false,
                },
                auth: {
                    type: "tuple",
                    description: "A tuple to enable a certain HTTP authentication.",
                    default: "None",
                    required: false,
                },
                cert: {
                    type: ["string", "tuple"],
                    description: "A String or Tuple specifying a cert file or key.",
                    default: "None",
                    required: false,
                },
                cookies: {
                    type: "dict",
                    additionalProperties: { type: "string" },
                    description: "Dictionary of cookies to send with the request.",
                    required: false,
                },
                proxies: {
                    type: "dict",
                    additionalProperties: { type: "string" },
                    description: "Dictionary of the protocol to the proxy url.",
                    required: false,
                },
                stream: {
                    type: "boolean",
                    description:
                        "A Boolean indication if the response should be immediately downloaded (False) or streamed (True).",
                    default: false,
                    required: false,
                },
                verify: {
                    type: ["boolean", "string"],
                    description:
                        "A Boolean or a String indication to verify the servers TLS certificate or not.",
                    default: true,
                    required: false,
                },
            },
        },
    },
    {
        name: "requests.get",
        description: "Sends a GET request to the specified URL.",
        parameters: {
            type: "dict",
            properties: {
                url: {
                    type: "string",
                    description:
                        "Geocoding API converting a a pair of latitude and longitude coordinates to human readable addresses",
                    default: "https://geocode.maps.co/reverse",
                },
                headers: {},
                timeout: {
                    type: ["number", "tuple"],
                    description:
                        "How many seconds to wait for the server to send data before giving up.",
                    required: false,
                },
                params: {
                    lat: {
                        type: "number",
                        description: "Latitude of the location to reverse geocode.",
                        required: true,
                    },
                    lon: {
                        type: "number",
                        description: "Longitude of the location to reverse geocode.",
                        required: true,
                    },
                    format: {
                        type: "string",
                        description:
                            "The desired response format. Options include 'xml', 'json', 'jsonv2', 'geojson', 'geocodejson'. Default is 'json'.",
                        required: false,
                    },
                },
                allow_redirects: {
                    type: "boolean",
                    description: "A Boolean to enable/disable redirection.",
                    default: true,
                    required: false,
                },
                auth: {
                    type: "tuple",
                    description: "A tuple to enable a certain HTTP authentication.",
                    default: "None",
                    required: false,
                },
                cert: {
                    type: ["string", "tuple"],
                    description: "A String or Tuple specifying a cert file or key.",
                    default: "None",
                    required: false,
                },
                cookies: {
                    type: "dict",
                    additionalProperties: { type: "string" },
                    description: "Dictionary of cookies to send with the request.",
                    required: false,
                },
                proxies: {
                    type: "dict",
                    additionalProperties: { type: "string" },
                    description: "Dictionary of the protocol to the proxy url.",
                    required: false,
                },
                stream: {
                    type: "boolean",
                    description:
                        "A Boolean indication if the response should be immediately downloaded (False) or streamed (True).",
                    default: false,
                    required: false,
                },
                verify: {
                    type: ["boolean", "string"],
                    description:
                        "A Boolean or a String indication to verify the servers TLS certificate or not.",
                    default: true,
                    required: false,
                },
            },
        },
    },
    {
        name: "requests.get",
        description: "Sends a GET request to the specified URL.",
        parameters: {
            type: "dict",
            properties: {
                url: {
                    type: "string",
                    description:
                        "The Date Nager API provides access holiday information for over 100 countries, including the ability to query for long weekends. It leverages ISO 3166-1 alpha-2 country codes to tailor the search to your specific region of interest. More information can be found in https://date.nager.at/Api",
                    default:
                        "https://date.nager.at/api/v3/LongWeekend/{year}/{countryCode}",
                },
                headers: {},
                timeout: {
                    type: ["number", "tuple"],
                    description:
                        "How many seconds to wait for the server to send data before giving up.",
                    required: false,
                },
                params: {},
                auth: {
                    type: "tuple",
                    description: "A tuple to enable a certain HTTP authentication.",
                    default: "None",
                    required: false,
                },
                cert: {
                    type: ["string", "tuple"],
                    description: "A String or Tuple specifying a cert file or key.",
                    default: "None",
                    required: false,
                },
                cookies: {
                    type: "dict",
                    additionalProperties: { type: "string" },
                    description: "Dictionary of cookies to send with the request.",
                    required: false,
                },
                proxies: {
                    type: "dict",
                    additionalProperties: { type: "string" },
                    description: "Dictionary of the protocol to the proxy url.",
                    required: false,
                },
                stream: {
                    type: "boolean",
                    description:
                        "A Boolean indication if the response should be immediately downloaded (False) or streamed (True).",
                    default: false,
                    required: false,
                },
                verify: {
                    type: ["boolean", "string"],
                    description:
                        "A Boolean or a String indication to verify the servers TLS certificate or not.",
                    default: true,
                    required: false,
                },
            },
        },
    },
];

PROMPTS = [
    "I'm planning a camping trip and I need to know the weather forecast. Can you fetch me the weather data for the campsite located at latitude 35.68 and longitude -121.34 for the next 10 days including daily temperature and precipitation forecasts? Also, I prefer the temperature 2 minute max in Fahrenheit and sum of precipitation in inches.",
    "Can you provide the address for latitude 37.4224764 and longitude -122.0842499 using the Geocoding API?",
    "I'm planning a series of long weekend getaways for the upcoming year and I need to know when they'll occur in my country. Could you fetch me the list of long weekends for Canada in the year 2023? I'd like to integrate this information into my holiday planning app.",
];

// Fetch the header JSON data from the external file
async function fetchHeaderData() {
    try {
        const response = await fetch('./data/forms/formHeaders.json'); // Replace with the path to your JSON file
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('There was a problem fetching the header data:', error);
    }
}

// Function to build the table header dynamically
function buildHeader(formKey, headerData) {
    const tableHead = document.getElementById('leaderboard-head');
    const form = headerData.forms[formKey];
    form.rows.forEach(row => {
        const tr = document.createElement('tr');
        row.columns.forEach(col => {
            const th = document.createElement('th');
            if (col.class) th.className = col.class;
            if (col.colspan) th.colSpan = col.colspan;
            if (col.id) th.id = col.id;
            th.textContent = col.content;

            if (col.canExpand) {
                const button = document.createElement('button');
                button.className = 'toggle-button';
                button.setAttribute('data-target', col.id);
                button.setAttribute('data-expanded', 'true');
                // Add Font Awesome left arrow for collapse by default
                button.innerHTML = '<i class="fas fa-chevron-left"></i>';
                th.appendChild(button);
            }

            tr.appendChild(th);
        });
        tableHead.appendChild(tr);
    });
}

// Load the table header once the JSON data is fetched
async function init(datasetName) {

    const csvFilePath = `./data_${datasetName}.csv`;

    const headerData = await fetchHeaderData();
    if (headerData) {
        buildHeader(datasetName, headerData); // Build the header for form1
    }
    fetch(csvFilePath)
        .then((response) => response.text())
        .then((csvText) => {
            const leaderboard_data = parseCSV_leaderboard(csvText, datasetName);
            addToTable(leaderboard_data);
            document.querySelectorAll('.toggle-button').forEach(button =>
                {
                    button.click()
                }
            )
            document.getElementById("rank-col").click(); // Sort by rank by default
        })
        .catch((error) => console.error(error));
    fetch(csvFilePath)
        .then((response) => response.text())
        .then((csvText) => {
            const chart_data = parseCSV_chart(csvText, datasetName);
            generateChart(chart_data);
        })
        .catch((error) => console.error(error));
    
    document.getElementById("example-btn-1").addEventListener("click", function () {
        populateInput(0);
    });
    document.getElementById("example-btn-2").addEventListener("click", function () {
        populateInput(1);
    });
    document.getElementById("example-btn-3").addEventListener("click", function () {
        populateInput(2);
    });

    document
        .getElementById("submit-btn")
        .addEventListener("click", async function () {
            var inputText = document.getElementById("input-text").value;
            var inputFunction = document.getElementById("input-function").value; // Assuming you have an input field with this id for the function
            var temperatureValue = document.getElementById("temperatureSlider").value;
            var model = document.getElementById("model-dropdown").value;

            if (inputText === "" || inputFunction === "") {
                alert("Please provide input and function definition.");
                return;
            }

            document.getElementById("code-output").innerText =
                "Loading Model Response...";
            document.getElementById("json-output").innerText =
                "Loading Model Response...";

            const requestData = {
                model: model,
                messages: [{ role: "user", content: inputText }],
                functions: [inputFunction],
                temperature: parseFloat(temperatureValue),
            };

            const response = await fetch(
                "https://luigi.millennium.berkeley.edu:443/v1/chat/completions",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: "EMPTY",
                    },
                    body: JSON.stringify(requestData),
                }
            );

            if (!response.ok) {
                document.getElementById("code-output").innerText =
                    "Error: " + response.status;
                return;
            }

            const jsonResponse = await response.json();

            if (model === "gorilla-openfunctions-v2") {
                directCode = jsonResponse.choices[0].message.content;
                jsonCode = jsonResponse.choices[0].message.function_call;
                document.getElementById("code-output").innerText = directCode;
                if (jsonCode) {
                    jsonCode = JSON.stringify(jsonCode, null, 2); // Pretty print the JSON
                    document.getElementById("json-output").innerText = jsonCode;
                } else {
                    document.getElementById("json-output").innerText =
                        "Error parsing JSON output.";
                }
            } else {
                jsonCode = jsonResponse.choices[0].message.function_call;
                jsonCode = JSON.stringify(jsonResponse, null, 2); // Pretty print the JSON
                document.getElementById("json-output").innerText = jsonCode;
                document.getElementById("code-output").innerText =
                    "Model does not support direct code output.";
            }

            // const executeButton = document.getElementById('exec-btn');
            // executeButton.style.display = 'block'; // Ensure the button is visible after receiving a response
            // executeButton.addEventListener('click', function () {
            //     window.open("https://star-history.com/#ShishirPatil/gorilla&gorilla-llm/gorilla-cli")
            // });
            document.getElementById("thumbs-up-btn").style.display = "block";
            document.getElementById("thumbs-down-btn").style.display = "block";
            document.getElementById("report-issue-btn").style.display = "block";
        });

    document
        .getElementById("report-issue-btn")
        .addEventListener("click", function () {
            var inputText = document.getElementById("input-text").value;
            var funcDef = document.getElementById("input-function").value;
            var temperatureValue = document.getElementById("temperatureSlider").value;
            var model = document.getElementById("model-dropdown").value;
            var codeOutputText = document.getElementById("code-output").innerText;
            var jsonOutputText = document.getElementById("json-output").innerText;
            if (inputText === "" || funcDef === "") {
                alert("Please provide input and function definition to send feedback.");
                return;
            }
            var issueTitle = "[bug] OpenFunctions-v2: ";
            var issueBody = `**Issue Description**%0A%0APrompt: ${inputText}%0A%0AModel: ${model}%0A%0ATemperature: ${temperatureValue}%0A%0AOutput (or Error if request failed): %0A%0A ${codeOutputText} %0A%0A ${jsonOutputText}%0A%0A**Additional Information**\n`;
            window.open(
                `https://github.com/ShishirPatil/gorilla/issues/new?assignees=&labels=hosted-openfunctions-v2&projects=&template=hosted-openfunctions-v2.md&title=${issueTitle}&body=${issueBody}`,
                "_blank"
            );
        });

    document.querySelectorAll("th.column-header").forEach(function (header, index) {

        var sortIndicator = document.createElement("span");
        header.appendChild(sortIndicator);

        header.addEventListener("click", function () {
            var table = header.closest("table");
            var tbody = table.querySelector("tbody");
            var columnIndex = Array.from(header.parentNode.children).indexOf(header);
            var isAscending = (header.asc = !header.asc);

            sortIndicator.textContent = isAscending ? " 🔼" : " 🔽";

            document.querySelectorAll("th span").forEach(function (otherIndicator) {
                if (otherIndicator !== sortIndicator) {
                    otherIndicator.textContent = ""; // Clear other indicators
                }
            });

            var rowsArray = Array.from(tbody.querySelectorAll("tr"));
            rowsArray
                .sort(createComparer(columnIndex, isAscending))
                .forEach(function (row) {
                    tbody.appendChild(row);
                });
            
            updateStickyColumnsLeft()
        });
    });

    // Add Expand/Collapse Event Click Listener to All Expandable Buttons
    document.querySelectorAll('.toggle-button').forEach(button => {
        button.addEventListener('click', function() {
            const target = button.getAttribute('data-target');
            const isExpanded = button.getAttribute('data-expanded') === 'true';
            
            // Get the target subheaders and the main header
            const subHeaderRows = document.getElementsByClassName(`${target}-sub-header`);
            const mainHeaders = document.getElementsByClassName(`${target}-header`);
            
            // Ensure there are elements found
            if (mainHeaders.length === 0 || subHeaderRows.length === 0) {
                console.error('No elements found for target:', target);
                return;
            }

            // Access the first element from the collections
            const mainHeader = mainHeaders[0];
            
            if (isExpanded) {
                // Collapse: Reduce colspan and hide subheaders
                mainHeader.setAttribute('colspan', 1);

                // Select all sub headers
                const allSubheaders = document.querySelectorAll(`.${target}-sub-header`);
                
                // Select all sub cells
                const allSubCells = document.querySelectorAll(`.${target}-sub-cell`);
                
                // Combine the NodeLists into a single array
                const allElements = [...allSubheaders, ...allSubCells];
                
                // Set display to 'none' for each element
                allElements.forEach(element => {
                    if (!element.className.includes("stay")) {
                        element.style.display = 'none';
                    }
                });

                const topHeader = document.querySelectorAll(`.${target}-top-header`)[0];

                // Get the current colspan value (returns a string, so we need to convert it to a number)
                let currentColspan = parseInt(topHeader.getAttribute('colspan'));
                
                // Modify the colspan by adding or subtracting the change value
                const newColspan = currentColspan - (allSubheaders.length - 1);
                
                // Ensure the colspan is not less than 1 (colspan cannot be zero or negative)
                topHeader.setAttribute('colspan', Math.max(1, newColspan));

                // Collapse: change icon to right arrow
                button.innerHTML = '<i class="fas fa-chevron-right"></i>';
            } else {
                // Expand: Set colspan and show subheaders
                const originalColspan = subHeaderRows.length;
                mainHeader.setAttribute('colspan', originalColspan);
                

                // Select all sub headers
                const allSubheaders = document.querySelectorAll(`.${target}-sub-header`);
                
                // Select all sub cells
                const allSubCells = document.querySelectorAll(`.${target}-sub-cell`);
                
                // Combine the NodeLists into a single array
                const allElements = [...allSubheaders, ...allSubCells];
                
                // Set display to 'true' for each element
                allElements.forEach(element => {
                    element.style.display = '';
                });


                const topHeader = document.querySelectorAll(`.${target}-top-header`)[0];

                // Get the current colspan value (returns a string, so we need to convert it to a number)
                let currentColspan = parseInt(topHeader.getAttribute('colspan'));
                
                // Modify the colspan by adding or subtracting the change value
                const newColspan = currentColspan + (allSubheaders.length - 1);
                
                // Ensure the colspan is not less than 1 (colspan cannot be zero or negative)
                topHeader.setAttribute('colspan', Math.max(1, newColspan));

                // Expand: change icon to left arrow
                button.innerHTML = '<i class="fas fa-chevron-left"></i>';
            }

            // Toggle the state
            button.setAttribute('data-expanded', !isExpanded);
        });
    });
}

// Initialize the table header creation when the page loads
document.addEventListener('DOMContentLoaded', init("combined_Sep_20_2024"));


function parseCSV_leaderboard(text, datasetName) {
    result = text.split("\n");
    // Skip the first row of the CSV (headers)
    for (let i = 1; i < result.length; i += 1) {
        result[i] = result[i].split(",");
        result[i] = result[i].map((value) => {
            if (value.endsWith("%")) {
                return parseFloat(value.slice(0, -1));
            }
            return value;
        });
        // if (datasetName == "combined") {
        //     result[i].splice(result[i].length, 0, result[i][4]);
        //     result[i].splice(result[i].length, 0, result[i][5]);
        //     result[i].splice(4, 2);
        //     result[i].splice(4, 0, result[i][result[i].length - 6]);
        //     result[i].splice(5, 0, result[i][result[i].length - 5]);
        //     result[i].splice(8, 0, result[i][result[i].length - 8]);
        //     result[i].splice(9, 0, result[i][result[i].length - 7]);
        //     result[i].splice(10, 0, result[i][result[i].length - 6]);
        //     result[i].splice(11, 0, result[i][result[i].length - 5]);
        //     result[i].splice(12, 0, result[i][result[i].length - 4]);
        //     result[i].splice(13, 0, result[i][result[i].length - 3]);
        //     result[i].splice(result[i].length - 6, 4);
        // } else if (datasetName == "live") {
        //     result[i].splice(result[i].length, 0, result[i][4]);
        //     result[i].splice(result[i].length, 0, result[i][5]);
        //     result[i].splice(4, 2);
        //     result[i].splice(4, 0, result[i][result[i].length - 6]);
        //     result[i].splice(5, 0, result[i][result[i].length - 5]);
        //     result[i].splice(7, 0, result[i][result[i].length - 8]);
        //     result[i].splice(8, 0, result[i][result[i].length - 7]);
        //     result[i].splice(9, 0, result[i][result[i].length - 6]);
        //     result[i].splice(10, 0, result[i][result[i].length - 5]);
        //     result[i].splice(11, 0, result[i][result[i].length - 4]);
        //     result[i].splice(12, 0, result[i][result[i].length - 3]);
        //     result[i].splice(result[i].length - 6, 4);
        // }
    }
    console.log(result)
    return result;
}

function parseCSV_chart(text) {
    result = text.split("\n");
    // Skip the first row of the CSV (headers)
    for (let i = 1; i < result.length; i += 1) {
        result[i] = result[i].split(",");
        result[i] = result[i].map((value) => {
            if (value.endsWith("%")) {
                return parseFloat(value.slice(0, -1));
            }
            return value;
        });
    }
    return result;
}

function addToTable(dataArray) {
    const tbody = document
        .getElementById("leaderboard-table")
        .getElementsByTagName("tbody")[0];
    dataArray.forEach((row, index) => {
        // Assuming the first row of the CSV is headers and skipping it
        if (index > 0) {
            const tr = document.createElement("tr");

            for (let cellIndex = 0; cellIndex < row.length; cellIndex += 1) {
                let cell = row[cellIndex];
                const td = document.createElement("td");
                if (cellIndex === 2) {
                    const a = document.createElement("a");
                    a.href = row[3];
                    cellIndex += 1;
                    a.textContent = cell;
                    td.appendChild(a);
                } else {
                    td.textContent = cell;
                }

                if (cellIndex >= 6 && cellIndex <= 7) {
                    // class for specific columns
                    td.className = "latency-sub-cell";
                } else if (cellIndex >= 9 && cellIndex <= 12) {
                    // class for specific columns
                    td.className = "nonliveast-sub-cell";
                } else if (cellIndex >= 14 && cellIndex <= 17) {
                    // class for specific columns
                    td.className = "nonliveexec-sub-cell";
                } else if (cellIndex >= 19 && cellIndex <= 22) {
                    // class for specific columns
                    td.className = "liveast-sub-cell";
                } else if (cellIndex >= 24 && cellIndex <= 28) {
                    // class for specific columns
                    td.className = "multiturn-sub-cell";
                }

                tr.appendChild(td);
            }

            tbody.appendChild(tr);
        }
    });
}

function populateInput(index) {
    document.getElementById("input-text").value = PROMPTS[index];
    document.getElementById("input-function").value = JSON.stringify(
        EXAMPLES[index],
        null,
        2
    );
}

const scriptURL =
    "https://script.google.com/macros/s/AKfycbxdAKyEA36HA_p0k3KwMzMigxgFCZ1XegRBPfjgxlNaOK2CsOnP9hrEV_6V1ARCAJw3vw/exec";
const form = document.forms["submit-to-google-sheet"];
const msg = document.getElementById("msg");
form.addEventListener("submit", (e) => {
    e.preventDefault(); // Prevents default refresh by the browser
    fetch(scriptURL, { method: "POST", body: new FormData(form) })
        .then((response) => {
            console.log("Success!", response);
            msg.innerHTML =
                "<span style='color: black;'>Message Sent Successfully!</span>";
            setTimeout(function () {
                msg.innerHTML = "";
            }, 5000);
            // form.reset()
        })
        .catch((error) => console.error("Error!", error.message));
});

const shown_model_list = [
    "Claude-3.5-Sonnet-20240620 (FC)",
    "Gorilla-OpenFunctions-v2 (FC)",
];
const color = [
    "rgb(255, 99, 132)",
    "rgb(54, 162, 235)",
    "rgb(255, 215, 0)",
    "rgb(153, 102, 255)",
    "rgb(85, 207, 47)",
    "rgb(0, 0, 255)",
    "rgb(64, 224, 208)",
    "rgb(192, 0, 0)",
    "rgb(47, 79, 79)",   
    "rgb(255, 140, 0)",  
    "rgb(75, 192, 192)",
    "rgb(255, 206, 86)",
    "rgb(54, 162, 235)",
    "rgb(255, 165, 0)",
    "rgb(65, 105, 225)",
    "rgb(75, 192, 192)",
    "rgb(255, 206, 86)",
    "rgb(128, 0, 0)",
    "rgb(185, 157, 47)",
    "rgb(163, 73, 164)",
    "rgb(255, 105, 180)",
    "rgb(60, 179, 113)",
    "rgb(218, 112, 214)",
    "rgb(85, 157, 147)",
    "rgb(255, 99, 132)",
    "rgb(0, 255, 255)",
    "rgb(85, 107, 47)",
    "rgb(0, 128, 128)",
    "rgb(255, 0, 255)",
    "rgb(0, 100, 0)",    
    "rgb(139, 0, 139)",  
    "rgb(255, 69, 0)",   
    "rgb(0, 191, 255)",  
    "rgb(255, 20, 147)",  
    "rgb(210, 105, 30)", 
    "rgb(144, 238, 144)",
    "rgb(70, 130, 180)", 
    "rgb(244, 164, 96)", 
    "rgb(255, 228, 196)",
    "rgb(0, 255, 127)",  
    "rgb(216, 191, 216)",
    "rgb(255, 239, 213)",
    "rgb(219, 112, 147)",
    "rgb(255, 250, 205)",
    "rgb(0, 206, 209)",  
    "rgb(148, 0, 211)",  
    "rgb(240, 230, 140)",
    "rgb(75, 0, 130)",
    "rgb(34, 139, 34)",
    "rgb(210, 180, 140)",
    "rgb(255, 182, 193)",
    "rgb(123, 104, 238)",
    "rgb(255, 160, 122)",
    "rgb(245, 222, 179)",
    "rgb(255, 218, 185)",
    "rgb(199, 21, 133)", 
    "rgb(238, 232, 170)",
    "rgb(176, 196, 222)",
    "rgb(255, 228, 225)",
    "rgb(135, 206, 250)",
    "rgb(240, 128, 128)",
    "rgb(102, 205, 170)",
    "rgb(255, 160, 122)",
    "rgb(72, 61, 139)",
    "rgb(173, 216, 230)",
    "rgb(216, 191, 216)",
    "rgb(221, 160, 221)",
    "rgb(250, 128, 114)",
    "rgb(233, 150, 122)",
    "rgb(127, 255, 212)",
    "rgb(219, 112, 147)",
    "rgb(188, 143, 143)",
    "rgb(233, 30, 99)",
    "rgb(255, 87, 34)",
    "rgb(76, 175, 80)",
    "rgb(255, 193, 7)",
    "rgb(96, 125, 139)",
    "rgb(103, 58, 183)",
    "rgb(3, 169, 244)",
    "rgb(0, 188, 212)",
    "rgb(205, 220, 57)",
    "rgb(139, 195, 74)",
    "rgb(0, 150, 136)",
    "rgb(33, 150, 243)",
    "rgb(63, 81, 181)",
    "rgb(121, 85, 72)",
    "rgb(156, 39, 176)",
    "rgb(255, 235, 59)",
    "rgb(158, 158, 158)",
    "rgb(224, 64, 251)",
    "rgb(244, 67, 54)",
    "rgb(255, 152, 0)",
    "rgb(233, 30, 99)",
    "rgb(124, 179, 66)",
    "rgb(255, 238, 88)",
    "rgb(230, 126, 34)",
    "rgb(93, 64, 55)",
    "rgb(233, 30, 99)",
    "rgb(76, 175, 80)",
    "rgb(63, 81, 181)",
    "rgb(255, 87, 34)",
    "rgb(96, 125, 139)",
    "rgb(158, 158, 158)",
    "rgb(230, 74, 25)",
    "rgb(0, 77, 64)",
    "rgb(156, 39, 176)",
    "rgb(123, 31, 162)",
    "rgb(255, 193, 7)",
    "rgb(245, 0, 87)",
];

function convertRGBtoRGBA(rgbString) {
    const rgbValues = rgbString.match(/\d+/g);
    return `rgba(${rgbValues.join(", ")}, 0.1)`;
}

let availableDatasets = [];
let myChart = null;
const datasetDropdown = $('#dataset-dropdown');

// Function to determine font size based on screen width
function getFontSize() {
    const screenWidth = window.innerWidth;
    if (screenWidth < 480) {
        return 8.5;  // Small font size for small screens
    } else if (screenWidth < 768) {
        return 10;  // Medium font size for medium screens
    } else {
        return 15;  // Default font size for larger screens
    }
}

function generateChart(csvData) {
    var dataset = [];
    for (let i = 1; i < csvData.length; i += 1) {
        var row = csvData[i];
        var model_name = row[2];

        var dataPoint = {
            label: model_name,
            data: [
                csvData[i][1],
                csvData[i][8],
                csvData[i][13],
                csvData[i][18],
                csvData[i][23],
                csvData[i][30],
            ],
            fill: true,
            backgroundColor: convertRGBtoRGBA(color[i - 1]),
            borderColor: color[i - 1],
            pointBackgroundColor: color[i - 1],
            pointBorderColor: "#fff",
            pointHoverBackgroundColor: "#fff",
            pointHoverBorderColor: color[i - 1],
        };
        dataset.push(dataPoint);
    }

    const data = {
        labels: [
            "Overall Accuracy",
            "Non-live AST Summary",
            "Non-live Exec Summary",
            "Live Summary",
            "Multi Turn Summary",
            "Hallucination Measurement",
        ],
        datasets: dataset,
    };

    availableDatasets = [...data.datasets];

    const ctx = document.getElementById('myChart').getContext('2d');

    myChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: data.labels,
            datasets: []
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,  // Allow the chart to adjust its aspect ratio
            elements: {
                line: {
                    borderWidth: 3,
                },
            },
            scales: {
                r: {
                    beginAtZero: true,
                    pointLabels: {
                        font: {
                            size: getFontSize()  // Adjust font size dynamically
                        }
                    },
                    ticks: {
                        display: true,
                        font: {
                            size: getFontSize()  // Adjust ticks font size dynamically
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top', // Ensure legend is at the top
                    labels: {
                        boxWidth: 15,
                        font: {
                            size: Math.min(getFontSize() + 3.5, 15) // Allow labels to adjust in size if needed
                        },
                        padding: 20, // Provide padding around labels to avoid crowding
                        usePointStyle: true, // Use point style to differentiate items
                    },
                    fullSize: true // Allow legend to take full width if needed
                }
            }
        }
    });

    // Initialize Semantic UI dropdown
    datasetDropdown.dropdown({
        onChange: function (value, text, $selectedItem) {
            handleDatasetSelection(value);
        }
    });

    // Populate the dropdown menu with datasets initially
    populateDropdown();

    // Resize chart font size on window resize
    window.addEventListener('resize', function () {
        // Update font sizes dynamically on screen resize
        myChart.options.scales.r.pointLabels.font.size = getFontSize();
        myChart.options.scales.r.ticks.font.size = getFontSize();
        myChart.options.plugins.legend.labels.font.size = getFontSize();
        myChart.update();  // Update the chart to reflect changes
    });
}

// Handle Clear All button click
$('#clear-all-btn').on('click', function () {
    // Clear the chart datasets
    myChart.data.datasets = [];
    myChart.update();

    // Clear the dropdown selection
    datasetDropdown.dropdown('clear');
});

// Populate the dropdown with dataset options
function populateDropdown() {
    availableDatasets.forEach((dataset, index) => {
        const item = `<div class="item" data-value="${index}">${dataset.label}</div>`;
        datasetDropdown.find('.menu').append(item);
    });

    // Initialize the dropdown and trigger change event
    datasetDropdown.dropdown({
        fullTextSearch: 'exact',  // Enables full substring matching
        onChange: function (value) {
            handleDatasetSelection(value);
        },
        // Custom search function for substring matching
        filterRemoteData: true,
        matcher: function (searchTerm, item) {
            return item.text.toLowerCase().includes(searchTerm.toLowerCase());
        }
    });
    
    // Pre-select datasets by label (finding the correct indices)
    const defaultSelectedIndices = availableDatasets
        .map((dataset, index) => shown_model_list.includes(dataset.label) ? index.toString() : null)
        .filter(index => index !== null);

    // Set the selected datasets in the dropdown
    datasetDropdown.dropdown('set exactly', defaultSelectedIndices);
}

// Handle dataset selection and removal
function handleDatasetSelection(value) {
    // Get the currently selected datasets
    const selectedIndices = datasetDropdown.dropdown('get value').split(',');

    // Clear the current datasets in the chart.
    myChart.data.datasets = [];

    // Add the selected datasets to the chart
    selectedIndices.forEach((index, count) => {
        if (index) {
            const dataset = availableDatasets[parseInt(index)];
            dataset.backgroundColor = convertRGBtoRGBA(color[count]);
            dataset.borderColor = color[count];
            dataset.pointBackgroundColor = color[count];
            dataset.pointHoverBorderColor = color[count];
            myChart.data.datasets.push(dataset);
        }
    });

    // Update the chart with the new datasets
    myChart.update();
}


// Note: If we have too many models, we can use the following code to add a plugin to automatically color the radar chart, but the color quality is not as good as the current one.

// const autocolors = window['chartjs-plugin-autocolors'];
// Chart.register(autocolors);

// function convertColorToRGBAWithAlpha(color) {
//     return Chart.helpers.color(color).alpha(0.15).rgbString();
// }

// new Chart(ctx, {
//     type: 'radar',
//     data: data,
//     options: {
//         elements: {
//             line: {
//                 borderWidth: 3
//             }
//         },
//         plugins: {
//             autocolors: {
//                 customize(context) {
//                     const colors = context.colors;
//                     return {
//                         background: convertColorToRGBAWithAlpha(colors.background),
//                         border: colors.border
//                     };
//                 },
//                 mode: 'label'
//             }
//         },
//     }
// });

var expand = false;
function toggleExpand() {
    // Select all detail-row and detail-header elements
    var elements = document.querySelectorAll(
        ".summary-row, .summary-small-header"
    );

    // Toggle the visibility of each element
    elements.forEach(function (element) {
        if (expand) {
            // Apply the appropriate display style based on the element's tag
            if (element.tagName === "TR") {
                element.style.display = "table-row";
            } else if (element.tagName === "TD" || element.tagName === "TH") {
                element.style.display = "table-cell";
            }
        } else {
            element.style.display = "none"; // Hide element
        }
    });

    // Select all detail-row and detail-header elements
    var elements = document.querySelectorAll(
        ".detail-row, .detail-header, .detail-small-header"
    );

    // Toggle the visibility of each element
    elements.forEach(function (element) {
        if (!expand) {
            // Apply the appropriate display style based on the element's tag
            if (element.tagName === "TR") {
                element.style.display = "table-row";
            } else if (element.tagName === "TD" || element.tagName === "TH") {
                element.style.display = "table-cell";
            }
        } else {
            element.style.display = "none"; // Hide element
        }
    });

    expand = !expand;
}

function sendFeedback(vote) {
    fetch(
        "https://us-west-2.aws.realm.mongodb.com/api/client/v2.0/app/data-onwzq/auth/providers/local-userpass/login",
        {
            method: "POST", // Specifies the request method
            headers: {
                "Content-Type": "application/json", // Sets header to indicate the media type of the resource
            },
            body: JSON.stringify({
                username: "website",
                password: "kl4hL0ZuQqjYOoSl",
            }), // Body of the request
        }
    )
        .then((response) => response.json()) // Parses the JSON response
        .then((data) => {
            const url =
                "https://us-west-2.aws.data.mongodb-api.com/app/data-onwzq/endpoint/data/v1/action/insertOne";
            const accessToken = data.access_token;

            const headers = {
                "Content-Type": "application/json",
                "Access-Control-Request-Headers": "*",
                Authorization: `Bearer ${accessToken}`,
            };
            var inputText = document.getElementById("input-text").value;
            var funcDef = document.getElementById("input-function").value;
            var temperatureValue = document.getElementById("temperatureSlider").value;
            var model = document.getElementById("model-dropdown").value;
            var codeOutputText = document.getElementById("code-output").innerText;
            var jsonOutputText = document.getElementById("json-output").innerText;

            if (inputText === "" || funcDef === "") {
                alert("Please provide input and function definition to send feedback.");
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
                    result: vote,
                },
            };

            fetch(url, {
                method: "POST",
                headers: headers,
                body: JSON.stringify(body),
            })
                .then((response) => response.json())
                .then((data) => alert("Feedback Sent Successfully!"))
                .catch((error) => console.error("Error:", error));
        })
        .catch((error) => console.error("Error:", error)); // Catches and logs any errors
}

function sendFeedbackNegative() {
    sendFeedback("negative");
}

function sendFeedbackPositive() {
    sendFeedback("positive");
}

function getCellValue(row, columnIndex) {
    return (
        row.children[columnIndex].innerText || row.children[columnIndex].textContent
    );
}

function createComparer(columnIndex, isAscending) {

    return function (rowA, rowB) {
        var valueA = getCellValue(isAscending ? rowA : rowB, columnIndex);
        var valueB = getCellValue(isAscending ? rowB : rowA, columnIndex);

        if (valueA !== "" && valueB !== "" && !isNaN(valueA) && !isNaN(valueB)) {
            return valueA - valueB; // Numeric comparison
        } else {
            return valueA.toString().localeCompare(valueB); // String comparison
        }
    };
}

$(document).ready(function() {
    // Initialize the dropdown with a focus on proper search input handling
    $('#dataset-dropdown').dropdown({
        fullTextSearch: true, // Enables substring search
        onShow: function() {
            // Attach event listener to the input field to dynamically adjust width
            const searchInput = $('.ui.dropdown .menu .search input');
            searchInput.off('input'); // Remove existing listeners to avoid duplication
            searchInput.on('input', function() {
                console.log('Input event triggered'); // Debug to ensure event fires
                $(this).css('width', 'auto'); // Reset width to calculate based on content
                const inputWidth = this.scrollWidth; // Calculate necessary width
                $(this).css('width', inputWidth + 'px'); // Adjust to new width
            });
        },
        onChange: function(value, text, $selectedItem) {
            console.log('Dropdown value changed: ', value); // Debug to ensure changes are detected
        }
    });
});

function updateStickyColumnsLeft() {
    
    const firstColumn = document.querySelector('#leaderboard tbody td:nth-child(1)');
    const secondColumn = document.querySelector('#leaderboard tbody td:nth-child(2)');
    
    if (firstColumn && secondColumn) {
        console.log("called")
        const firstColumnWidth = firstColumn.getBoundingClientRect().width;
        const secondColumnWidth = secondColumn.getBoundingClientRect().width;

        const secondColumnCells = document.querySelectorAll('#leaderboard tbody td:nth-child(2), #leaderboard thead .sticky-second-column:nth-child(2)');
        const thirdColumnCells = document.querySelectorAll('#leaderboard tbody td:nth-child(3), #leaderboard thead .sticky-second-column:nth-child(3)');
        
        // Update the left position of the second column
        secondColumnCells.forEach(cell => {
            cell.style.left = `${firstColumnWidth}px`;
        });

        // Update the left position of the third column
        thirdColumnCells.forEach(cell => {
            cell.style.left = `${firstColumnWidth + secondColumnWidth}px`;
        });
    }
}

