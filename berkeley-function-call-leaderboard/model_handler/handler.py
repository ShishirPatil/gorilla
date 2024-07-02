from model_handler.model_style import ModelStyle
import json, os
import aiofiles

class BaseHandler:
    model_name: str
    model_style: ModelStyle

    def __init__(self, model_name, temperature=0.7, top_p=1, max_tokens=1000) -> None:
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

    ## make the write function async
    async def write(self, result, file_to_open):
        # Ensure the result directories exist
        if not os.path.exists("./result"):
            os.mkdir("./result")
        if not os.path.exists("./result/" + self.model_name):
            os.mkdir("./result/" + self.model_name)

        # Use aiofiles to write asynchronously
        async with aiofiles.open(
            "./result/"
            + self.model_name
            + "/"
            + file_to_open.replace(".json", "_result.json"),
            mode='a+'
        ) as f:
            await f.write(json.dumps(result) + "\n")

    def load_result(self, test_category):
        # This method is used to load the result from the file.
        result_list = []
        with open(
            f"./result/{self.model_name}/gorilla_openfunctions_v1_test_{test_category}_result.json"
        ) as f:
            for line in f:
                result_list.append(json.loads(line))
        return result_list
    
    # open the result file and sort it on idx
    def sort_results(self,file_to_open):
        path = "./result/"+ self.model_name+ "/" + file_to_open.replace(".json", "_result.json")
        with open(path,mode='r',) as f:
            lines = f.readlines()
        results = [json.loads(line) for line in lines]
        sorted_results = sorted(results, key=lambda x: x['idx'])
        with open(path, mode='w') as f:
            for result in sorted_results:
                f.write(json.dumps(result) + "\n")
