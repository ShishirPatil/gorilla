import React, { useState, useEffect, useContext } from "react";
import axios, { all } from "axios";
import {
  Container,
  Row,
  Col,
  Button,
  Form,
  OverlayTrigger,
  Tooltip,
  Spinner,
} from "react-bootstrap";
import { FiPaperclip, FiX } from "react-icons/fi"; // Clipper icon
import { toast } from "react-toastify";
import { MdClose } from "react-icons/md";
import AgentDropdown from "./AgentDropdown";
import CodeEditor from "./CodeEditor";
import useTypingEffect from "./useTypingEffect";
import { ThemeContext } from "../App";
import { Analytics } from "@vercel/analytics/react";
import { AnsiUp } from "ansi_up";
import CodeMirror from "@uiw/react-codemirror";
import AgentOutput from "./AgentOutput"

const AgentArena = () => {
  const [leftAgent, setLeftAgent] = useState(null);
  const [rightAgent, setRightAgent] = useState(null);
  const { theme } = useContext(ThemeContext);
  const ansiUp = new AnsiUp();
  const [goal, setGoal] = useState("");
  const [agents, setAgents] = useState([]);
  const [leftExecutedCode, setLeftExecutedCode] = useState("");
  const [rightExecutedCode, setRightExecutedCode] = useState("");
  const [leftOutput, setLeftOutput] = useState([]);
  const [rightOutput, setRightOutput] = useState([]);

  const [leftCompleted, setLeftCompleted] = useState(false);
  const [rightCompleted, setRightCompleted] = useState(false);
  const [ratingEnabled, setRatingEnabled] = useState(false);
  const [hasVoted, setHasVoted] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [votedResult, setVotedResult] = useState("");
  const [shareURL, setShareURL] = useState("");
  const [promptId, setPromptId] = useState(null);
  const [leftFile, setLeftFile] = useState(null);
  const [rightFile, setRightFile] = useState(null);
  const [isExample3, setIsExample3] = useState(false);
  const [userApiKeys, setUserApiKeys] = useState({});
  const [isRunningBoth, setIsRunningBoth] = useState(false);
  const [leftCodeCollapsed, setLeftCodeCollapsed] = useState(false);
  const [rightCodeCollapsed, setRightCodeCollapsed] = useState(false);
  const [runBothTriggered, setRunBothTriggered] = useState(false);
  const [file, setFile] = useState(null); // To store the uploaded file
  const [fileUploadAllowed, setFileUploadAllowed] = useState(false);
  const [agentDescriptions, setAgentDescriptions] = useState("");

  const [showLeftRawOutput, setShowLeftRawOutput] = useState(false);
  const [showRightRawOutput, setShowRightRawOutput] = useState(false);

  const [leftEventSource, setLeftEventSource] = useState(null);
  const [rightEventSource, setRightEventSource] = useState(null);

  const [showVotedAgentNames, setShowVotedAgentNames] = useState(false);

  const [showAgentNames, setShowAgentNames] = useState(false); 

  
  const AgentHeader = ({ title }) => (
    <h2 className="text-center mb-4" style={{
      fontSize: '2rem',
      fontWeight: 'bold',
      color: '#ffff',
      textShadow: '1px 1px 2px rgba(0,0,0,0.1)',
      borderBottom: showAgentNames ? 'none' : '2px solid #6b46c1',
      paddingBottom: showAgentNames? '0px': '10px',
      marginTop: '20px'
    }}>
      {title}
    </h2>
  );

  const examplePrompts = [
    "what was AAPL stock yesterday",
    "Summarize for me a fascinating article about cats",
    "Find cheap hotels in Austin, Texas",
    "What is this paper about: 1706.03762",
  ];

  useEffect(() => {
    // Fetch the text file from the public folder
    fetch("/agents_desc.txt")
      .then((response) => response.text())
      .then((data) => {
        setAgentDescriptions(data); // Store the file content in state
      })
      .catch((error) => {
        console.error("Error fetching the file:", error);
      });
  }, []);

  const displayedPrompt = useTypingEffect(examplePrompts);

  const removeFile = () => {
    setFile(null); // Reset file
  };

  useEffect(() => {
    axios
    .get("https://agent-arena.vercel.app/api/agents")
    .then((response) => {
      const fetchedAgents = response.data.filter(agent => !agent.modificationNeeded); // Filter agents where modificationNeeded is false
      if (!fetchedAgents || fetchedAgents.length === 0) {
        // Show toast notification that no agents are available and reloading
        toast.info("Loading agents, please wait...");
  
        // Reload the page after a short delay (e.g., 2 seconds)
        setTimeout(() => {
          window.location.reload();
        }, 2000);
      } else {
        setAgents(fetchedAgents); // Set agents if data is available
      }
    })
    .catch((error) => {
      // Show toast notification for error and reload
      toast.info("Loading agents, please wait...");  
      // Reload the page after a short delay (e.g., 2 seconds)
      setTimeout(() => {
        window.location.reload();
      }, 2000);
  
      console.error("Error fetching agents:", error);
    });
  

    const token = localStorage.getItem("token");
    if (token) {
      axios
        .get("https://agent-arena.vercel.app/api/profile", {
          headers: { Authorization: `Bearer ${token}` },
        })
        .then((response) => {
          setIsLoggedIn(true);
          setUserApiKeys(response.data.apiKeys || {});
        })
        .catch((error) => {
          console.error("Error fetching profile:", error);
        });
    }
  }, []);

  useEffect(() => {
    if (leftCompleted && rightCompleted) {
      setRatingEnabled(true);
    }
  }, [leftCompleted, rightCompleted]);

  const handleLeftSelect = (agent) => {
    if (leftEventSource) {
      leftEventSource.close();
      setLeftEventSource(null);
    }
    setLeftAgent(agent);
    setLeftExecutedCode(
      goal ? agent.code.replace("Enter Goal/Prompt Here", goal) : agent.code
    );
    resetVotingState();
    setLeftCodeCollapsed(false); // Ensure code editor is expanded when selecting a new agent
    setRightCodeCollapsed(false); // Ensure code editor is expanded when selecting a new agent
    if(isExample3){
      setFile(null);
      setLeftFile(null);
    }
    setFileUploadAllowed(agent.allowsFileUpload);
    setShowVotedAgentNames(false);

  };

  useEffect(() => {
    console.log("Left file updated:", leftFile);
  }, [leftFile]);

  useEffect(() => {
    console.log("Right file updated:", rightFile);
  }, [rightFile]);

  const checkBothCompleted = () => {
    if (leftCompleted && rightCompleted) {
      setIsRunningBoth(false);
      setRatingEnabled(true);
      setRunBothTriggered(false);
    }
  };

  const buttonStyles = {
    search: {
      normal: "#c5cae9",
      hover: "#9fa8da",
    },
    finance: {
      normal: "#a2d5f2",
      hover: "#8bc3de",
    },
    data: {
      normal: "#dcedc1",
      hover: "#c6d7a8",
    },
    research: {
      normal: "#ffe0b2", // Research Example button color
      hover: "#ffcc80", // Slightly darker shade for hover effect
    },
    automation: { normal: "#ffccbc", hover: "#ffab91" },
  };

  const runBothButtonStyle = {
    backgroundColor: theme === "dark" ? "#6f42c1" : "#28a745", // Purple for dark mode, Green for light mode
    borderColor: theme === "dark" ? "#6f42c1" : "#28a745",
    color: "#fff",
    fontSize: "1.25rem", // Make the text larger
    fontWeight: "bold",
    padding: "10px 25px",
    borderRadius: "8px",
    boxShadow: "0px 4px 15px rgba(0, 0, 0, 0.2)", // Add shadow for depth
    transition: "all 0.3s ease",
  };

  const runBothButtonHoverStyle = {
    backgroundColor: "#218838", // Darker green on hover
    borderColor: "#218838",
  };

  const handleRightSelect = (agent) => {
    if (rightEventSource) {
      rightEventSource.close();
      setRightEventSource(null);
    }
  
    setRightAgent(agent);
    setRightExecutedCode(
      goal ? agent.code.replace("Enter Goal/Prompt Here", goal) : agent.code
    );
      // If the selected agent is not part of Example 3, reset the file
    setIsExample3(false);
    if (isExample3) {
      setFile(null);
      setRightFile(null);
    }
    resetVotingState();
    setRightCodeCollapsed(false); // Ensure code editor is expanded when selecting a new agent
    setLeftCodeCollapsed(false); // Ensure code editor is expanded when selecting a new agent
    setFileUploadAllowed(agent.allowsFileUpload);
    setShowVotedAgentNames(false);

  };

  const resetVotingState = () => {
    setLeftCompleted(false);
    setRightCompleted(false);
    setRatingEnabled(false);
    setHasVoted(false);
    setLeftOutput("");
    setRightOutput("");
    setVotedResult("");
    setShareURL("");
    setPromptId(null);
    setLeftFile(null);
    setRightFile(null);
    setIsExample3(false);
    setIsRunningBoth(false);
    setRunBothTriggered(false);

    if (leftEventSource) {
      leftEventSource.close();
      setLeftEventSource(null);
    }
    if (rightEventSource) {
      rightEventSource.close();
      setRightEventSource(null);
    }
  };

  const handleRating = (rating) => {
    toast.success("Your rating has been submitted!");
    setHasVoted(true);
    setVotedResult(rating);

    setRatingEnabled(false);
    setShowVotedAgentNames(true);


    const leftOutputString = leftOutput.join(""); // Convert array to string
    const rightOutputString = rightOutput.join(""); // Convert array to string

 
    axios
      .post("https://agent-arena.vercel.app/api/ratings", {
        leftAgent: leftAgent._id,
        rightAgent: rightAgent._id,
        rating,
        executedCode: leftExecutedCode + "\n" + rightExecutedCode,
        leftOutput:leftOutputString,
        rightOutput:rightOutputString,
        savePrompt: isLoggedIn,
      })
      .then((response) => {
        setPromptId(response.data.promptId);
      })
      .catch((error) => {
        console.error("Error saving rating:", error);
      });
  };

  const handleSavePrompt = async () => {
    if (!isLoggedIn) {
      toast.error("You need to be logged in to save prompts");
      return;
    }
    const leftOutputString = leftOutput.join(""); // Convert array to string
    const rightOutputString = rightOutput.join(""); // Convert array to string

    try {
      const response = await axios.post(
        "https://agent-arena.vercel.app/api/prompts/save",
        {
          text: goal,
          leftAgent: leftAgent._id,
          rightAgent: rightAgent._id,
          leftExecutedCode,
          rightExecutedCode,
          votedResult,
          leftOutput:leftOutputString,
          rightOutput:rightOutputString,
        },
        {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        }
      );
      toast.success("Prompt saved successfully");
      setPromptId(response.data.promptId);
      setShareURL(`https://agent-arena.com/prompts/${response.data.promptId}`);
    } catch (error) {
      toast.error("Error saving prompt");
    }
  };

  const handleSearch = async (searchGoal) => {
    if (!agents.length) {
      toast.error("No agents available for selection");
      return;
    }
    searchGoal = searchGoal.replace(/"/g, '');
    searchGoal = searchGoal.replace(/'/g, '');



    try {
      const agentNames = agents.map((agent) => agent.name);
      const response = await axios.post(
        "https://agent-arena.vercel.app/api/goals/interpret-goal",
        { goal: searchGoal, agentNames, fileUploaded: file  }
      );
      const { agent1, agent2 } = response.data;
      setFileUploadAllowed(agent1.allowsFileUpload || agent2.allowsFileUpload);
      console.log(fileUploadAllowed);

      setLeftAgent(agent1);
      setRightAgent(agent2);
      setLeftExecutedCode(
        searchGoal
          ? agent1.code.replace("Enter Goal/Prompt Here", goal)
          : agent1.code
      );
      setRightExecutedCode(
        searchGoal
          ? agent2.code.replace("Enter Goal/Prompt Here", goal)
          : agent2.code
      );

      if (agent1.allowsFileUpload && file) {
        setLeftFile(file); // Set the leftFile to the global file if leftAgent allows file uploads
      }
      if (agent2.allowsFileUpload && file) {
        setRightFile(file);
      }
      resetVotingState();
    } catch (error) {
      console.error("Error during agent search:", error);

      // Automatically select fallback agents if no agents are found
      const fallbackAgent1 = agents.find(
        (agent) => agent.name === "langchain brave-search agent (gemini-1.5-flash-001)"
      );
      const fallbackAgent2 = agents.find(
        (agent) =>
          agent.name === "llamaindex brave-search agent (gpt-4o-2024-08-06)"
      );

      if (fallbackAgent1 && fallbackAgent2) {
        setLeftAgent(fallbackAgent1);
        setRightAgent(fallbackAgent2);
        setLeftExecutedCode(
          goal
            ? fallbackAgent1.code.replace("Enter Goal/Prompt Here", goal)
            : fallbackAgent1.code
        );
        setRightExecutedCode(
          goal
            ? fallbackAgent2.code.replace("Enter Goal/Prompt Here", goal)
            : fallbackAgent2.code
        );
        resetVotingState();
      } else {
        toast.error(
          "There was an issue selecting fallback agents. Please try again."
        );
      }
    }
  };

  const handleRunBoth = async () => {
    setLeftCodeCollapsed(true);
    setRightCodeCollapsed(true);
    if (!leftAgent || !rightAgent) {
      toast.error("Please select both agents before running");
      return;
    }


    if((fileUploadAllowed || leftAgent.allowsFileUpload || rightAgent.allowsFileUpload) && !file) {
      toast.error("Please upload a file before running these agents");
      return;
    }


    setIsRunningBoth(true);
    setLeftCompleted(false);
    setRightCompleted(false);
    setRatingEnabled(false);
    setHasVoted(false);
    setLeftOutput("");
    setRightOutput("");
    setRunBothTriggered((prev) => !prev);

    const leftFormData = new FormData();
    const rightFormData = new FormData();




    if (fileUploadAllowed && file) {
      leftFormData.append("general_file", file);
      rightFormData.append("general_file", file);
    }
    

    leftFormData.append("code", leftExecutedCode);
    leftFormData.append("agentId", leftAgent._id);
    if (leftFile) {
      leftFormData.append("general_file", leftFile);
    }
    if (file) {
      leftFormData.append("general_file", file);
      rightFormData.append("general_file", file);
    }
    Object.keys(userApiKeys).forEach((key) => {
      leftFormData.append(key, userApiKeys[key]);
    });

    rightFormData.append("code", rightExecutedCode);
    rightFormData.append("agentId", rightAgent._id);
    if (rightFile) {
      rightFormData.append("general_file", rightFile);
    }
    Object.keys(userApiKeys).forEach((key) => {
      rightFormData.append(key, userApiKeys[key]);
    });

    try {
      const [leftResponse, rightResponse] = await Promise.all([
        axios.post("https://agent-arena-location.onrender.com/api/jobs/create", leftFormData, {
          headers: { "Content-Type": "multipart/form-data" },
        }),
        axios.post("https://agent-arena-location.onrender.com/api/jobs/create", rightFormData, {
          headers: { "Content-Type": "multipart/form-data" },
        }),
      ]);
  
      const leftES = streamJobOutput(leftResponse.data.jobId, setLeftOutput, () => {
        const blocks = processFullOutput(leftOutput);
        setLeftCompleted(true);
        checkBothCompleted();
      });
      setLeftEventSource(leftES); // Store the EventSource
  
      const rightES = streamJobOutput(rightResponse.data.jobId, setRightOutput, () => {
        const blocks = processFullOutput(rightOutput);
        setRightCompleted(true);
        checkBothCompleted();
      });
      setRightEventSource(rightES); // Store the EventSource
    } catch (error) {
      toast.error("An error occurred while running the agents");
      setIsRunningBoth(false);
    }
  };

  const streamJobOutput = (jobId, setOutput, onComplete) => {
    const eventSource = new EventSource(
      `https://agent-arena-location.onrender.com/api/jobs/${jobId}/stream`
    );
    let fullOutput = [];
  
    // Set a timeout to close the EventSource after 90 seconds
    const timeoutId = setTimeout(() => {
      eventSource.close();
      onComplete(fullOutput);
      toast.info("Execution time exceeded 90 seconds. Output has been truncated.");
    }, 90000); // 90 seconds in milliseconds
  
    eventSource.onmessage = (event) => {
      let processedOutput = event.data;
      const coloredHtml = ansiUp.ansi_to_html(processedOutput);
      fullOutput.push(coloredHtml);
      setOutput((prevOutput) => [...prevOutput, coloredHtml]);
    };
  
    eventSource.onerror = (error) => {
      console.error("EventSource failed:", error);
      clearTimeout(timeoutId); // Clear the timeout
      eventSource.close();
      onComplete(fullOutput);
    };
  
    eventSource.addEventListener("end", () => {
      clearTimeout(timeoutId); // Clear the timeout
      eventSource.close();
      onComplete(fullOutput);
    });
  
    return eventSource; // Return the EventSource instance
  };
  
  

  const handleShareSession = async () => {

    const leftOutputString = leftOutput.join(""); // Convert array to string
    const rightOutputString = rightOutput.join(""); // Convert array to string
    if (promptId) {
      navigator.clipboard.writeText(shareURL);
      toast.success("Session link copied to clipboard");
    } else {
      try {
        const response = await axios.post(
          "https://agent-arena.vercel.app/api/prompts/saveWithoutUser",
          {
            text: goal,
            leftAgent: leftAgent._id,
            rightAgent: rightAgent._id,
            leftExecutedCode,
            rightExecutedCode,
            votedResult,
            leftOutput:leftOutputString,
            rightOutput:rightOutputString,
          }
        );
        const newPromptId = response.data.promptId;
        setPromptId(newPromptId);
        const newShareURL = `https://www.agent-arena.com/prompts/${newPromptId}`;
        setShareURL(newShareURL);
        navigator.clipboard.writeText(newShareURL);
        toast.success("Session link copied to clipboard");
      } catch (error) {
        toast.error("Error sharing session");
      }
    }
  };

  const processFullOutput = (fullOutput) => {
    console.log(fullOutput);

    // Define keywords
    const thoughtKeywords = [
      "thought:",
      "Thought:",
      "Observation:",
      "observation:",
    ];
    const actionKeywords = [
      "Action:",
      "action:",
      "Action input:",
      "action input:",
      "Action Input:",
      "action Input:",
    ];
    const answerKeywords = [
      "Final Answer:",
      "final answer:",
      "Final answer:",
      "final Answer:",
      "Answer:",
      "answer:",
      "Output:",
      "output:",
    ];

    // Initialize sets
    const thoughts = new Set();
    const actions = new Set();
    const answers = new Set();

    // Ensure that fullOutput is a string
    let outputString = String(fullOutput);

    // Remove the span tags and take what is inside the spans only (so basically remove the tags only)
    outputString = outputString.replace(/<span.*?>/g, "");
    outputString = outputString.replace(/<\/span>/g, "");

    console.log(outputString);

    try {
      // Find matches for each keyword category
      thoughtKeywords.forEach((keyword) => {
        const matches = outputString.match(new RegExp(`${keyword}.*`, "gi"));
        if (matches) thoughts.add(...matches);
      });

      actionKeywords.forEach((keyword) => {
        const matches = outputString.match(new RegExp(`${keyword}.*`, "gi"));
        if (matches) actions.add(...matches);
      });

      answerKeywords.forEach((keyword) => {
        const matches = outputString.match(new RegExp(`${keyword}.*`, "gi"));
        if (matches) answers.add(...matches);
      });
    } catch (e) {
      console.error(e);
    }

    // Convert sets to lists
    const answersList = Array.from(answers);

    return answersList;
  };

  const setExample = async (exampleNumber) => {
    setShowVotedAgentNames(false);

    setIsRunningBoth(false);
    resetVotingState();
    setIsRunningBoth(false);
    setLeftCompleted(false);
    setRightCompleted(false);
    setRunBothTriggered(false);
    setLeftCodeCollapsed(false);
    setRightCodeCollapsed(false);

    let newGoal = "";
    const domains = [
      "finance",
      "stocks",
      "stock analysis",
      "stock comparisons",
      "sports news",
      "political news",
      "financial news",
      "weather",
      "entertainment news",
      "data analysis",
      "tech news",
      "trivia",
      "technology",
      "health",
      "education",
      "creative tasks",
      "data analysis",
      "everyday life",
      "research",
    ];

    const randomDomain = domains[Math.floor(Math.random() * domains.length)];
    console.log(randomDomain);

    if (exampleNumber !== 3) {
      setFile(null); // Clear the file if not the financial data example
      setLeftFile(null);
      setRightFile(null);
    }

    if (exampleNumber === "surprise") {
      try {
        const response = await axios.post(
          "https://api.openai.com/v1/chat/completions",
          {
            model: "gpt-4o-2024-08-06",
            temperature: 0.9,
            messages: [
              {
                role: "system",
                content: `You are an assistant that generates random, engaging goals for users to try in an LLM agent comparison platform. 
                        These goals should be interesting, varied, and cover diverse areas such as:
                        - **Finance:** e.g., "Analyze the performance of the MSFT stock over the last month. Has the price increased or decreased?"
                        - **Technology:** e.g., "What is the latest news regarding OpenAI's new LLM? What are the model's main contributions. "
                        - **Health:** e.g., "Design a meal plan for a vegetarian trying to get in at least 100 grams of protein every day."
                        - **Education:** e.g., "Summarize the key points of the book 'To Kill a Mockingbird' in less than 500 words."
                        - **Research** e.g., "Tell me about the contributions of Shishir Patil's Gorilla paper"
                        - **Creative Tasks:** e.g., "Write a short story set in a dystopian future."
                        - **Data Analysis:** e.g., "Analyze the dataset provided and identify the key trends and patterns."
                        - **Everyday Life:** e.g., "Organize a weekly schedule that maximizes productivity for remote workers."
                        - **Weather:** e.g., "What is the weather in Jaipur right now? Is it going to rain today?"
                        - **Sports News** e.g., "Who is currently first in the Premier League table?"
                        - **Stock Comparisos** e.g., "Compare the performance of NVDA and Broadcom stocks over the last year."
                        
                        The goal that you are trying to achieve should be able to completed by one of our AI agents. Here are the descriptions of the agents available, along with their names as well. In your prompts, do not refer to the agents that are supposed to be executing the goal at all:
                        ${agentDescriptions}
                        
                        Ensure that each goal is specific, clear, and suitable for comparing two different LLM agents. Avoid repeating similar types of goals, especially those related to travel and food. Strive for a balanced distribution across the mentioned categories.
                        `,
              },
              {
                role: "user",
                content: `Please generate a random goal for the user to use. The goal should be:
                        - **Clear and Specific:** Precisely defined to allow effective comparison between two LLM agents.
                        - **Exciting and Diverse:** Cover a range of topics such as finance, technology, health, education, creative tasks, data analysis, and everyday life.
                        - **Educational or Practical:** Aim to provide value through learning or real-world application.
                        - **One-Liner:** Concise and to the point.
                        
                        **Important:** Avoid goals related to travel and food. Ensure that the generated goal does not fall into these categories and maintains diversity from previous goals. Do not include quotation marks around the goal when returning it.

                        In this case, the user is looking for a prompt under the following category: ${randomDomain}.
                        `,
              },
            ],
            max_tokens: 100,
          },
          {
            headers: {
              Authorization: `Bearer ${process.env.REACT_APP_OPENAI_API_KEY}`,
            },
          }
        );

        newGoal = response.data.choices[0].message.content.trim();
        handleSearch(newGoal);
      } catch (error) {
        toast.error("Failed to generate a surprise goal. Please try again.");
        return;
      }
    } else {
      let isExample3Update = false;




      switch (exampleNumber) {
        case 1:
          newGoal = "What is new in California today";
          break;
        case 2:
          newGoal = "what was AAPL stock yesterday";
          break;
        case 3:
          setIsExample3(true);
          setRatingEnabled(false);
          console.log(ratingEnabled);

          newGoal =
            "using this csv of General Electric financial data, calculate the average return in 2007";
          console.log(isExample3);

          try {
            const response = await axios.get(
              "https://agent-arena-location.onrender.com/api/db/mydata",
              { responseType: "blob" }
            );
            const file = new File([response.data], "mydata.csv", {
              type: "text/csv",
            });
            setFile(file);
            // setLeftFile(file);
            // setRightFile(file);
          } catch (error) {
            toast.error("Error fetching mydata.csv");
          }
          break;
        case 4: // New Research Example case
          newGoal =
            "Analyze the use of attention mechanisms in transformers for natural language processing, particularly in long-document summarization tasks";
          break;
        case 5:
          newGoal =
            "Automate the process of identifying key patterns in large datasets for predictive analysis.";
          break;
        default:
          break;
      }
    }

    setGoal(newGoal);
    await loadExampleAgents(newGoal);
  };

  const loadExampleAgents = async (goal) => {
    let leftAgentName = "";
    let rightAgentName = "";
    if (!agents.length) {
      // Show loading message
      toast.info("Loading agents, please wait...");
  
      // Reload the page to try fetching agents again after a brief delay
      setTimeout(() => {
        window.location.reload();
      }, 2000); // Wait 2 seconds before reloading
  
      return;
    }

    switch (goal) {
      case "What is new in California today":
        leftAgentName =
          "langchain google-serper search agent (gpt-4o-2024-08-06)";
        rightAgentName = "langchain brave-search agent (gpt-4o-2024-08-06)";
        break;
      case "what was AAPL stock yesterday":
        leftAgentName =
          "langchain alpha-vantage stock agent (gpt-4-turbo-2024-04-09)";
        rightAgentName =
          "langchain alpha-vantage stock agent (gemini-1.5-flash-001)";
        break;
      case "using this csv of General Electric financial data, calculate the average return in 2007":
        leftAgentName = "langchain Pandas DataFrame (gpt-4o-2024-08-06)";
        rightAgentName =
          "langchain Pandas DataFrame (llama-3.1-405B-instruct)";
        setIsExample3(true);
        break;
      case "Analyze the use of attention mechanisms in transformers for natural language processing, particularly in long-document summarization tasks": // New Research Example
        leftAgentName = "langchain ArXiv Article Fetcher (gpt-4-0613)";
        rightAgentName =
          "llamaindex ArXiv Article Fetcher (gpt-4o-2024-08-06)";
        break;
      case "Automate the process of identifying key patterns in large datasets for predictive analysis.":
        leftAgentName = "llamaindex code interpreter (claude-3-haiku-20240307)";
        rightAgentName = "langchain Python REPL (gpt-4-turbo-2024-04-09)";
        break;
      default:
        break;
    }

    const leftAgent = agents.find((agent) => agent.name === leftAgentName);
    const rightAgent = agents.find((agent) => agent.name === rightAgentName);

    if (leftAgent && rightAgent) {
      setLeftExecutedCode(
        leftAgent.code.replace("Enter Goal/Prompt Here", goal)
      );
      setRightExecutedCode(
        rightAgent.code.replace("Enter Goal/Prompt Here", goal)
      );
      setLeftAgent(leftAgent);
      setRightAgent(rightAgent);
      setLeftCodeCollapsed(false);
      setRightCodeCollapsed(false);
    }
  };

  return (
    <Container className="d-flex flex-column align-items-center">
      <Analytics />
      <div className="w-100 mb-2 d-flex flex-column justify-content-center align-items-center">
        <h1
          className="text-center mb-1"
          style={{
            color: "#ffffff", // Bright white for the main title
            flexGrow: 1,
            fontSize: "2.5rem", // Larger font size for emphasis
            fontWeight: "bold", // Bold for stronger presence
            letterSpacing: "1px", // Added letter spacing for a sleek look
          }}
        >
          Agent Arena
        </h1>

      </div>

      <p className="text-center mb-4">
        Welcome to the LLM Agent Arena. Here, you can pit two agents against
        each other based on a goal you provide. You can also head to your
        profile to save prompts for agents and visit the Prompt Hub to see
        prompts used by other users along with their ratings. Ensure your API
        keys are configured in your profile for optimal performance.
      </p>

      {/* Search bar with file upload */}
      <Row className="mb-3 w-100 d-flex justify-content-center align-items-center">
        <Col
          xs={12}
          md={8}
          className="d-flex flex-column flex-md-row justify-content-center align-items-center"
        >
          {/* Input for goal */}
          <Form.Control
            type="text"
            placeholder={displayedPrompt || "Enter your goal"}
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === "Enter") handleSearch(goal);
            }}
            className="flex-grow-1 me-md-2 mb-2 mb-md-0"
            style={{
              borderRadius: "6px",
              padding: "10px",
              border: "1px solid #ccc",
            }}
          />

          {/* File upload button */}
          <OverlayTrigger
            placement="top"
            overlay={<Tooltip>Attach a file</Tooltip>}
          >
            <Button
              variant="outline-primary"
              onClick={() => document.getElementById("file-input").click()}
              className="me-md-2 mb-2 mb-md-0"
              style={{
                padding: "10px",
                borderRadius: "6px",
                height: "calc(100% - 2px)", // Adjust height to match the input
                display: "flex",
                alignItems: "center", // Center the icon vertically
              }}
            >
              <FiPaperclip style={{ marginRight: "5px", fontSize: "18px" }} />
              Upload
            </Button>
          </OverlayTrigger>

          {/* Hidden file input */}
          <Form.Control
            id="file-input"
            type="file"
            onChange={(e) => setFile(e.target.files[0])}
            style={{ display: "none" }}
          />

          {/* Search Button */}
          <Button
            variant="primary"
            onClick={() => handleSearch(goal)} // Pass the current goal
            style={{
              padding: "10px 20px",
              borderRadius: "6px",
              backgroundColor: "#6f42c1",
              borderColor: "#6f42c1",
            }}
          >
            Search
          </Button>
        </Col>
      </Row>

      {/* Display uploaded file */}
      {/* File upload section */}
      {file && (
        <Row className="mb-3 w-100 d-flex justify-content-center align-items-center">
          <Col className="d-flex align-items-center justify-content-center">
            <div
              className="file-upload-display d-flex align-items-center"
              style={{
                backgroundColor: "#333", // Background color for better visibility
                padding: "10px",
                borderRadius: "6px",
                maxWidth: "350px", // Limit file name width to avoid overflow
                wordWrap: "break-word",
              }}
            >
              {/* Display file name */}
              <span
                className="file-name text-white"
                style={{ marginRight: "10px", color: "#fff", fontSize: "14px" }}
              >
                {file.name}
              </span>

              {/* Close icon to remove file */}
              <MdClose
                style={{
                  cursor: "pointer",
                  color: "#ff6b6b", // Light red color for visibility
                  fontSize: "20px",
                }}
                onClick={removeFile}
              />
            </div>
          </Col>
        </Row>
      )}

      <Row className="mb-4 w-100">
        <Col className="d-none d-md-flex justify-content-center align-items-center">
          <Button
            variant="info"
            onClick={() => setExample(1)}
            className="mx-2"
            style={{
              backgroundColor: buttonStyles.search.normal,
              borderColor: buttonStyles.search.normal,
              color: theme === "light" ? "#000" : "#000", // Black text in light mode, white in dark mode
            }}
            onMouseEnter={(e) =>
              (e.target.style.backgroundColor = buttonStyles.search.hover)
            }
            onMouseLeave={(e) =>
              (e.target.style.backgroundColor = buttonStyles.search.normal)
            }
          >
            Search Example
          </Button>
          <Button
            variant="info"
            onClick={() => setExample(2)}
            className="mx-2"
            style={{
              backgroundColor: buttonStyles.finance.normal,
              borderColor: buttonStyles.finance.normal,
              color: theme === "light" ? "#000" : "#000", // Black text in light mode, white in dark mode
            }}
            onMouseEnter={(e) =>
              (e.target.style.backgroundColor = buttonStyles.finance.hover)
            }
            onMouseLeave={(e) =>
              (e.target.style.backgroundColor = buttonStyles.finance.normal)
            }
          >
            Stock Example
          </Button>
          <Button
            variant="info"
            onClick={() => setExample(3)}
            className="mx-2"
            style={{
              backgroundColor: buttonStyles.data.normal,
              borderColor: buttonStyles.data.normal,
              color: theme === "light" ? "#000" : "#000", // Black text in light mode, white in dark mode
            }}
            onMouseEnter={(e) =>
              (e.target.style.backgroundColor = buttonStyles.data.hover)
            }
            onMouseLeave={(e) =>
              (e.target.style.backgroundColor = buttonStyles.data.normal)
            }
          >
            Financial Data Example
          </Button>
          <Button
            variant="info"
            onClick={() => setExample(4)} // New Research Example
            className="mx-2"
            style={{
              backgroundColor: buttonStyles.research.normal,
              borderColor: buttonStyles.research.normal,
              color: theme === "light" ? "#000" : "#000",
            }}
            onMouseEnter={(e) =>
              (e.target.style.backgroundColor = buttonStyles.research.hover)
            }
            onMouseLeave={(e) =>
              (e.target.style.backgroundColor = buttonStyles.research.normal)
            }
          >
            Research Example
          </Button>
          <Button
            variant="info"
            onClick={() => setExample(5)}
            className="mx-2"
            style={{
              backgroundColor: buttonStyles.automation.normal,
              borderColor: buttonStyles.automation.normal,
              color: theme === "light" ? "#000" : "#000", // Black text for visibility
            }}
            onMouseEnter={(e) =>
              (e.target.style.backgroundColor = buttonStyles.automation.hover)
            }
            onMouseLeave={(e) =>
              (e.target.style.backgroundColor = buttonStyles.automation.normal)
            }
          >
            Automation Example
          </Button>
          <Button
            variant="info"
            onClick={() => setExample("surprise")}
            className="mx-2"
            style={{
              color: theme === "light" ? "#000" : "#000",
              backgroundColor: "#17a2b8",
              borderColor: "#17a2b8",
            }}
          >
            Surprise Me
          </Button>
        </Col>
        <Col xs={12} className="d-md-none">
          <Row>
            <Col xs={6} className="mb-2">
              <Button
                variant="info"
                onClick={() => setExample(1)}
                className="w-100"
                style={{
                  backgroundColor: buttonStyles.search.normal,
                  borderColor: buttonStyles.search.normal,
                  color: theme === "light" ? "#000" : "#000", // Black text for visibility
                }}
                onMouseEnter={(e) =>
                  (e.target.style.backgroundColor = buttonStyles.search.hover)
                }
                onMouseLeave={(e) =>
                  (e.target.style.backgroundColor = buttonStyles.search.normal)
                }
              >
                Search Example
              </Button>
            </Col>
            <Col xs={6} className="mb-2">
              <Button
                variant="info"
                onClick={() => setExample(2)}
                className="w-100"
                style={{
                  backgroundColor: buttonStyles.finance.normal,
                  borderColor: buttonStyles.finance.normal,
                  color: theme === "light" ? "#000" : "#000",
                }}
                onMouseEnter={(e) =>
                  (e.target.style.backgroundColor = buttonStyles.finance.hover)
                }
                onMouseLeave={(e) =>
                  (e.target.style.backgroundColor = buttonStyles.finance.normal)
                }
              >
                Stock Example
              </Button>
            </Col>
            <Col xs={6} className="mb-2">
              <Button
                variant="info"
                onClick={() => setExample(3)}
                className="w-100"
                style={{
                  backgroundColor: buttonStyles.data.normal,
                  borderColor: buttonStyles.data.normal,
                  color: theme === "light" ? "#000" : "#000",
                }}
                onMouseEnter={(e) =>
                  (e.target.style.backgroundColor = buttonStyles.data.hover)
                }
                onMouseLeave={(e) =>
                  (e.target.style.backgroundColor = buttonStyles.data.normal)
                }
              >
                Financial Data Example
              </Button>
            </Col>
            <Col xs={6} className="mb-2">
              <Button
                variant="info"
                onClick={() => setExample(4)}
                className="w-100"
                style={{
                  backgroundColor: buttonStyles.research.normal,
                  borderColor: buttonStyles.research.normal,
                  color: theme === "light" ? "#000" : "#000",
                }}
                onMouseEnter={(e) =>
                  (e.target.style.backgroundColor = buttonStyles.data.hover)
                }
                onMouseLeave={(e) =>
                  (e.target.style.backgroundColor = buttonStyles.data.normal)
                }
              >
                Research Example
              </Button>
            </Col>

            <Col xs={6} className="mb-2">
              <Button
                variant="info"
                onClick={() => setExample(5)}
                className="w-100"
                style={{
                  backgroundColor: buttonStyles.automation.normal,
                  borderColor: buttonStyles.automation.normal,
                  color: theme === "light" ? "#000" : "#000", // Black text for visibility
                }}
                onMouseEnter={(e) =>
                  (e.target.style.backgroundColor =
                    buttonStyles.automation.hover)
                }
                onMouseLeave={(e) =>
                  (e.target.style.backgroundColor =
                    buttonStyles.automation.normal)
                }
              >
                Automation Example
              </Button>
            </Col>

            <Col xs={6} className="mb-2">
              <Button
                variant="info"
                onClick={() => setExample("surprise")}
                className="w-100"
                style={{
                  backgroundColor: "#17a2b8",
                  borderColor: "#17a2b8",
                  color: theme === "light" ? "#000" : "#000",
                }}
              >
                Surprise Me
              </Button>
            </Col>
          </Row>
        </Col>
      </Row>

      <Row className="mb-4 w-100">
        <Col className="d-flex justify-content-center align-items-center">
        <OverlayTrigger
            placement="top"
            overlay={
              <Tooltip>
                {!leftAgent || !rightAgent
                  ? "Please select both agents before running"
                  : "Agent execution will not take more than 90 seconds."}
              </Tooltip>
            }
          >
            <span>
              <Button
                variant="primary"
                onClick={handleRunBoth}
                style={runBothButtonStyle}
                className="mx-3 my-2"
                disabled={
                  !leftAgent ||
                  !rightAgent ||
                  (isRunningBoth && !leftCompleted && !rightCompleted)
                }
              >
                {isRunningBoth && (!leftCompleted || !rightCompleted) ? (
                  <>
                    <Spinner
                      as="span"
                      animation="border"
                      size="sm"
                      role="status"
                      aria-hidden="true"
                      className="me-2"
                    />
                    Running...
                  </>
                ) : (
                  "Run Both Agents"
                )}
              </Button>
            </span>
          </OverlayTrigger>
        </Col>
      </Row>
      <Row className="justify-content-center w-100">
      <Col md={5}>
        
  <AgentHeader title={showVotedAgentNames && leftAgent ? leftAgent.name : "Agent 1"} />
  {showAgentNames ? (
    <AgentDropdown
      agents={agents}
      selectedAgent={leftAgent}
      onSelect={handleLeftSelect}
    />
  ) : null}
  {leftAgent ? (
    <>
      <div>
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            margin: "10px 0",
          }}
        >
           {leftCompleted && (
            <div
              style={{
                display: "flex",
                justifyContent: "center",
                margin: "10px 0",
              }}
            >
              <Button
                variant="primary"
                onClick={() => setShowLeftRawOutput(!showLeftRawOutput)}
                className="mx-3 my-2"
              >
                {showLeftRawOutput ? "Hide Left Raw Output" : "Show Left Raw Output"}
              </Button>
            </div>
          )}
        </div>
        {((leftCompleted && showLeftRawOutput) || !leftCompleted) && (
          <CodeEditor
            agentId={leftAgent._id}
            initialCode={leftExecutedCode}
            onExecute={(code, output) => {
              setLeftExecutedCode(code);
              setLeftOutput(output);
              setLeftCompleted(true);
            }}
            output={leftOutput}
            allowsFileUpload={leftAgent.allowsFileUpload}
            fileUploadMessage={leftAgent.fileUploadMessage}
            dbFilePath={leftAgent.allowsFileUpload ? leftFile : null}
            file={leftAgent.allowsFileUpload ? file : null}
            onCodeChange={(updatedCode) => setLeftExecutedCode(updatedCode)}
            isExample3={isExample3}
            modificationNeeded={leftAgent.modificationNeeded}
            agentName={leftAgent.name}
            averageExecutionTime={leftAgent.averageExecutionTime}
            userApiKeys={userApiKeys}
            codeCollapsed={leftCodeCollapsed}
            setCodeCollapsed={setLeftCodeCollapsed}
            isRunningBoth={isRunningBoth}
            runBothTriggered={runBothTriggered}
            completed={leftCompleted}
          />
        )}
      </div>
      {leftCompleted && leftOutput.length > 0 ? (
  <>
  <AgentOutput output={leftOutput} agentNumber={1} />
  </>
) : null}


    </>
  ) : null}
