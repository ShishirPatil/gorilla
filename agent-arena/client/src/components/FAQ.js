import React from 'react';
import { Container, Row, Col, Accordion } from 'react-bootstrap';
import { Analytics } from "@vercel/analytics/react";

const FAQ = () => {
  return (
    <Container className="mt-4">
      <Analytics />
      <h1 className="text-center mb-4">FAQ</h1>
      <p className="text-center mb-4">
        Here you'll find answers to some frequently asked questions about the LLM Agent Arena, its features, and how to get the most out of the platform.
      </p>
      
      <Accordion>
        <Accordion.Item eventKey="0">
          <Accordion.Header>What is LLM Agent Arena?</Accordion.Header>
          <Accordion.Body>
            The LLM Agent Arena is a platform that allows users to compare two different LLM agents based on specific goals. You can select agents, run their code, and evaluate their performance to see which one meets the goal better.
          </Accordion.Body>
        </Accordion.Item>

        <Accordion.Item eventKey="1">
        <Accordion.Header>How do I select and compare agents?</Accordion.Header>
        <Accordion.Body>
            You can enter a goal in the search bar, and our system will automatically assign two random agents that are best suited to achieve the goal. However, you can also use the dropdown menus labeled "Agent 1" and "Agent 2" to change the agents manually. After selecting or modifying the agents, you can run them to compare their outputs and vote on which one performs better.
        </Accordion.Body>
        </Accordion.Item>


        <Accordion.Item eventKey="2">
          <Accordion.Header>What are examples of goals I can use to compare agents?</Accordion.Header>
          <Accordion.Body>
            The platform provides a variety of example goals, such as:
            <ul>
              <li>“What was AAPL stock yesterday?”</li>
              <li>“Summarize an interesting article about cats.”</li>
              <li>“Find cheap hotels in Austin, Texas.”</li>
            </ul>
            You can also create your own goal by entering a specific task in the search bar.
          </Accordion.Body>
        </Accordion.Item>

        <Accordion.Item eventKey="3">
          <Accordion.Header>What is the Prompt Hub?</Accordion.Header>
          <Accordion.Body>
            The Prompt Hub is a feature that allows users to save and share prompts used in the arena. You can view prompts from other users, along with the agents and results they used. This is a great way to explore different goals and see which agents work best for specific tasks.
          </Accordion.Body>
        </Accordion.Item>

        <Accordion.Item eventKey="4">
          <Accordion.Header>How does the rating system work?</Accordion.Header>
          <Accordion.Body>
            After running both agents, you will be able to rate their performance by choosing whether Agent 1, Agent 2, both, or neither performed better. Your rating helps improve the overall rankings of agents in the leaderboard.
          </Accordion.Body>
        </Accordion.Item>

        <Accordion.Item eventKey="5">
          <Accordion.Header>What is the Leaderboard?</Accordion.Header>
          <Accordion.Body>
            The Leaderboard is a comprehensive ranking system that showcases the performance of AI agents, models, tools, and frameworks. It uses an ELO-like rating system derived from battle-style competitions between agents across various categories. The Leaderboard doesn't just rank agents as a whole, but also leverages battle information to evaluate and rank individual components such as models (e.g., OpenAI, Anthropic), tools (categorized by function), and frameworks (e.g., LangChain, LlamaIndex). This granular approach provides insights into what makes an effective AI agent and helps users understand which underlying technologies are driving success in different domains.
          </Accordion.Body>
        </Accordion.Item>

        <Accordion.Item eventKey="6">
          <Accordion.Header>How do I save prompts and view my saved prompts?</Accordion.Header>
          <Accordion.Body>
            After running agents and voting, you can save the prompt for future use by heading to your profile and selecting "Save Prompt." All saved prompts will be available in your profile under the "Saved Prompts" section.
          </Accordion.Body>
        </Accordion.Item>

        <Accordion.Item eventKey="7">
          <Accordion.Header>How can I use my own API keys in the arena?</Accordion.Header>
          <Accordion.Body>
            For the best experience, it is recommended to add your own API keys for specific agents. After logging in, you can configure your API keys in your profile page by navigating to the "API Keys" section. These keys will then be automatically used when running the agents.
          </Accordion.Body>
        </Accordion.Item>

        <Accordion.Item eventKey="8">
          <Accordion.Header>Is there a way to share results with others?</Accordion.Header>
          <Accordion.Body>
            Yes! After voting, you can share your session by generating a shareable link. This link will allow others to view the agents you used, the prompt, and the output results. You can find the shareable link in your saved prompts or after running agents.
          </Accordion.Body>
        </Accordion.Item>


        <Accordion.Item eventKey="9">
          <Accordion.Header>How can people contribute agents or models?</Accordion.Header>
          <Accordion.Body>
            If you'd like to contribute agents or models to the LLM Agent Arena, we welcome your contributions! You can reach out to us via our <a href="/contact-us">Contact Us</a> page to discuss the agents or models you'd like to add. Our team will review your submission and get back to you.
          </Accordion.Body>
        </Accordion.Item>

        <Accordion.Item eventKey="10">
          <Accordion.Header>What models do we consider?</Accordion.Header>
          <Accordion.Body>
            We currently have support for models across various providers, including OpenAI, Anthropic, Google Gemini, Llama, and Mistral. Here are the models we have integrated:
            <ul>
              <li>gpt-4o-2024-08-06, gpt-4o-2024-05-13, gpt-4-turbo-2024-04-09, gpt-4-0613</li>
              <li>claude-3-5-sonnet-20240620, claude-3-opus-20240229, claude-3-haiku-20240307</li>
              <li>gemini-1.5-pro-001, gemini-1.5-flash-001</li>
              <li>open-mixtral-8x7b, mistral-large-2407, open-mixtral-8x22b</li>
              <li>llama-3.1-405B-instruct, llama-3.1-8B-instruct, llama-3.1-70B-instruct</li>
              <li>llama-3.1-sonar-small-128k-online, llama-3.1-sonar-large-128k-online, llama-3.1-sonar-huge-128k-online</li>
            </ul>
          </Accordion.Body>
        </Accordion.Item>

        <Accordion.Item eventKey="11">
          <Accordion.Header>What agents do we consider?</Accordion.Header>
          <Accordion.Body>
            We support agents from various frameworks such as:
            <ul>
              <li><a href="https://python.langchain.com/v0.2/docs/integrations/tools/" target="_blank" rel="noopener noreferrer">LangChain</a></li>
              <li><a href="https://llamahub.ai/?tab=tools" target="_blank" rel="noopener noreferrer">LlamaIndex</a></li>
              <li><a href="https://github.com/crewAIInc/crewAI-examples" target="_blank" rel="noopener noreferrer">CrewAI</a></li>
              <li><a href="https://github.com/ComposioHQ/composio/tree/master/cookbook" target="_blank" rel="noopener noreferrer">Composio</a></li>
            </ul>
            Some of our featured agents use various tools like Brave API, Yahoo Finance, and more. We also source and modify example agents from the respective frameworks. 
            Additionally, we have general-purpose assistants like <a href="https://platform.openai.com/docs/assistants/overview" target="_blank" rel="noopener noreferrer">OpenAI’s assistants</a> (e.g., code interpreting, file reading), and tool/API-based examples from <a href="https://github.com/anthropics/anthropic-cookbook" target="_blank" rel="noopener noreferrer">Anthropic</a> and <a href="https://docs.perplexity.ai/home" target="_blank" rel="noopener noreferrer">Perplexity</a>.
          </Accordion.Body>
        </Accordion.Item>

        <Accordion.Item eventKey="12">
          <Accordion.Header>Have more questions?</Accordion.Header>
          <Accordion.Body>
            If you have more questions, feel free to reach out to us via email at <a href="mailto:agentarenateam@gmail.com">agentarenateam@gmail.com</a> or use our <a href="/contact-us">Contact Us</a> form.
          </Accordion.Body>
        </Accordion.Item>
      </Accordion>
    </Container>
  );
};

export default FAQ;
