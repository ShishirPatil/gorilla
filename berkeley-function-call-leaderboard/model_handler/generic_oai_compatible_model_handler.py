from model_handler.handler import BaseHandler
from model_handler.model_style import ModelStyle
from model_handler.utils import (
    convert_to_tool,
    convert_to_function_call,
    augment_prompt_by_languge,
    language_specific_pre_processing,
    ast_parse,
)
from model_handler.constant import (
    GORILLA_TO_OPENAPI,
    GORILLA_TO_PYTHON,
    USER_PROMPT_FOR_CHAT_MODEL,
    SYSTEM_PROMPT_FOR_CHAT_MODEL,
)
from openai import OpenAI
import os, time, json

# TODO: update system_prompt, user_prompt and parsing logic
SYSTEM_PROMPT_FOR_FC_MODEL = """Remember to pay attention to the description of each argument if specified in the tool schema. It may contain hints on the data type of the argument or hints on the expected format of the value.\nFor example: If the tool given to you is:
{'type': 'function', 'function': {'name': 'simple_interest', 'description': 'Calculate simple interest for a certain time period.', 'parameters': {'type': 'object', 'properties': {'principal': {'type': 'integer', 'description': 'The initial amount of money that was invested or loaned out.'}, 'annual_rate': {'type': 'number', 'description': 'The interest rate for a year as a percentage. This is a float type value.', 'format': 'float'}, 'time': {'type': 'integer', 'description': 'The time the money is invested for in years.'}}, 'required': ['principal', 'annual_rate', 'time_in_years']}}}
Then, NOTE that the annual_rate is a float type value. So if the rate of interest is 15% then you should enter 15 and not 0.15. Also note that time is in years.

DO NOT HALLUCINATE PARAMETERS. If you are not sure about a parameter, just leave it out. It's better to leave it out than to hallucinate a value.
However BE SPECIFIC about the parameters that you are sure about. If the user asks for something specific, ONLY RETURN that specific information. Do not return any additional unnecessary information.

For example, suppose the tool given to you is:
[{'type': 'function', 'function': {'name': 'player_stats_getAverages', 'description': 'Get average statistics for a specific player in cricket', 'parameters': {'type': 'object', 'properties': {'player_name': {'type': 'string', 'description': 'The name of the cricket player.'}, 'country': {'type': 'string', 'description': 'The country that player plays for.'}, 'metrics': {'type': 'array', 'items': {'type': 'string', 'enum': ['Runs', 'Wickets', 'Strike Rate']}, 'description': 'Specific metrics to retrieve. If no value is specified, all available metrics will be returned by default.'}}, 'required': ['player_name', 'country']}}}]
And the user query is 'Get the average runs of player 'Sachin Tendulkar'.
Then you should only return the average runs of Sachin Tendulkar. Do not return any additional information. Therefore, the tool_call should specify 'player_name': 'Sachin Tendulkar', 'country': 'India' (since country is a required parameter) and 'metrics': ['Runs'] since the user specifically asked for the average runs, and not the other metrics.
"""