</Col>

<Col md={5}>
 <AgentHeader title={showVotedAgentNames && rightAgent ? rightAgent.name : "Agent 2"} />
  {showAgentNames ? (
    <AgentDropdown
      agents={agents}
      selectedAgent={rightAgent}
      onSelect={handleRightSelect}
    />
  ) : null}
  {rightAgent ? (
    <>
      <div>
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            margin: "10px 0",
          }}
        >
          {rightCompleted && (
            <div
              style={{
                display: "flex",
                justifyContent: "center",
                margin: "10px 0",
              }}
            >
              <Button
                variant="primary"
                onClick={() => setShowRightRawOutput(!showRightRawOutput)}
                className="mx-3 my-2"
              >
                {showRightRawOutput ? "Hide Right Raw Output" : "Show Right Raw Output"}
              </Button>
            </div>
          )}
        </div>
        {((rightCompleted && showRightRawOutput) || !rightCompleted) && (
          <CodeEditor
            agentId={rightAgent._id}
            initialCode={rightExecutedCode}
            onExecute={(code, output) => {
              setRightExecutedCode(code);
              setRightOutput(output);
              setRightCompleted(true);
            }}
            output={rightOutput}
            allowsFileUpload={rightAgent.allowsFileUpload}
            fileUploadMessage={rightAgent.fileUploadMessage}
            dbFilePath={rightAgent.allowsFileUpload ? rightFile : null}
            file={rightAgent.allowsFileUpload ? file : null}
            onCodeChange={(updatedCode) => setRightExecutedCode(updatedCode)}
            isExample3={isExample3}
            modificationNeeded={rightAgent.modificationNeeded}
            agentName={rightAgent.name}
            averageExecutionTime={rightAgent.averageExecutionTime}
            userApiKeys={userApiKeys}
            codeCollapsed={rightCodeCollapsed}
            setCodeCollapsed={setRightCodeCollapsed}
            isRunningBoth={isRunningBoth}
            runBothTriggered={runBothTriggered}
            completed={rightCompleted}
          />
        )}
      </div>
      {rightCompleted && rightOutput.length > 0 ? (
  <>
                <AgentOutput output={rightOutput} agentNumber={2} />
  </>
) : null}



    </>
  ) : null}
