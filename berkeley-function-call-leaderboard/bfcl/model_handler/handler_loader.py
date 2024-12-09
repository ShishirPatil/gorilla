import json
import importlib.util
import os
from pathlib import Path
from typing import Type, Optional

from bfcl.model_handler.base_handler import BaseHandler
from bfcl.model_handler.handler_map import HANDLER_MAP

class HandlerLoader:
    @staticmethod
    def load_handler_class(module_path: str, class_name: str) -> Optional[Type[BaseHandler]]:
        """Dynamically load handler classes from a specified path"""
        try:
            abs_path = str(Path(module_path).resolve())
            spec = importlib.util.spec_from_file_location("custom_module", abs_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load spec for module: {module_path}")
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            handler_class = getattr(module, class_name, None)
            if handler_class is None:
                raise AttributeError(f"Class {class_name} not found in {module_path}")
            
            # Checking for BaseHandler Inheritance
            if not issubclass(handler_class, BaseHandler):
                raise TypeError(f"Class {class_name} must inherit from BaseHandler")
                
            return handler_class
            
        except Exception as e:
            print(f"Error loading handler class {class_name} from {module_path}: {str(e)}")
            return None

    @staticmethod
    def get_handler_class(model_name: str) -> Optional[Type[BaseHandler]]:
        """Returns the handler class corresponding to the model name"""
        # Check the path to the handler mapping file in an environment variable
        handler_config_path = os.getenv("BFCL_HANDLER_CONFIG")
        
        if handler_config_path and os.path.exists(handler_config_path):
            try:
                with open(handler_config_path) as f:
                    handler_config = json.load(f)
                    
                if model_name in handler_config:
                    config = handler_config[model_name]
                    handler_class = HandlerLoader.load_handler_class(
                        config["module_path"], 
                        config["class_name"]
                    )
                    if handler_class:
                        return handler_class
                        
            except Exception as e:
                print(f"Error loading custom handler config: {str(e)}")
        
        # Lookup in the default handler map
        return HANDLER_MAP.get(model_name)
