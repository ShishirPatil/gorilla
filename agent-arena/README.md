# Agent Arena

**Agent Arena** is a platform designed for users to compare and evaluate various language model agents across different models, frameworks, and tools. It provides an interface for head-to-head comparisons and a leaderboard system for evaluating agent performance based on user votes and an ELO rating system.

## Frontend

The frontend of the Agent Arena is built using **React**. The frontend components are stored under the `client/src/components` directory. You can modify or enhance the UI by editing these files.

To get started with development on the frontend:

1. Navigate to the `client` folder.

   ```bash
   cd client
   ```

2. Install the dependencies:

   ```bash
   npm install
   ```

3. Start the development server:

   ```bash
   npm start
   ```

   The app will run in development mode, and you can view it at [http://localhost:3000](http://localhost:3000).


## Evaluation Directory

Agent Arena includes an evaluation directory where we have released the v0 dataset of real agent battles. This dataset includes:

- **Notebook**: A Jupyter notebook (`Agent_Arena_Elo_Rating.ipynb`) that outlines the evaluation process for agents using ELO ratings.
- **Data**: Several JSON files that store the agent, tool, framework, and model ratings.

To view the dataset and run the evaluation notebook, navigate to the `evaluation` directory:

1. Open the notebook using Jupyter or any other notebook editor.

2. You can also find the ratings for agents, models, and tools in the respective JSON files in the `evaluation` directory:
   - `agent_ratings_V0.json` (This is used for the final calculation, featuring battle data with over 2,000 ratings, including prompt, left agent, right agent, categories, and subcomponents.)
   - `toolratings_V0.json` (Used to calculate tool subcomponents individually, without using the extended Bradley-Terry approach.)
   - `modelratings_V0.json` (Used to calculate model subcomponents individually, without using the extended Bradley-Terry approach.)
   - `frameworkratings_V0.json` (Used to calculate framework subcomponents individually, without using the extended Bradley-Terry approach.)


## ELO Ratings and Evaluation

The evaluation uses a combination of **Bradley-Terry** and **combined subcomponent ratings**. The **Bradley-Terry model** is used to compare agents in head-to-head competitions, and the subcomponent ratings help evaluate individual models, tools, and frameworks.

We have also released a **leaderboard** where you can view the current standings of agents. To access the leaderboard, visit:

[Agent Arena Leaderboard](https://www.agent-arena.com/leaderboard)

### Instructions to Run

1. Ensure you have Jupyter installed in your environment.
2. Navigate to the `evaluation` directory.
3. Run the notebook:

Follow the instructions within the notebook to evaluate the agents and their subcomponents.

## Contributing

If you'd like to contribute changes to the Agent Arena, you can do so by creating a Pull Request (PR) in the Gorilla repository. Follow these steps:

1. Fork the [Gorilla repository](https://github.com/ShishirPatil/gorilla) to your GitHub account.
2. Clone the forked repository to your local machine.
   ```bash
   git clone https://github.com/<your-username>/gorilla.git
   ```
3. Create a new branch for your changes.
   ```bash
   git checkout -b your-branch-name
   ```
4. Make your changes in the `client/src/components` or other relevant directories.
5. Test your changes thoroughly.
6. Commit your changes and push them to your forked repository.
   ```bash
   git add .
   git commit -m "Description of your changes"
   git push origin your-branch-name
   ```
7. Go to the original Gorilla repository and create a Pull Request from your fork.

We welcome contributions and look forward to seeing your innovative ideas in action!

## Links

- **Arena**: [Agent-Arena](https://www.agent-arena.com/)
- **Leaderboard**: [Agent Leaderboard](https://www.agent-arena.com/leaderboard)
- **Prompt Hub**: [Prompt Hub](https://www.agent-arena.com/users)
