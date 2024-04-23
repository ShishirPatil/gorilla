import React from "react";
import InputCard from "./InputCard/InputCard";
import OutputCard from "./OutputCard/OutputCard";
import { DashboardProvider } from "../context/DashboardContext";
import Examples from "./Examples";
import '../styles/components/DashboardStyles.css';
interface DashboardProps {
  // 
}


const Dashboard: React.FC<DashboardProps> = () => {
  return (
    <DashboardProvider>
      <div className="row justify-content-center ">
        <div className="col-lg-11 mb-3" >
          <div className="card-deck">
            <InputCard></InputCard>
            <OutputCard></OutputCard>
          </div>
        </div>
        <Examples></Examples>
      </div>
    </DashboardProvider>
  );
};

export default Dashboard;