class GenericOAICompatibleModelHandler(BaseHandler):
    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.model_style = ModelStyle.OpenAI
        # TODO: to avoid changing BFCL too much, just passing these as environment variables
        if os.environ.get("MODEL_API_KEY") is None or os.environ.get("MODEL_ENDPOINT_URL") is None or os.environ.get("ENDPOINT_MODEL_NAME") is None:
            raise ValueError("MODEL_API_KEY or MODEL_ENDPOINT_URL or ENDPOINT_MODEL_NAME environment variables are not set. Please set them to use the GenericOAICompatibleModelHandler.")
        self.client = OpenAI(
            api_key=os.environ["MODEL_API_KEY"],
            base_url=os.environ["MODEL_ENDPOINT_URL"],
        )

    def inference(self, prompt,functions,test_category):
        # TODO: do this more elegantly
        API_FAILURE_MESSAGE = None # hacky way to get the error message out of the try block

        if "FC" not in self.model_name:
            prompt = augment_prompt_by_languge(prompt,test_category)
            functions = language_specific_pre_processing(functions,test_category,False)
            message = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT_FOR_CHAT_MODEL,
                },
                {
                    "role": "user",
                    "content": "Questions:"
                    + USER_PROMPT_FOR_CHAT_MODEL.format(
                        user_prompt=prompt, functions=str(functions)
                    ),
                },
            ]
            start_time = time.time()
            response = self.client.chat.completions.create(
                messages=message,
                model=os.environ.get("ENDPOINT_MODEL_NAME", self.model_name),
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
            )
            latency = time.time() - start_time
            result = response.choices[0].message.content
        else:
            prompt = augment_prompt_by_languge(prompt, test_category)
            functions = language_specific_pre_processing(functions, test_category, True)
            if type(functions) is not list:
                functions = [functions]
            message = [
                # {"role": "system", "content": SYSTEM_PROMPT_FOR_FC_MODEL},
                {"role": "user", "content": "Questions:" + prompt}]
            oai_tool = convert_to_tool(
                functions, GORILLA_TO_OPENAPI, self.model_style, test_category, True
            )
            start_time = time.time()
            if len(oai_tool) > 0:
                # bugfix: the cards tool is an "object" without "properties", which breaks outlines
                """
                # looks like this happens in more cases. can I make my solution more generic?
                Functions=[{'name': 'calculate_standard_deviation', 'description': 'This function calculates the standard deviation across different scores for a specific student.', 'parameters': {'type': 'object', 'properties': {'gradeDict': {'type': 'object', 'description': 'A dictionary where keys represent subjects and values represent scores'}}, 'required': ['gradeDict']}}, {'name': 'calculate_average', 'description': 'This function calculates the average grade across different subjects for a specific student.', 'parameters': {'type': 'object', 'properties': {'gradeDict': {'type': 'object', 'description': 'A dictionary where keys represent subjects and values represent scores'}}, 'required': ['gradeDict']}}, {'name': 'highest_grade', 'description': 'This function finds the subject where the student got the highest score.', 'parameters': {'type': 'object', 'properties': {'gradeDict': {'type': 'object', 'description': 'A dictionary where keys represent subjects and values represent scores'}}, 'required': ['gradeDict']}}]
                """
                try:
                    for tool in oai_tool:
                        if 'cards' in tool['function']['parameters']['properties'].keys():
                            tool['function']['parameters']['properties']['cards'] =\
                                {'type': 'object',
                                 'description': 'An object containing the player name as key and the cards as values in a list.',
                                 'properties': {'player_name': {'type': 'string', 'description': 'The name of the player.'},
                                 'cards': {'type': 'array',
                                 'items': {'type': 'string',},
                                 'description': 'List of cards that the player has.'}},
                                }
                        if 'gradeDict' in tool['function']['parameters']['properties'].keys():
                            tool['function']['parameters']['properties']['gradeDict'] =\
                                {'type': 'string',
                                 'description': 'A dictionary where keys represent subjects and values represent scores',
                                 }
                        if 'population' in tool['function']['parameters']['properties'].keys():
                            tool['function']['parameters']['properties']['population'] =\
                                {'type': 'object',
                                 'description': "The description of population. 'adults' is the number of adults in the household. 'children' is the number of children. 'singles' is the number of single adults living alone.",
                                 'required': ['adults', 'children', 'singles'],
                                    'properties': {'adults': {'type': 'integer', 'description': 'The number of adults in the household.'},
                                                   'children': {'type': 'integer', 'description': 'The number of children in the household.'},
                                                   'singles': {'type': 'integer', 'description': 'The number of single adults living alone.'},
                                                  }
                                 }
                except Exception as e:
                    pass
                try:
                    response = self.client.chat.completions.create(
                        messages=message,
                        model=os.environ.get("ENDPOINT_MODEL_NAME", self.model_name).replace("-FC", ""),
                        temperature=self.temperature,
                        max_tokens=self.max_tokens,
                        top_p=self.top_p,
                        tools=oai_tool,
                        tool_choice='auto', # this is important as it let's the model decide when to use FC
                    )
                except Exception as e:
                    print(f"\nError while trying to do FC: {e}\n")
                    print(f"Messages={message}")
                    print(f"Functions={functions}\n")
                    API_FAILURE_MESSAGE = f"API Failure: {e}"
            else:
                # @KS: TODO: Gorilla decided not to use the tool? What's going on here.
                print(f"DEBUG: BFCL decided to not use the tool.")
                print(f"Prompt = {prompt}")
                print(f"Functions = {functions}")
                response = self.client.chat.completions.create(
                    messages=message,
                    model=os.environ.get("ENDPOINT_MODEL_NAME", self.model_name).replace("-FC", ""),
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    top_p=self.top_p,
                )
            latency = time.time() - start_time
            try:
                result = [
                    {func_call.function.name: func_call.function.arguments}
                    for func_call in response.choices[0].message.tool_calls
                ]
            except Exception as e:
                print("Error while trying to extract function calls from response:", e)
                if API_FAILURE_MESSAGE:
                    result = API_FAILURE_MESSAGE
                else:
                    result = response.choices[0].message.content
        metadata = {}
        if API_FAILURE_MESSAGE:
            # do something
            metadata["input_tokens"] = -1
            metadata["output_tokens"] = -1
        else:
            metadata["input_tokens"] = response.usage.prompt_tokens
            metadata["output_tokens"] = response.usage.completion_tokens
        metadata["latency"] = latency
        return result,metadata
    
    def decode_ast(self,result,language="Python"):
        if "FC" not in self.model_name:
            decoded_output = ast_parse(result,language)
        else:
            decoded_output = []
            for invoked_function in result:
                name = list(invoked_function.keys())[0]
                if name == "weather_get_by_coordinates_date":
                    date_field = invoked_function[name].split('"date": ')[1].replace("}", "")
                    invoked_function[name].replace(date_field, f'"{date_field}"')
                params = json.loads(invoked_function[name])
                if language == "Python":
                    pass
                else:
                    # all values of the json are casted to string for java and javascript
                    for key in params:
                        params[key] = str(params[key])
                decoded_output.append({name: params})
        return decoded_output
    
    def decode_execute(self,result):
        if "FC" not in self.model_name:
            decoded_output = ast_parse(result)
            execution_list = []
            for function_call in decoded_output:
                for key, value in function_call.items():
                    execution_list.append(
                        f"{key}({','.join([f'{k}={repr(v)}' for k, v in value.items()])})"
                    )
            return execution_list
        else:
            function_call = convert_to_function_call(result)
            return function_call
