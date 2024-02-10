// Utility functions
function getElement(selector) {
  return document.getElementById(selector);
}

function toggleSpinner(visible) {
  const spinner = getElement("loading-spinner");
  spinner.style.visibility = visible ? "visible" : "hidden";
}

function performConversion(option2Data) {
  fetch("/convert", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(option2Data),
  })
    .then((response) => response.json())
    .then((option1Data) => {
      getElement("option1Output").value = JSON.stringify(option1Data, null, 2);
      toggleSpinner(false);
    })
    .catch((error) => {
      console.error("Error:", error);
      toggleSpinner(false);
    });
}

// Validate Option 2 JSON structure
function validateOption2JSON(jsonInput) {
  const requiredFields = [
    { key: "user_name", type: "string" },
    { key: "api_name", type: "string", maxLength: 50 },
    { key: "api_url", type: "string" },
  ];

  requiredFields.forEach((field) => {
    if (
      typeof jsonInput[field.key] !== field.type ||
      (field.maxLength && jsonInput[field.key].length > field.maxLength)
    ) {
      throw new Error(
        `The "${field.key}" field is missing, not a ${field.type}, or exceeds length limits.`
      );
    }
  });

  return true;
}

// Event listeners setup
function setupEventListeners() {
  getElement("convertButton").addEventListener("click", () => {
    toggleSpinner(true);
    const option2Json = getElement("option2Input").value;

    try {
      const option2Data = JSON.parse(option2Json);
      validateOption2JSON(option2Data);
      performConversion(option2Data);
    } catch (e) {
      alert("Invalid JSON: \n" + e.message);
      toggleSpinner(false);
    }
  });

  getElement("editButton").addEventListener("click", () => {
    const option1Output = getElement("option1Output");
    option1Output.removeAttribute("readonly");
    option1Output.focus();
    option1Output.addEventListener(
      "blur",
      () => option1Output.setAttribute("readonly", true),
      { once: true }
    );
  });

  getElement("copyButton").addEventListener("click", () => {
    const option1Output = getElement("option1Output");
    option1Output.select();
    document.execCommand("copy");
  });

  getElement("submitPR").addEventListener("click", () => {
    const option1Content = getElement("option1Output").value;
    option1JSON = JSON.parse(option1Content);
    makePullRequest(option1JSON);
  });
}

function makePullRequest(option1JSON) {
  fetch("/pullrequest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(option1JSON),
  })
    .then((response) => response.json())
    .then((data) => alert("Pull request submitted successfully"))
    .catch((error) => console.error("Error:", error));
}

setupEventListeners();
