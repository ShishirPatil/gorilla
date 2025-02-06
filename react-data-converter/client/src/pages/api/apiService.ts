// Next.js API route support: https://nextjs.org/docs/api-routes/introduction
import type { NextApiRequest, NextApiResponse } from "next";
import { ConvertResult, ConvertedURL } from "@/types/types";

// apiService.js
const BACKEND_BASEURL = "http://localhost:8080";

// Add the convertUrls function here
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


export const raisePullRequest = async (urlResults: ConvertResult) => {
  try {
    const response = await fetch(`${BACKEND_BASEURL}/store-option1-content`, {
      method: "POST",
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(urlResults),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    // Redirect to GitHub login on successful API call
    window.location.href = `${BACKEND_BASEURL}/login/github`;

    // Assuming a JSON response for successful API call
    return await response.json();
  } catch (error) {
    console.error("Failed to store Option1 content:", error);
    throw new Error('An error occurred while storing Option1 content and initiating GitHub login');
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
  