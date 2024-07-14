from typing import Dict, List

import numpy as np

from bfcl.evaluator import constants


class LeaderboardModelMetrics:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._init_metrics()

    def _init_metrics(self) -> None:
        self._metrics = dict(
            cost=dict(input_tokens=[], output_tokens=[]),
            latency=[],
        )

    def reset(self) -> None:
        self._init_metrics()
    
    def compute(self) -> Dict:
        cost = mean_latency = std_latency = p95_latency = 'N/A'
        if (
            self.model_name in constants.INPUT_PRICE_PER_MILLION_TOKEN
            and len(self._metrics['cost']['input_tokens']) > 0
            and len(self._metrics['cost']['output_tokens']) > 0
        ):
            mean_input_tokens = np.mean(self._metrics['cost']['input_tokens'])
            mean_output_tokens = np.mean(self._metrics['cost']['output_tokens'])
            cost = (
                mean_input_tokens * constants.INPUT_PRICE_PER_MILLION_TOKEN[self.model_name]
                + mean_output_tokens * constants.OUTPUT_PRICE_PER_MILLION_TOKEN[self.model_name]
            ) / 1000

        if self.model_name in constants.OSS_LATENCY:
            mean_latency = round(constants.OSS_LATENCY[self.model_name] / 1700, 2)
            cost = mean_latency * 1000 * constants.V100_x8_PRICE_PER_HOUR / 3600
        elif len(self._metrics['latency']) != 0:
            mean_latency = np.mean(self._metrics['latency'])
            std_latency = np.std(self._metrics['latency'])
            p95_latency = np.percentile(self._metrics['latency'], 95)
            mean_latency = round(mean_latency, 2)
            std_latency = round(std_latency, 2)
            p95_latency = round(p95_latency, 2)

            if self.model_name not in constants.INPUT_PRICE_PER_MILLION_TOKEN:
                cost = sum(self._metrics['latency']) * constants.V100_x8_PRICE_PER_HOUR / 3600
                cost = round(cost, 2)

        if self.model_name in constants.NO_COST_MODELS:
            cost = 'N/A'
        elif isinstance(cost, float):
            cost = round(cost, 2)

        computed_metrics = dict(
            cost=cost, 
            mean_latency=mean_latency, 
            std_latency=std_latency, 
            p95_latency=p95_latency
        )
        return computed_metrics

    def __call__(self, model_responses: List[Dict]) -> None:
        for response in model_responses:
            if (latency := response.get('latency')):
                self._metrics['latency'].append(latency)
                if latency > 60:
                    print("*" * 100)
                    print(f"❗️Warning: Latency for a model '{self.model_name}' response is {latency:.4f}.")
                    print("*" * 100)
            if (input_tokens := response.get('input_tokens')) and input_tokens != 0:
                self._metrics['cost']['input_tokens'].append(input_tokens)
            if (output_tokens := response.get('output_tokens')) and output_tokens != 0:
                self._metrics['cost']['output_tokens'].append(output_tokens)
