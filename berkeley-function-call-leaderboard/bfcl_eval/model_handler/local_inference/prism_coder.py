"""
PrismCoderHandler: Custom handler for prism-coder.

Supports 7B, 32B, and 72B model variants.
Extends QwenFCHandler with:
1. Multi-turn FC methods (8 abstract methods for inference_multi_turn_FC)
2. Language-aware type coercion (Python-only bool fix for Java/JS compat)
3. Abstention detection for irrelevance scoring
4. Robust JSON extraction from model output

BFCL Scoring Formula: 10% Non-Live + 10% Live + 10% Irrelevance + 30% Multi-Turn + 40% Agentic
"""

import json
import os
import re
import time
from typing import Any

from bfcl_eval.model_handler.local_inference.qwen_fc import QwenFCHandler
from bfcl_eval.model_handler.utils import convert_to_function_call, convert_to_tool
from overrides import override


class PrismCoderHandler(QwenFCHandler):

    ############################################################################
    # System Prompt Override — Abstention Instruction
    ############################################################################

    @override
    def _format_prompt(self, messages, function):
        """Override to inject abstention instruction into the system prompt.
        
        The base QwenFCHandler always says "You may call one or more functions..."
        which trains the model to ALWAYS call a function. We add an explicit
        instruction that the model should respond with plain text when no
        function is relevant to the user's query.
        """
        formatted_prompt = ""

        if len(function) > 0:
            formatted_prompt += "<|im_start|>system\n"
            if messages[0]["role"] == "system":
                formatted_prompt += messages[0]["content"] + "\n\n"

            formatted_prompt += "# Tools\n\nYou may call one or more functions to assist with the user query.\n\nYou are provided with function signatures within <tools></tools> XML tags:\n<tools>"
            # StructXML: Convert JSON tool schemas to XML for better attention head mapping
            for tool in function:
                formatted_prompt += f"\n<function>\n  <name>{tool.get('name', '')}</name>\n  <description>{tool.get('description', '')}</description>\n"
                params = tool.get('parameters', {})
                props = params.get('properties', {})
                required = params.get('required', [])
                if props:
                    formatted_prompt += "  <parameters>\n"
                    for prop_name, prop_data in props.items():
                        req = "required" if prop_name in required else "optional"
                        ptype = prop_data.get('type', 'string')
                        pdesc = prop_data.get('description', '')
                        formatted_prompt += f'    <parameter name="{prop_name}" type="{ptype}" presence="{req}">\n'
                        if 'enum' in prop_data:
                            formatted_prompt += f"      <enum>{', '.join(str(e) for e in prop_data['enum'])}</enum>\n"
                        formatted_prompt += f"      <description>{pdesc}</description>\n"
                        formatted_prompt += "    </parameter>\n"
                    formatted_prompt += "  </parameters>\n"
                formatted_prompt += "</function>"
            formatted_prompt += '\n</tools>\n\n'
            formatted_prompt += 'For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:\n<tool_call>\n{"name": <function-name>, "arguments": <args-json-object>}\n</tool_call>\n\n'
            # xLAM-proven strict execution + abstention + agentic answer instructions
            formatted_prompt += 'IMPORTANT RULES:\n'
            formatted_prompt += '1. If NONE of the provided functions are relevant to the user\'s query, respond with a plain text message. Do NOT call any function when the query is unrelated to ALL available tools.\n'
            formatted_prompt += '2. Do not interpret or guess information. Wait for tool results to be returned before responding.\n'
            formatted_prompt += '3. If a tool result provides the answer, output it directly and concisely. Do not add conversational filler.\n'
            formatted_prompt += '4. If the user\'s input lacks required parameters, ask for clarification.\n'
            formatted_prompt += '5. When you have the final answer, state it clearly. Example: "The result is X."\n'
            formatted_prompt += '6. Do not hallucinate optional parameters. If the user does not explicitly provide a value for an optional parameter, do not include that parameter in your JSON arguments.\n'
            formatted_prompt += '7. When saving data to memory or a database, use the EXACT variable names and values provided by the user or the tool. Do not summarize or alter keys.<|im_end|>\n'
        else:
            if messages[0]["role"] == "system":
                formatted_prompt += (
                    f"<|im_start|>system\n{messages[0]['content']}<|im_end|>\n"
                )

        # Replicate the rest of the parent's _format_prompt logic
        last_query_index = len(messages) - 1
        for offset, message in enumerate(reversed(messages)):
            idx = len(messages) - 1 - offset
            if (
                message["role"] == "user"
                and type(message["content"]) == str
                and not (
                    message["content"].startswith("<tool_response>")
                    and message["content"].endswith("</tool_response>")
                )
            ):
                last_query_index = idx
                break

        for idx, message in enumerate(messages):
            content = message.get("content", "")
            if not isinstance(content, str):
                content = ""

            # Extract reasoning_content if present
            reasoning_content = ""
            if message.get("reasoning_content"):
                reasoning_content = message["reasoning_content"]
            elif message["role"] == "assistant" and "</|synalux_think|>" in content:
                reasoning_content = content.split("</|synalux_think|>")[0].rstrip("\n").split("<|synalux_think|>")[-1].lstrip("\n")
                content = content.split("</|synalux_think|>")[-1].lstrip("\n")
            elif message["role"] == "assistant" and "</think>" in content:
                reasoning_content = content.split("</think>")[0].rstrip("\n").split("<think>")[-1].lstrip("\n")
                content = content.split("</think>")[-1].lstrip("\n")

            if message["role"] == "user" or (
                message["role"] == "system" and idx > 0
            ):
                formatted_prompt += (
                    f"<|im_start|>{message['role']}\n{content}<|im_end|>\n"
                )
            elif message["role"] == "assistant":
                # Only inject <think> for the response we're about to generate (after last query)
                # For history messages, include reasoning if present
                if idx > last_query_index:
                    if reasoning_content:
                        formatted_prompt += f"<|im_start|>assistant\n<|synalux_think|>\n{reasoning_content}\n</|synalux_think|>\n\n{content}"
                    else:
                        formatted_prompt += f"<|im_start|>assistant\n<|synalux_think|>\n\n</|synalux_think|>\n\n{content}"
                else:
                    formatted_prompt += f"<|im_start|>assistant\n{content}"

                if "tool_calls" in message and message["tool_calls"]:
                    for tool_call in message["tool_calls"]:
                        tc = tool_call.get("function", tool_call)
                        args = tc.get("arguments", {})
                        if isinstance(args, str):
                            args_str = args
                        else:
                            args_str = json.dumps(args)
                        formatted_prompt += f'\n<tool_call>\n{{"name": "{tc["name"]}", "arguments": {args_str}}}\n</tool_call>'
                formatted_prompt += "<|im_end|>\n"
            elif message["role"] == "tool":
                # Native Qwen2.5 tool role — matches base model pre-training template
                formatted_prompt += f"<|im_start|>tool\n{content}<|im_end|>\n"

        # Only inject <think> tags for models that support reasoning/thinking mode
        # Stock Qwen2.5-Coder models do NOT support <think> tags.
        # Set PRISM_ENABLE_THINKING=1 if using a fine-tuned model with thinking support.
        enable_thinking = os.getenv("PRISM_ENABLE_THINKING", "0") == "1"
        if enable_thinking:
            formatted_prompt += "<|im_start|>assistant\n<|synalux_think|>\n\n</|synalux_think|>\n\n"
        else:
            formatted_prompt += "<|im_start|>assistant\n"
        return formatted_prompt

    ############################################################################
    # Decode Methods — Language-Aware Type Coercion
    ############################################################################

    @override
    def decode_ast(self, result, language, has_tool_call_tag):
        """Override to handle abstention and language-aware type coercion."""
        
        tool_calls = self._extract_tool_calls(result)
        
        if not tool_calls:
            return []
        
        if type(tool_calls) != list or any(type(item) != dict for item in tool_calls):
            raise ValueError(f"Model did not return a list of function calls: {result}")
        
        decoded = []
        for call in tool_calls:
            name = call.get("name", "")
            args = call.get("arguments", {})
            # Language-aware type coercion: only fix types for Python
            fixed_args = self._fix_argument_types(args, language=language)
            decoded.append({name: fixed_args})
        
        return decoded

    @override
    def decode_execute(self, result, has_tool_call_tag):
        """Override to handle abstention + type coercion + eval()-safe formatting.
        
        CRITICAL: This method's output is literally eval()'d by multi_turn_utils.py.
        Uses xLAM's proven repr(v) pattern for eval() safety.
        Applies _fix_argument_types for Python type coercion (bool/null strings).
        """
        
        tool_calls = self._extract_tool_calls(result)
        
        if not tool_calls:
            return []
        
        if type(tool_calls) != list or any(type(item) != dict for item in tool_calls):
            raise ValueError(f"Model did not return a list of function calls: {result}")
        
        execution_list = []
        for item in tool_calls:
            if type(item) == str:
                item = eval(item)
            name = item["name"]
            arguments = item.get("arguments", {})
            # CRITICAL FIX: Apply type coercion (Python-only) before execution
            arguments = self._fix_argument_types(arguments, language="Python")
            # Use xLAM's repr(v) pattern for eval()-safe argument formatting
            execution_list.append(
                f"{name}({','.join([f'{k}={repr(v)}' for k, v in arguments.items()])})"
            )
        return execution_list

    ############################################################################
    # FC Mode Methods — Multi-Turn Support
    ############################################################################

    @override
    def _pre_query_processing_FC(self, inference_data: dict, test_entry: dict) -> dict:
        """Initialize inference data for FC mode multi-turn."""
        functions: list = test_entry.get("function", [])
        inference_data["message"] = []
        inference_data["function"] = functions
        return inference_data

    @override
    def _compile_tools(self, inference_data: dict, test_entry: dict) -> dict:
        """Store the function definitions for prompt formatting.
        
        For our prompting-style FC handler, we don't need OpenAI-style tool conversion.
        We pass raw function definitions directly to _format_prompt.
        """
        inference_data["function"] = test_entry.get("function", [])
        return inference_data

    @override
    def add_first_turn_message_FC(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        """Add the first turn message(s) to the conversation history."""
        inference_data["message"].extend(first_turn_message)
        return inference_data

    @override
    def _add_next_turn_user_message_FC(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        """Add subsequent turn user messages to conversation history."""
        inference_data["message"].extend(user_message)
        return inference_data

    @override
    def _query_FC(self, inference_data: dict):
        """Query the model in FC mode using our prompting-style approach.
        
        Since prism-coder uses Ollama's OpenAI-compatible completions API,
        we build the prompt via _format_prompt and call the completions endpoint.
        This is identical to _query_prompting but uses FC inference_data.
        """
        function: list[dict] = inference_data["function"]
        message: list[dict] = inference_data["message"]

        formatted_prompt: str = self._format_prompt(message, function)
        inference_data["inference_input_log"] = {"formatted_prompt": formatted_prompt}

        # Tokenize to manage context window
        input_token_count = len(self.tokenizer.tokenize(formatted_prompt))

        if self.max_context_length < input_token_count + 2:
            leftover_tokens_count = 1000
        else:
            leftover_tokens_count = min(
                4096,
                self.max_context_length - input_token_count - 2,
            )

        start_time = time.time()
        api_response = self.client.completions.create(
            model=self.model_path_or_id,
            temperature=self.temperature,
            prompt=formatted_prompt,
            max_tokens=leftover_tokens_count,
            timeout=72000,
        )
        end_time = time.time()

        return api_response, end_time - start_time

    @override
    def _parse_query_response_FC(self, api_response: Any) -> dict:
        """Parse the FC mode response — extract tool calls and build chat history entry.
        
        Returns a dict with:
        - model_responses: raw text for decode_execute
        - model_responses_message_for_chat_history: structured message for conversation
        - input_token, output_token: token counts
        - reasoning_content: extracted <think> content
        """
        model_response = api_response.choices[0].text
        extracted_tool_calls = self._extract_tool_calls(model_response)

        # Extract reasoning_content
        reasoning_content = ""
        cleaned_response = model_response
        if "</|synalux_think|>" in model_response:
            parts = model_response.split("</|synalux_think|>")
            reasoning_content = parts[0].rstrip("\n").split("<|synalux_think|>")[-1].lstrip("\n")
            cleaned_response = parts[-1].lstrip("\n")
        elif "</think>" in model_response:
            parts = model_response.split("</think>")
            reasoning_content = parts[0].rstrip("\n").split("<think>")[-1].lstrip("\n")
            cleaned_response = parts[-1].lstrip("\n")

        # Build the message for chat history
        if len(extracted_tool_calls) > 0:
            # Convert extracted tool calls to the format expected by _format_prompt
            tool_calls_for_history = []
            for tc in extracted_tool_calls:
                tool_calls_for_history.append({
                    "function": {
                        "name": tc.get("name", ""),
                        "arguments": tc.get("arguments", {}),
                    }
                })
            
            # Preserve any conversational text outside of tool_call blocks
            content_only = re.sub(r"<tool_call>.*?</tool_call>", "", cleaned_response, flags=re.DOTALL).strip()
            model_responses_message_for_chat_history = {
                "role": "assistant",
                "content": content_only,
                "tool_calls": tool_calls_for_history,
            }
        else:
            model_responses_message_for_chat_history = {
                "role": "assistant",
                "content": cleaned_response,
            }
        
        model_responses_message_for_chat_history["reasoning_content"] = reasoning_content

        return {
            "model_responses": cleaned_response,
            "reasoning_content": reasoning_content,
            "model_responses_message_for_chat_history": model_responses_message_for_chat_history,
            "input_token": api_response.usage.prompt_tokens,
            "output_token": api_response.usage.completion_tokens,
        }

    @override
    def _add_assistant_message_FC(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        """Add assistant response (with tool calls) to conversation history."""
        inference_data["message"].append(
            model_response_data["model_responses_message_for_chat_history"]
        )
        return inference_data

    @override
    def _add_execution_results_FC(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        """Add tool execution results to conversation history.
        
        Results are formatted as <tool_response> within a user message,
        matching the Qwen chat template for tool responses.
        """
        for execution_result in execution_results:
            # === REFLEXION: Self-Correction on Tool Errors ===
            # When a tool returns an error, inject a corrective instruction
            # so the model analyzes the failure instead of repeating broken calls.
            if "Error during execution:" in execution_result or (
                "error" in execution_result.lower() and len(execution_result) < 500
            ):
                execution_result = (
                    f"TOOL ERROR: {execution_result}\n"
                    f"SYSTEM INSTRUCTION: The previous tool call failed. Do not repeat the same arguments. "
                    f"Analyze why the API rejected your input, correct the parameter types or values, and try again "
                    f"with a different approach."
                )
            
            inference_data["message"].append({
                "role": "tool",
                "content": execution_result,
            })
        return inference_data

    ############################################################################
    # Type Coercion — Language-Aware
    ############################################################################

    @staticmethod
    def _fix_argument_types(args, language="Python"):
        """Fix common type coercion issues in function call arguments.
        
        LANGUAGE-AWARE: Only applies bool/null coercion for Python.
        Java and JavaScript expect string values for String parameters,
        so "true"/"false" must remain as strings.
        
        Issues fixed (Python only):
        1. Stringified booleans: "true"/"false" -> True/False
        2. Stringified null: "null"/"none" -> None
        
        Issues fixed (all languages):
        3. Stringified JSON objects: '{"key": "val"}' -> {"key": "val"}
        4. Extra-quoted strings: "'USERSPACE1'" -> "USERSPACE1"
        """
        if not isinstance(args, dict):
            return args
        
        fixed = {}
        for key, value in args.items():
            fixed[key] = PrismCoderHandler._fix_value(value, language=language)
        return fixed
    
    @staticmethod
    def _fix_value(value, language="Python"):
        """Recursively fix a single value."""
        if isinstance(value, str):
            # Fix stringified booleans — ONLY for Python
            if language == "Python":
                if value.lower() == "true":
                    return True
                if value.lower() == "false":
                    return False
                if value.lower() == "null" or value.lower() == "none":
                    return None
            
            # Fix extra-quoted strings: "'something'" -> "something" (all languages)
            if len(value) >= 2 and value[0] == "'" and value[-1] == "'":
                return value[1:-1]
            
            # Fix stringified JSON objects/arrays (all languages)
            if (value.startswith("{") and value.endswith("}")) or \
               (value.startswith("[") and value.endswith("]")):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, dict):
                        return PrismCoderHandler._fix_argument_types(parsed, language=language)
                    elif isinstance(parsed, list):
                        return [PrismCoderHandler._fix_value(v, language=language) for v in parsed]
                    return parsed
                except json.JSONDecodeError:
                    pass
            
            return value
        
        elif isinstance(value, dict):
            return PrismCoderHandler._fix_argument_types(value, language=language)
        
        elif isinstance(value, list):
            return [PrismCoderHandler._fix_value(v, language=language) for v in value]
        
        return value

    ############################################################################
    # Tool Call Extraction
    ############################################################################

    @staticmethod
    @override
    def _extract_tool_calls(input_string):
        """Extract tool calls from model output.
        
        Handles:
        1. Standard <tool_call> tag extraction (Qwen native format)
        2. Bare JSON objects (prism-coder format)
        3. Abstention (no tool call - returns empty list)
        """
        # Strip <think>...</think> blocks first
        cleaned = re.sub(r"<think>.*?</think>", "", input_string, flags=re.DOTALL).strip()
        cleaned = re.sub(r"<\|synalux_think\|>.*?</\|synalux_think\|>", "", cleaned, flags=re.DOTALL).strip()
        
        # If the output doesn't contain any JSON-like content, it's an abstention
        if not re.search(r'[{]', cleaned):
            return []
        
        # Try the standard <tool_call> tag extraction (Qwen native format)
        # Match with or without newlines around JSON content
        pattern = r"<tool_call>\s*(.*?)\s*</tool_call>"
        matches = re.findall(pattern, cleaned, re.DOTALL)
        if matches:
            result = []
            for match in matches:
                try:
                    result.append(json.loads(match.strip()))
                except Exception:
                    pass
            if result:
                return result

        # Try to parse the entire output as a single JSON tool call
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict) and "name" in parsed:
                return [parsed]
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

        # Try to find all JSON objects in the output (for parallel calls)
        json_objects = PrismCoderHandler._find_json_objects(cleaned)
        if json_objects:
            return json_objects

        # Try line-by-line JSON parsing as last resort
        result = []
        for line in cleaned.split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
                if isinstance(parsed, dict) and "name" in parsed:
                    result.append(parsed)
            except json.JSONDecodeError:
                continue
        
        return result
    
    @staticmethod
    def _find_json_objects(text):
        """Find all complete JSON objects with 'name' key in text using bracket matching."""
        result = []
        i = 0
        while i < len(text):
            if text[i] == '{':
                depth = 0
                start = i
                for j in range(i, len(text)):
                    if text[j] == '{':
                        depth += 1
                    elif text[j] == '}':
                        depth -= 1
                        if depth == 0:
                            candidate = text[start:j+1]
                            try:
                                parsed = json.loads(candidate)
                                if isinstance(parsed, dict) and "name" in parsed:
                                    result.append(parsed)
                            except json.JSONDecodeError:
                                pass
                            i = j + 1
                            break
                else:
                    i += 1
            else:
                i += 1
        return result
