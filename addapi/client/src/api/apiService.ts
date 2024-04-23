import { ConvertResult, ConvertedURL } from "../types/types";

// apiService.js
const VIRTUAL_API_BASE = "/api";
const BACKEND_URL = "http://34.133.163.39/addapi/";
// const BACKEND_URL = "http://localhost:8080/";
const GITHUB_CLIENT_ID = "752573cfa527a1b392ad";

export const convertUrls = async (
  username: string,
  apiName: string,
  urls: string[]
): Promise<ConvertResult> => {
  try {
    const response = await fetch(`${VIRTUAL_API_BASE}/convert`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        user_name: username,
        api_name: apiName,
        api_urls: urls,
      }),
    });

    if (!response.ok) {
      throw new Error(`Error: ${response.status}`);
    }
    const data: ConvertResult = await response.json();
    return data;
  } catch (error) {
    console.error("Failed to convert URLs:", error);
    throw error; // Rethrow the error to be handled by the caller
  }
};

export const raisePullRequest = async (
  username: string,
  urlResults: ConvertResult
) => {
  // Helper function to validate urlResults
  function isValidUrlResults(urlResults: ConvertResult): boolean {
    return Object.values(urlResults).some(
      (result) => result.status === "success"
    );
  }
  const accessToken = localStorage.getItem("accessToken");
  if (!accessToken) {
    alert("Please login to Github to raise a pull request");
    return;
  }
  if (!username || !isValidUrlResults(urlResults)) {
    alert(
      "Please enter a username and at least one urlResult must be successful to raise a pull request"
    );
    return;
  }
  try {
    const response = await fetch(`${VIRTUAL_API_BASE}/raise-pr`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      credentials: "include",
      body: JSON.stringify({
        user_name: username,
        api_urls: urlResults,
      }),
    });
    if (response.ok) {
      const result = await response.json();
      // Redirect the user to GitHub comparison page
      window.location.href = result.compare_url;
    } else {
      const errorDetails = await response.text();
      throw new Error(
        `HTTP error! status: ${response.status}, details: ${errorDetails}`
      );
    }
  } catch (error) {
    console.error("Failed to raise a pull request:", error);
    throw error; // rethrow to handle this error further up the call stack
  }
};

export const reportIssue = (url: string, result: ConvertedURL) => {
  const title = "Conversion Error for API URL";
  const description = `
**Issue Description:** There was an issue converting the provided URL to the desired format.
**URL:** ${url}
**Conversion Result:**
\`\`\`json
${JSON.stringify(result, null, 2)}
\`\`\`
Please investigate the conversion process for potential issues.
  `.trim();

  const issueUrl = new URL(
    "https://github.com/ShishirPatil/gorilla/issues/new"
  );
  issueUrl.searchParams.append("title", title);
  issueUrl.searchParams.append("body", description);
  issueUrl.searchParams.append("labels", "conversion-error,apibench-data");

  window.open(issueUrl.toString(), "_blank");
};

export async function getAccessToken(codeParam: string) {
  try {
    const response = await fetch(
      `${VIRTUAL_API_BASE}/get-access-token?code=${codeParam}`, {
        method: "GET",
      }
    );
    const data = await response.json();
    if (data.access_token) {
      localStorage.setItem("accessToken", data.access_token);
    }
  } catch (error) {
    console.error("Failed to fetch access token:", error);
    throw error;
  }
}

export async function checkAccessToken(accessToken: string | null) {
  // Checks the validity of the access token
  if (accessToken === null) {
    return false;
  }
  try {
    const response = await fetch(`${VIRTUAL_API_BASE}/check-access-token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
      body: JSON.stringify({ access_token: accessToken }),
    });

    if (!response.ok) {
      // If the backend service doesn't return a 200 status, handle it as a failure
      console.error("Failed to verify access token with the backend.");
      console.error(response);
      return false;
    }
    const data = await response.json();
    return data.valid;
  } catch (error) {
    // Handle network errors or unexpected problems in the fetch call
    console.error("An error occurred while verifying the access token:", error);
    return false;
  }
}

export function loginWithGithub(): void {
  "will be redirected to get-access-token, where the code will available in the url parameters.";
  // Generates a random hexadecimal string using window.crypto for security
  function generateRandomHex(size: number): string {
    const buffer = new Uint8Array(size);
    window.crypto.getRandomValues(buffer);
    return Array.from(buffer, byte => byte.toString(16).padStart(2, '0')).join('');
  }
   // Construct the GitHub authorization URL with necessary query parameters
   const state = generateRandomHex(16); // Generate a secure random state
   const githubUrl = new URL('https://github.com/login/oauth/authorize');
   githubUrl.searchParams.append('client_id', GITHUB_CLIENT_ID);
   githubUrl.searchParams.append('redirect_uri', `${BACKEND_URL}get-access-token`);
   githubUrl.searchParams.append('scope', 'public_repo');
   githubUrl.searchParams.append('state', state);
   githubUrl.searchParams.append('allowed_signup', 'true');
 
   // Store state in sessionStorage for later validation
   sessionStorage.setItem('oauth_state', state);
 
   // Redirect user to GitHub OAuth page
   window.location.href = githubUrl.toString();
}
