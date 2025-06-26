import os
<<<<<<< HEAD:berkeley-function-call-leaderboard/bfcl/model_handler/api_inference/dm_cito.py
from bfcl.model_handler.model_style import ModelStyle
from openai import OpenAI
from bfcl.model_handler.api_inference.mining import MiningHandler
=======
from bfcl_eval.model_handler.model_style import ModelStyle
from openai import OpenAI
from bfcl_eval.model_handler.api_inference.mining import MiningHandler
>>>>>>> upstream/main:berkeley-function-call-leaderboard/bfcl_eval/model_handler/api_inference/dm_cito.py

class DMCitoHandler(MiningHandler):
    def __init__(self, model_name, temperature) -> None:
        super().__init__(model_name, temperature)
        self.model_style = ModelStyle.OpenAI
        self.client = OpenAI(
            base_url= os.getenv("DMCITO_BASE_URL"),
            api_key=os.getenv("DMCITO_API_KEY"),
        )