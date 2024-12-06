import json
import os
from typing import Dict, Any

from bfcl.model_handler.handler_map import local_inference_handler_map
from bfcl.eval_checker.model_metadata import (
    MODEL_METADATA_MAPPING,
    OUTPUT_PRICE_PER_MILLION_TOKEN,
    NO_COST_MODELS,
)

class MetadataLoader:
    @staticmethod
    def load_metadata() -> tuple[Dict[str, Any], Dict[str, float], list[str]]:
        """
        Load model metadata, pricing information, and list of no-cost models.
        
        Returns:
            tuple containing:
            - metadata: Dict mapping model names to their metadata
            - prices: Dict mapping model names to their prices
            - no_cost_models: List of model names that have no associated cost
        """
        metadata = dict(MODEL_METADATA_MAPPING)
        prices = dict(OUTPUT_PRICE_PER_MILLION_TOKEN)
        no_cost = list(NO_COST_MODELS)

        # Check for additional metadata config file path in environment variables
        metadata_config_path = os.getenv("BFCL_MODEL_METADATA")
        
        if metadata_config_path and os.path.exists(metadata_config_path):
            try:
                with open(metadata_config_path) as f:
                    custom_config = json.load(f)
                
                # Add custom model metadata
                if "metadata" in custom_config:
                    metadata.update(custom_config["metadata"])
                
                # Add custom pricing information
                if "prices" in custom_config:
                    prices.update(custom_config["prices"])
                
                # Add additional no-cost models
                if "no_cost_models" in custom_config:
                    no_cost.extend(custom_config["no_cost_models"])
                    
            except Exception as e:
                print(f"Error loading custom metadata config: {str(e)}")
        
        return metadata, prices, no_cost

# Global metadata loader instance
metadata_loader = MetadataLoader() 