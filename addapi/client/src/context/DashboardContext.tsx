import React, { createContext, useContext, ReactNode, useState } from "react";
import { ConvertResult } from "../types/types";

interface DashboardContextType {
  username: string;
  apiName: string;
  urls: string[];
  urlsResults: ConvertResult;
  setUsername: React.Dispatch<React.SetStateAction<string>>;
  setApiName: React.Dispatch<React.SetStateAction<string>>;
  setUrls: React.Dispatch<React.SetStateAction<string[]>>;
  setUrlsResults: React.Dispatch<React.SetStateAction<ConvertResult>>;
}

// context with a default empty state
const defaultState: DashboardContextType = {
  username: "",
  apiName: "",
  urls: [],
  urlsResults: {},
  setUsername: () => { },
  setApiName: () => { },
  setUrls: () => { },
  setUrlsResults: () => { },
};

const DashboardContext = createContext<DashboardContextType>(defaultState);

interface DashboardProviderProps {
  children: ReactNode;
}

// hook to use the dashboard context
export const useDashboard = () => useContext(DashboardContext);

export const DashboardProvider: React.FC<DashboardProviderProps> = ({ children }) => {
  const [username, setUsername] = useState<string>("");
  const [apiName, setApiName] = useState<string>("");
  const [urls, setUrls] = useState<string[]>(['']);
  const [urlsResults, setUrlsResults] = useState<ConvertResult>({});

  // Value to be passed to the provider
  const value = {
    username,
    apiName,
    urls,
    urlsResults,
    setUsername,
    setApiName,
    setUrls,
    setUrlsResults,
  };

  return (
    <DashboardContext.Provider value={value}>
      {children}
    </DashboardContext.Provider>
  );
};
