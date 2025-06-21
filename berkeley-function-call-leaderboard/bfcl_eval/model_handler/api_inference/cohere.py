import ast
import json
import os
import time
from typing import Any, Optional

import cohere
from bfcl_eval.model_handler.base_handler import BaseHandler
from bfcl_eval.constants.type_mappings import GORILLA_TO_OPENAPI
from bfcl_eval.model_handler.model_style import ModelStyle
from bfcl_eval.model_handler.utils import (
    convert_to_tool,
    func_doc_language_specific_pre_processing,
    retry_with_backoff,
)
from tenacity.stop import stop_after_attempt


class CohereHandler(BaseHandler):
    """
    A handler class for interacting with Cohere's API, specifically designed for function calling capabilities. Inherits from BaseHandler and implements various methods for processing and generating responses using Cohere's models.
    """
    client: cohere.ClientV2

    def __init__(self, model_name: str, temperature: float) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.COHERE
        self.is_fc_model = True
        self.client = cohere.ClientV2(api_key=os.getenv("COHERE_API_KEY"))

    def decode_ast(self, result: list[dict[str, Any]], language: str="Python") -> list[dict[str, Any]]:
        """
        Decodes the AST (Abstract Syntax Tree) representation of tool calls from Cohere's response format into a more standardized dictionary format.
        
        Args:
            result (list[dict[str, Any]]): The raw tool call results from Cohere's API
            language (str): The programming language of the output (default: 'Python')
        
        Returns:
            list[dict[str, Any]]: A list of decoded tool calls in format {tool_name: parameters}
        """
        decoded_output = []
        if isinstance(result, list):
            for tool_call in result:
                name = tool_call["tool_name"]
                params = tool_call["parameters"]
                decoded_output.append({name: params})
        return decoded_output

    def decode_execute(self, result: list[dict[str, Any]]) -> list[str]:
        """
        Converts tool call results into executable code strings.
        
        Args:
            result (list[dict[str, Any]]): The tool call results
        
        Returns:
            list[str]: List of executable code strings representing the tool calls
        """
        execution_list = []
        if isinstance(result, list):
            for tool_call in result:
                parameter_key_value_list = []
                for parameter_name, parameter_value in tool_call["parameters"].items():
                    parameter_key_value_list.append("{}={}".format(parameter_name, repr(parameter_value)))
                execution_list.append("{}({})".format(tool_call["tool_name"], ",".join(parameter_key_value_list)))
        return execution_list

    #### FC methods ####

    def _query_FC(self, inference_data: dict) -> tuple[dict[str, Any], float]:
        """
        Main method for querying Cohere's API with function calling capabilities.
        
        Args:
            inference_data (dict): Contains chat history, system message, and tools
        
        Returns:
            tuple[dict[str, Any], float]: Metadata about the response and the latency
        """
        if system_message := inference_data.get("system_message"):
            system_turn = [
                cohere.SystemChatMessageV2(
                    role="system",
                    content=system_message,
                )
            ]
        else:
            system_turn = []
        all_chat_turns = system_turn + inference_data["chat_turns"]

        response, latency = self.generate_with_backoff(
            messages=all_chat_turns,
            tools=[load_cohere_tool(tool=tool) for tool in inference_data["tools"]],
        )

        model_tool_calls = []
        chat_turn_to_append = cohere.AssistantChatMessageV2(role="assistant")
        response_message = response.message
        if response_message.tool_calls:
            chat_turn_to_append.tool_calls = response_message.tool_calls
            for tool_call in response_message.tool_calls:
                model_tool_calls.append(
                    {
                        "tool_name": tool_call.function.name,
                        "parameters": json.loads(tool_call.function.arguments),
                    }
                )
        if response_message.tool_plan:
            chat_turn_to_append.tool_plan = response_message.tool_plan
        if response_message.content:
            chat_turn_to_append.content = [
                cohere.TextAssistantMessageContentItem(text=msg.text, type="text")
                for msg in response_message.content
            ]
        if response_message.citations:
            chat_turn_to_append.citations = response_message.citations
        inference_data["chat_turns"].append(chat_turn_to_append)

        input_token: float | None = None
        output_token: float | None = None
        if response.usage and response.usage.billed_units:
            input_token = response.usage.billed_units.input_tokens
            output_token = response.usage.billed_units.output_tokens

        metadata = {
            "model_responses": chat_turn_to_append.content if chat_turn_to_append.content else None,
            "tool_calls": model_tool_calls,
            "chat_history": [],
            "input_token": input_token or 0,
            "output_token": output_token or 0,
        }
        return metadata, latency

    @retry_with_backoff(error_type=Exception, stop=stop_after_attempt(5), reraise=True)
    def generate_with_backoff(
        self,
        messages: list,
        tools: list[cohere.types.ToolV2]
    ) -> tuple[cohere.types.ChatResponse, float]:
        """
        Wrapper for Cohere's chat API with retry logic for failed requests.
        
        Args:
            messages (list): List of chat messages
            tools (list[cohere.types.ToolV2]): List of tools available for function calling
        
        Returns:
            tuple[cohere.types.ChatResponse, float]: The API response and request latency
        """
        start_time = time.time()
        api_response = self.client.chat(
            model=self.model_name.replace("-FC", ""),
            messages=messages,
            tools=tools,
            citation_options=cohere.CitationOptions(mode="OFF"),
            temperature=self.temperature,
        )
        end_time = time.time()

        return api_response, end_time - start_time

    def _pre_query_processing_FC(self, inference_data: dict, test_entry: dict) -> dict:
        """
        Preprocesses the test entry data before querying the API.
        
        Args:
            inference_data (dict): The inference data structure
            test_entry (dict): The test case data
        
        Returns:
            dict: Updated inference data
        """
        turns = []
        for turn_idx, turn in enumerate(test_entry["question"]):
            if turn_idx == 0:  # we only extract system message from the first turn
                system_message = load_system_message(turn)
                if system_message:
                    inference_data["system_message"] = system_message  # we log system message if necessary
            if len(turn) > 0:
                turns.append(preprocess_chat_turns(turn))
            else:
                turns.append([])  # for miss_func categories, the turn to supplement function will be empty
        assert len(turns) == len(test_entry["question"])
        test_entry["question"] = turns
        return inference_data

    def _compile_tools(self, inference_data: dict, test_entry: dict) -> dict:
        """
        Compiles and processes the tools/functions for function calling.
        
        Args:
            inference_data (dict): The inference data structure
            test_entry (dict): The test case data
        
        Returns:
            dict: Updated inference data with compiled tools
        """
        functions: list = test_entry["function"]
        test_category: str = test_entry["id"].rsplit("_", 1)[0]

        functions = func_doc_language_specific_pre_processing(functions, test_category)
        tools = convert_to_tool(functions, GORILLA_TO_OPENAPI, self.model_style)
        inference_data["tools"] = tools

        return inference_data

    def _parse_query_response_FC(self, api_response: Any) -> dict:
        """
        Parses the raw API response into a standardized format.
        
        Args:
            api_response (Any): The raw API response
        
        Returns:
            dict: Parsed response containing model responses and tool calls
        """
        if len(api_response["tool_calls"]) > 0:  # non empty tool call list
            model_responses = api_response["tool_calls"]  # list: {"tool_name": , "parameters"}
        else:
            if isinstance(api_response["model_responses"], list):
                model_responses = []
                for item in api_response["model_responses"]:
                    if isinstance(item, cohere.types.TextAssistantMessageContentItem):
                        model_responses.append(item.text)
                    else:
                        model_responses.append(item)
                model_responses = "\n".join(model_responses)
            else:
                model_responses = api_response["model_responses"]

        return {
            "model_responses": model_responses,
            "tool_calls": api_response["tool_calls"],
            "chat_history": api_response["chat_history"],
            "input_token": api_response["input_token"],
            "output_token": api_response["output_token"],
        }

    def add_first_turn_message_FC(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        """
        Adds the initial message(s) to start a conversation.
        
        Args:
            inference_data (dict): The inference data structure
            first_turn_message (list[dict]): The initial message(s)
        
        Returns:
            dict: Updated inference data with initial messages
        """
        chat_turns = []
        for message in first_turn_message:
            message_role = message["role"]
            assert message_role in ["user", "assistant"], "message role must be in ['user', 'assistant']"
            if message_role == "user":
                chat_turns.append(cohere.UserChatMessageV2(role="user", content=message["content"]))
            else:
                chat_turns.append(
                    cohere.AssistantChatMessageV2(
                        role="assistant",
                        content=message["content"],
                    )
                )
        inference_data["chat_turns"] = chat_turns
        inference_data["raw_prompt"] = []
        inference_data["raw_completion"] = []
        return inference_data

    def _add_next_turn_user_message_FC(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        """
        Adds subsequent user messages to the conversation.
        
        Args:
            inference_data (dict): The inference data structure
            user_message (list[dict]): The user message(s) to add
        
        Returns:
            dict: Updated inference data with new messages
        """
        assert "chat_turns" in inference_data, "expected chat_turns to be present"
        for message in user_message:
            message_role = message["role"]
            if message_role == "user":
                inference_data["chat_turns"].append(
                    cohere.UserChatMessageV2(role="user", content=message["content"]))
            elif message_role == "assistant":
                inference_data["chat_turns"].append(
                    cohere.AssistantChatMessageV2(
                        role="assistant",
                        content=message["content"],
                    )
                )
            else:
                raise Exception(f"Role {message_role} is undefined!")
        if inference_data["chat_turns"][-1].role != "user":
            # if last turn is not user turn - we suffixing a user turn at the end of the conversation history
            inference_data["chat_turns"].append(cohere.UserChatMessageV2(role="user", content=""))
        return inference_data

    def _add_assistant_message_FC(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        """
        Placeholder method for adding assistant messages (not needed for Cohere).
        
        Args:
            inference_data (dict): The inference data structure
            model_response_data (dict): The model response data
        
        Returns:
            dict: Unmodified inference data
        """
        # Cohere has all the messages in the chat history already, so no need to add anything here
        return inference_data

    def _add_execution_results_FC(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        """
        Adds execution results of tool calls to the conversation history.
        
        Args:
            inference_data (dict): The inference data structure
            execution_results (list[str]): Results of tool executions
            model_response_data (dict): The model response data
        
        Returns:
            dict: Updated inference data with execution results
        """
        if execution_results:
            # non-empty execution_results, the last turn of inference_data["chat_turns"] must be a tool use turn
            # otherwise, do nothing
            assert (
                inference_data["chat_turns"][-1].role == "assistant"
            ), "last turn must be tool use turn and from the assistant"
            assert inference_data["chat_turns"][-1].tool_calls, "last turn must have tool calls"
            assert len(inference_data["chat_turns"][-1].tool_calls) == len(
                execution_results
            ), "Number of execution result must match number of tool calls from last turn!"
            tool_call_messages = []
            for tool_call, execution_result in zip(inference_data["chat_turns"][-1].tool_calls, execution_results):
                tool_call_id = tool_call.id
                try:
                    tool_execution_result = ast.literal_eval(execution_result)
                except:
                    tool_execution_result = execution_result
                if isinstance(tool_execution_result, dict):
                    if "id" in tool_execution_result:
                        tool_execution_result["ID"] = tool_execution_result["id"]
                        del tool_execution_result["id"]
                    result_to_render = json.dumps(tool_execution_result)
                else:
                    result_to_render = execution_result
                one_tool_call_output = cohere.ToolChatMessageV2(
                    tool_call_id=tool_call_id,
                    content=[
                        cohere.TextToolContent(type="text", text=result_to_render),
                    ],
                )
                tool_call_messages.append(one_tool_call_output)
            inference_data["chat_turns"].extend(tool_call_messages)
        return inference_data


def load_system_message(all_messages: list[dict]) -> Optional[str]:
    """
    Extracts the system message from a list of chat messages.
    
    Args:
        all_messages (list[dict]): List of chat messages
    
    Returns:
        Optional[str]: The system message content if found, else None
    """
    for message in all_messages:
        if message["role"] == "system":
            return message["content"]
    return None


def preprocess_chat_turns(all_messages: list[dict]) -> list[dict]:
    """
    Filters out system messages from chat history.
    
    Args:
        all_messages (list[dict]): List of chat messages
    
    Returns:
        list[dict]: Filtered messages without system messages
    """
    processed_messages: list[dict] = []
    for message in all_messages:
        if message["role"] == "system":
            continue  # skip system message, it has been logged in inference_data
        processed_messages.append(message)
    return processed_messages


def load_cohere_tool(tool: dict) -> cohere.ToolV2:
    """
    Converts a tool specification into Cohere's ToolV2 format.
    
    Args:
        tool (dict): The tool specification
    
    Returns:
        cohere.ToolV2: The tool in Cohere's format
    """
    function = tool["function"]
    return cohere.ToolV2(
        type="function",
        function=cohere.ToolV2Function(
            name=function["name"],
            description=function["description"],
            parameters=function["parameters"],
        ),
    )