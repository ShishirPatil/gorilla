# Agent Marketplace [[Project Website](https://www.llm-agents.info/)]



Welcome to the Agent Marketplace! This platform is designed for users to explore and submit various Large Language Model (LLM) agents. The marketplace is suited for users seeking tools to enhance your productivity, automate tasks, or opportunities to contribute their own agents.

## Getting Started

To get the Agent Marketplace up and running on your local machine, you will need to set up both the client (frontend) and the server (backend).

### Prerequisites

- Node.js installed on your machine. You can download it from [Node.js official website](https://nodejs.org/).
- NPM (Node Package Manager), which comes with Node.js.

### Setting Up the Server

The server for the Agent Marketplace is deployed on Vercel. Therefore, you don't need to run the server locally. Any changes to the server should be made through pull requests, and they will be deployed automatically.


### Setting Up the Client

1. **Navigate to the client directory** from the root of the project:
    ```bash
    cd client
    ```

2. **Install the necessary npm packages**:
    ```bash
    npm install
    ```
    This installs all the dependencies required for the client side of the application.

3. **Start the client**:
    ```bash
    npm start
    ```
    This command will start the React application. By default, it should open in your web browser at `http://localhost:3000`. If it doesn't, you can manually navigate to this URL in your browser.

## Contributing

Contributions to the Agent Marketplace are welcome! If you have a change you'd like to submit or improvements to the platform, please follow the standard GitHub pull request process:

1. Fork the repository.
2. Create a new branch for your contribution.
3. Make your changes.
4. Submit a pull request with a clear description of your changes.

If you want to add new agents through a PR, in the `server/index.js` file, input your agent's data in a clearly defined JSON object in the `agentsData` array with the following format:

```javascript
const agentsData = [
    {
        name: "Example Agent",
        description: "This agent demonstrates...",
        readme: "Usage instructions here...",
        source: "https://github.com/username/repository",
        skeletonCode: "function exampleAgent() {...}",
        additionalResources: "https://resource.link",
        tags: ["example", "demo"]
    }
];
```

## Support

If you encounter any issues or have questions about setting up the project, feel free to open an issue on the GitHub repository, or reach out to the community on Discord.

Enjoy using and contributing to the Agent Marketplace!
