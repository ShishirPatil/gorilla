import { ConvertResult, ConvertedURL } from "../types/types";

// apiService.js
const BACKEND_BASEURL = "/api";
const GITHUB_CLIENT_ID = "752573cfa527a1b392ad"

export const convertUrls = async (username: string, apiName: string, urls: string[]): Promise<ConvertResult> => {
  try {
    const response = await fetch(`${BACKEND_BASEURL}/convert`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: 'include',
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


export const raisePullRequest = async ( username: string, urlResults: ConvertResult) => {
  const accessToken = localStorage.getItem('accessToken');
  if (!accessToken) {
    alert("Please login to Github to raise a pull request");
    return;
  }
  if (!username || !isValidUrlResults(urlResults)) {
    alert("Please enter a username and at least one urlResult must be successful to raise a pull request");
    return;
  }
  try {
    const response = await fetch(`${BACKEND_BASEURL}/raise-pr`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json", 
        "Authorization": `Bearer ${accessToken}` 
      },
      credentials: 'include',
      body: JSON.stringify({
        user_name: username,
        api_urls: urlResults,
      }),
    });
    if (response.ok) {
      const result = await response.json();
      console.log('Success:', result);
      // Redirect the user to GitHub comparison page
      window.location.href = result.compare_url;
    } else {
      const errorDetails = await response.text();
      throw new Error(`HTTP error! status: ${response.status}, details: ${errorDetails}`);
    }
  } catch (error) {
    console.error("Failed to raise a pull request:", error);
    throw error;  // rethrow to handle this error further up the call stack
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

  const issueUrl = new URL('https://github.com/ShishirPatil/gorilla/issues/new');
  issueUrl.searchParams.append('title', title);
  issueUrl.searchParams.append('body', description);
  issueUrl.searchParams.append('labels', 'conversion-error,apibench-data');

  window.open(issueUrl.toString(), '_blank');
}

export async function getAccessToken(codeParam: string) {
  try {
    const response = await fetch(`${BACKEND_BASEURL}/getAccessToken?code=${codeParam}`, {
      method: "GET",
    });
    const data = await response.json();
    if (data.access_token) {
      localStorage.setItem("accessToken", data.access_token);
      console.log('Access Token:', data.access_token);
    }
  } catch (error) {
    console.error('Failed to fetch access token:', error);
    throw error;
  }
}
  
export function loginWithGithub(): void {
  function generateRandomHex(size: number) {
    const buffer = new Uint8Array(size);
    window.crypto.getRandomValues(buffer);
    return Array.from(buffer, byte => byte.toString(16).padStart(2, '0')).join('');
  }

  // Generate a 16-byte hex string
  const state = generateRandomHex(16);
  const githubUrl = new URL('https://github.com/login/oauth/authorize');
  githubUrl.searchParams.set('client_id', GITHUB_CLIENT_ID);
  githubUrl.searchParams.set('scope', 'repo');
  githubUrl.searchParams.set('state', state);
  githubUrl.searchParams.set('allowed_signup', 'true');

  console.log(githubUrl.toString());
  
  window.location.assign(githubUrl.toString());
}

// Helper function to validate urlResults
function isValidUrlResults(urlResults: ConvertResult): boolean {
  return Object.values(urlResults).some(result => result.status === "success");
}
