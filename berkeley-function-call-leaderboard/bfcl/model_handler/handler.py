from bfcl.model_handler.model_style import ModelStyle
import json, os

class BaseHandler:
    model_name: str
    model_style: ModelStyle

    def __init__(self, model_name, temperature=0.001, top_p=1, max_tokens=1000) -> None:
        self.model_name = model_name
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens

    def inference(self, prompt, functions, test_category):
        # This method is used to retrive model response for each model.
        pass

    def decode_ast(self, result, language="Python"):
        # This method takes raw model output and convert it to standard AST checker input.
        pass

    def decode_execute(self, result):
        # This method takes raw model output and convert it to standard execute checker input.
        pass

    def write(self, result):
        model_name_dir = self.model_name.replace("/", "_")
        os.makedirs(f"./result/{model_name_dir}", exist_ok=True)
        
        if type(result) is dict:
            result = [result]
            
        for entry in result:
            test_category = entry["id"].rsplit("_", 1)[0]
            file_to_write = f"BFCL_v2_{test_category}_result.json"
            file_to_write = f"./result/{model_name_dir}/{file_to_write}"
            
            with open(file_to_write, "a+") as f:
                f.write(json.dumps(entry) + "\n")
