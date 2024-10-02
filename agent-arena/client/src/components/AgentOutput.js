import React from 'react';

const AgentOutput = ({ output, agentNumber }) => {
    const processOutput = (outputArray) => {
        console.log("Received outputArray:", outputArray);

        // Step 1: Look for a block containing 'output':, accounting for possible HTML encoding like &apos;
        const outputBlock = outputArray.find(block => block.includes("'output':") || block.includes("&#x27;output&#x27;"));
        console.log("Found block with 'output':", outputBlock);

        if (outputBlock) {
            // Step 2: Extract everything after 'output': in the block
            const outputIndex = outputBlock.indexOf("'output':") !== -1 
                ? outputBlock.indexOf("'output':") 
                : outputBlock.indexOf("&#x27;output&#x27;");
            console.log("Index of 'output':", outputIndex);

            if (outputIndex !== -1) {
                // Extract content after 'output': and decode HTML entities
                let result = outputBlock.slice(outputIndex + 19).trim(); // Adjust to remove 'output': itself
                result = result.replace(/[{}]+/g, ''); // Remove curly braces
                result = result.replace(/&#x27;/g, "'"); // Replace HTML entities for single quotes
                
                console.log("Extracted and cleaned content after 'output':", result);

                // Return the content styled with HTML for green color
                return `<span style="color: #0f9600; font-weight: bold; font-style: italic;">${result}</span>`;
            }
        }

        // Step 3: Fallback to looking for "Final Answer" if no 'output' is found
        const finalAnswerIndex = outputArray.findIndex(block => block.includes("Final Answer"));
        console.log("Final Answer index:", finalAnswerIndex);

        if (finalAnswerIndex !== -1) {
          // Remove specific empty spans with ">" symbol
          const finalAnswerBlocks = outputArray.slice(finalAnswerIndex).filter(block => !block.includes("<span style=\"font-weight:bold\">&gt; </span>"));
      
          // Join the remaining blocks, clean up any stray characters, and remove any trailing '>'
          const finalResult = finalAnswerBlocks.join('').replace(/>$/, '').trim();
          console.log("Extracted content after 'Final Answer':", finalResult);
          
          // Return the cleaned-up result
          return finalResult;
      }
      

        // Step 4: If neither 'output' nor "Final Answer" is found, return the full output
        const fullOutput = outputArray.join('').replace(/>$/, '').trim();
        console.log("Returning full output:", fullOutput);
        return fullOutput;
    };

    const processedOutput = processOutput(output);
    console.log("Processed output:", processedOutput);

    return (
        <>
            <h3
                className="text-center mt-4"
                style={{ fontSize: "1.5rem", color: "#4CAF50" }}
            >
                {output.some(block => block.includes("Final Answer")) || output.some(block => block.includes("'output':"))
                    ? `Final Answer from Agent ${agentNumber}:`
                    : `Full Output from Agent ${agentNumber}:`}
            </h3>
            <div
                style={{
                    maxHeight: "300px",
                    overflowY: "auto",
                    backgroundColor: "#f1f1f1",
                    color: "#000000",
                    padding: "15px",
                    borderRadius: "10px",
                    boxShadow: "0px 4px 10px rgba(0, 0, 0, 0.1)",
                    marginBottom: "20px",
                    textAlign: "left",
                    fontFamily: "'Roboto', sans-serif",
                    fontSize: "1.1rem",
                    wordBreak: "break-word",
                    maxWidth: "600px",
                    margin: "auto",
                }}
            >
                <div dangerouslySetInnerHTML={{ __html: processedOutput }} />
            </div>
        </>
    );
};

export default AgentOutput;
