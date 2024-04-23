// types.ts
export interface ApiCallDetail {
  user_name: string;
  api_name: string;
  api_call: string;
  api_version: string | null;
  api_arguments: string[][];
  functionality: string;
  env_requirements: string[] | string | null;
  example_code: string;
  meta_data: string | null;
  Questions: string[];
}

export interface ConvertedURL {
  status: string;
  data: ApiCallDetail[];
}

export interface ConvertResult {
  [key: string]: ConvertedURL; // Key is the URL string
}
