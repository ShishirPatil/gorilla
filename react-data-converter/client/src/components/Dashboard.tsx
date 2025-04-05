import React, { useState } from "react";
import InputCard from "./InputCard/InputCard";
import OutputCard from "./OutputCard/OutputCard";
import { ConvertResult } from "../types/types";
import { convertUrls } from "@/pages/api/apiService";
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

interface DashboardProps {
  // 
}

const Dashboard: React.FC<DashboardProps> = () => {
  const [urlsResults, setUrlsResults] = useState<ConvertResult>({});

  const handleConvertAndSetUrls = async (username: string, apiName: string, urls: string[]) => {
    setUrlsResults({});
    try {
      const result = await toast.promise(convertUrls(username, apiName, urls),
        {
          pending: "Converting URLs...",
          success: "URLs converted successfully!",
          error: "Conversion failed.",
        });

      setUrlsResults(result);
    } catch (error) {
      throw error;
    }
  };

  return (
    <div className="row justify-content-center">
      <div className="col-lg-11">
        <div className="card-deck">
          <InputCard handleConvertAndSetUrls={handleConvertAndSetUrls}></InputCard>
          <OutputCard urlsResults={urlsResults}></OutputCard>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
