from bfcl.model_handler.base_handler import BaseHandler
from bfcl.model_handler.model_style import ModelStyle
from bfcl.model_handler.utils import (
    convert_to_tool,
    convert_to_function_call,
    func_doc_language_specific_pre_processing,
)
from bfcl.model_handler.constant import GORILLA_TO_OPENAPI
from openai import OpenAI
import os, time, json
import requests
import hashlib

class UniGPTHandler(BaseHandler):
    def __init__(self, model_name, temperature=0.0, top_p=1, max_tokens=1000) -> None:
        super().__init__(model_name, temperature, top_p, max_tokens)
        self.model_style = ModelStyle.OpenAI
        self.base_url = "https://unigpt-api.hivoice.cn/rest/v1.1/chat/completions"
        self.secret = ''
        self.appkey = ''
    
    def get_sha256(self,uid,timestamp):
        hs = hashlib.sha256()
        hs.update((self.appkey +uid+ timestamp + self.secret).encode('utf-8'))
        signature = hs.hexdigest().upper()
        return signature
    
    def inference(self, prompt, functions, test_category):
        def func_doc_language_specific_pre_processing(function, test_category):
            if len(function) == 0:
                return function
            assert type(function) == list
            for item in function:
                func_description = item["description"]
                item["description"] = item["description"]
                properties = item["parameters"]["properties"]
                if test_category == "java":
                    for key, value in properties.items():
                        if value["type"] == "any":
                            properties[key]["description"] += (
                                " This parameter can be of any type of Java object in string representation."
                            )
                        else:
                            value["description"] += (
                                f" This is Java {value['type']} type parameter in string representation."
                            )
                        if value["type"] == "ArrayList" or value["type"] == "Array":
                            value["description"] += (
                                f" The list elements are of type {value['items']['type']}; they are not in string representation."
                            )
                            del value["items"]
                            
                        value["type"] = "string"
                        
                elif test_category == "javascript":
                    for key, value in properties.items():
                        if value["type"] == "any":
                            properties[key]["description"] += (
                                " This parameter can be of any type of JavaScript object in string representation."
                            )
                        else:
                            value["description"] += (
                                f" This is JavaScript {value['type']} type parameter in string representation."
                            )
                        if value["type"] == "array":
                            value["description"] += (
                                f" The list elements are of type {value['items']['type']}; they are not in string representation."
                            )
                            del value["items"]
                        
                        if value["type"] == "dict":
                            if "properties" in value:    # not every dict has properties
                                value["description"] += (
                                    f" The dictionary entries have the following schema; they are not in string representation. {json.dumps(value['properties'])}"
                                )
                                del value["properties"]

                        value["type"] = "string"
                        
            return function
        functions = func_doc_language_specific_pre_processing(functions, test_category)        
        if type(functions) is not list:
            functions = [functions]
        messages = prompt
        oai_tool = convert_to_tool(
            functions, GORILLA_TO_OPENAPI, self.model_style, test_category
        )
        millis = int(round(time.time() * 1000))
        strmil=str(millis)
        udid="device0001"
        sign=self.get_sha256(udid,strmil)

        headers = {
            'appkey': self.appkey,
            'udid': udid,
            'timestamp': strmil,
            'stream': "false",
            'sign' : sign
        }
        model_name_map={"unigpt2.0":"UniGPT_v2.0_0910","unigpt4.0":"UniGPT_v4.0_0910"}
        raw_request = {
        "messages": messages,
        "tools": oai_tool,
        "model": model_name_map[self.model_name]
        }
        
        content = requests.post(self.base_url, headers=headers, json=raw_request)
        res = content.content.decode()
        res = json.loads(res)["result"]['choices'][0]['message']
        try:
            result = [
                {func_call["function"]["name"]: func_call["function"]["arguments"]}
                for func_call in res['tool_calls']
            ]
        except Exception as e:
            result = res.choices[0].message.content
        
        metadata = {}
        metadata["input_tokens"] = 0
        metadata["output_tokens"] = 0
        metadata["latency"] = 0
        return result, metadata

    def decode_ast(self,result,language="Python"):
        decoded_output = []
        for invoked_function in result:
            name = list(invoked_function.keys())[0]
            params = invoked_function[name]
            try:
                params = ast.literal_eval(params)
            except:
                try:
                    params = json.loads(params)
                except:
                    try:
                        params = eval(params)
                    except:
                        pass
            if isinstance(params,dict):
                decoded_output.append({name: params})
        return decoded_output

    def decode_execute(self,result):
        decoded_output = []
        for invoked_function in result:
            name = list(invoked_function.keys())[0]
            params = invoked_function[name]
            try:
                params = ast.literal_eval(params)
            except:
                try:
                    params = json.loads(params)
                except:
                    try:
                        params = eval(params)
                    except:
                        pass
            if isinstance(params,dict):
                decoded_output.append({name: json.dumps(params)})
        function_call = convert_to_function_call(decoded_output)
        return function_call