</Col>

      </Row>
      <Row className="mt-4 w-100">
        <Col className="text-center">
          <Button
            variant="success"
            onClick={() => handleRating("A is better")}
            className="mx-3 my-2"
            disabled={!ratingEnabled || hasVoted}
          >
            A is better
          </Button>
          <Button
            variant="success"
            onClick={() => handleRating("B is better")}
            className="mx-3 my-2"
            disabled={!ratingEnabled || hasVoted}
          >
            B is better
          </Button>
          <Button
            variant="info"
            onClick={() => handleRating("Tie")}
            className="mx-3 my-2"
            disabled={!ratingEnabled || hasVoted}
          >
            Tie
          </Button>
          <Button
            variant="danger"
            onClick={() => handleRating("Both are bad")}
            className="mx-3 my-2"
            disabled={!ratingEnabled || hasVoted}
          >
            Both are bad
          </Button>
        </Col>
      </Row>
<Row className="mt-4 justify-content-center w-100">
  <Col className="text-center">
    {/* If user is logged in, show the Save Prompt button */}
    {isLoggedIn && (
      <Button
        variant="primary"
        onClick={handleSavePrompt}
        className="mt-2"
        disabled={!hasVoted}
        style={{
          backgroundColor: "#6f42c1", // Purple color
          borderColor: "#6f42c1", // Purple border color
        }}
      >
        Save Prompt
      </Button>
    )}

    {/* Share Result button available for both logged-in and non-logged-in users */}
    <OverlayTrigger
      placement="top"
      overlay={
        <Tooltip>You can share the result after voting!</Tooltip>
      }
    >
      <span className="d-inline-block">
        <Button
          variant="primary"
          onClick={handleShareSession}
          className="mt-2"
          disabled={!hasVoted}
          style={{ pointerEvents: !hasVoted ? "none" : "auto" }}
        >
          Share Result
        </Button>
      </span>
    </OverlayTrigger>
  </Col>
</Row>
    </Container>
  );
};

export default AgentArena;
