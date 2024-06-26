import React from 'react';
import '../App.css'; // Assuming your CSS is here
import { useNavigate } from 'react-router-dom';

const FAQPage = () => {
  const navigate = useNavigate();

  const backButtonStyle = {
    padding: '10px 20px', 
    margin: '0 0 20px', 
    cursor: 'pointer',
    fontWeight: 'bold',
    fontSize: '1rem', // Use 'rem' units for scalable font size
    minWidth: '100px', // Minimum width so the button doesn't become too small
    minHeight: '40px', // Minimum height for the same reason
  };

  const demoContainerStyle = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    marginTop: '20px',
  };

  const demoStyle = {
    width: '100%',
    maxWidth: '700px', // Ensure videos don't grow too large
    margin: '20px 0',
    textAlign: 'center',
  };

  const iframeStyle = {
    width: '100%',
    height: '400px', // Increased height
    border: 'none',
  };

  const captionStyle = {
    fontSize: '1em',
    textAlign: 'center',
    marginTop: '10px',
  };

  return (
    <>    
    <div className="faqContainer">
      <button onClick={() => navigate(-1)} style={backButtonStyle}>← Go Back</button>

      <h2>FAQs</h2>
      <div className="faqQuestion">What is the Agent Marketplace?</div>
      <div className="faqAnswer">The Agent Marketplace is a centralized platform where users can easily search for, discover, and deploy a variety of LLM (Large Language Model) agents for tasks such as productivity, automation, data retrieval, and more. Although numerous agents have been developed integrating both LLMs and APIs, the absence of a unified platform has limited their exposure and utilization. Through the marketplace, these agents gain increased exposure to the open-source community, allowing users to leverage them to automate daily tasks or build complex applications.</div>

      <div className="faqQuestion">What are the benefits of using LLM agents?</div>
      <div className="faqAnswer">LLM agents offer expanded functionality by allowing interaction with external systems and APIs, improved accuracy by providing relevant and up-to-date context, and automation of repetitive tasks to enhance efficiency.</div>

      <div className="faqQuestion">How can I use the agents available in the marketplace?</div>
      <div className="faqAnswer">Users can interact with agents through their individual cards on the homepage. Each agent includes a detailed ReadMe file with instructions for use, which may involve providing an OpenAI API key and following setup steps on how to run the agent source code.</div>

      <div className="faqQuestion">Where are the agents sourced from?</div>
      <div className="faqAnswer">The agents are sourced from trusted platforms and open-source repositories, including LangChain, LlamaIndex, OpenAI Assistants, and CrewAI.</div>

      <div className="faqQuestion">Can I contribute to the marketplace?</div>
      <div className="faqAnswer">Yes, contributions are encouraged. Users can submit their own agents through the marketplace interface or via GitHub pull requests. Detailed instructions for submitting agents are available on the platform.</div>

      <div className="faqQuestion">Is there a limit to the number of agents I can use?</div>
      <div className="faqAnswer">No, there is no limit. Users can access and utilize as many agents as needed to enhance their productivity and task automation.</div>

      <div className="faqQuestion">How are the agents categorized?</div>
      <div className="faqAnswer">The agents are categorized into practical categories such as Communication, Finance, Data, and AI, making it easier for users to find agents suited to their specific needs.</div>

      <div className="faqQuestion">How can I deploy the agents?</div>
      <div className="faqAnswer">Each agent comes with a description and a ReadMe file with instructions on how to deploy it. Users need to install the necessary requirements and obtain any required API keys as detailed in the agent's documentation.</div>

      <div className="faqQuestion">What is the review and verification process for agents?</div>
      <div className="faqAnswer">Agents on the marketplace are verified and reviewed by users. This helps maintain a high standard of quality and reliability for all agents available on the platform.</div>

      <div style={demoContainerStyle}>
        <div style={demoStyle}>
          <div className="faqQuestion">See the Yahoo Finance Agent in action:</div>
          <iframe 
            src="https://www.youtube.com/embed/muSPKnPLI_w?si=S6IG4BWIJElgGKC1" 
            style={iframeStyle}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen>
          </iframe>
          <i style={captionStyle}>
            Search and get code to run AI agents from the marketplace such as this Yahoo Finance Agent.
          </i>
        </div>
        <div style={demoStyle}>
          <div className="faqQuestion">See the Google Jobs Agent in action:</div>
          <iframe 
            src="https://www.youtube.com/embed/3Lz2pCGjQEU?si=9-M0bPkncJ-el9xD" 
            style={iframeStyle}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen>
          </iframe>
          <p style={captionStyle}>
            <i style={{ fontSize: '1em' }}>
              Google Jobs agent providing real time postings of request occupation.
            </i>
          </p>    
        </div>
      </div>
    </div>
    </>
  );
};

export default FAQPage;
