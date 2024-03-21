import { ConvertResult, ConvertedURL } from "../types/types";

// apiService.js
const BACKEND_BASEURL = "/api";

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
  try {
    const response = await fetch(`${BACKEND_BASEURL}/store-option1-content`, {
      method: "POST",
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify( {user_name: username, data: urlResults} ),
    });

    if (!response.ok) {
      const errorDetails = await response.text();
      throw new Error(`HTTP error! status: ${response.status}, details: ${errorDetails}`);
    }
    // Redirect to GitHub login on successful API call
    window.location.href = `${BACKEND_BASEURL}/login/github`;

    return response.json();
  } catch (error) {
    console.error("Failed to store Option1 content:", error);
    throw error;
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
  