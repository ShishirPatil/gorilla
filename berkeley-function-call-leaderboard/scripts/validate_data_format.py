import json
import sys
import os
from jsonschema import validate
from glob import glob
from typing import List, Dict, Any, Tuple
from enum import Enum

class FileType(Enum):
    MULTI_TURN = "multi_turn"
    LIVE_SIMPLE = "live_simple"
    LIVE_MULTIPLE = "live_multiple"
    LIVE_PARALLEL = "live_parallel"
    SIMPLE = "simple"
    PARALLEL = "parallel"
    JAVASCRIPT = "javascript"
    EXEC = "exec"

def get_file_type(filepath: str) -> FileType:
    """Determine the file type based on filename."""
    filename = os.path.basename(filepath)
    for file_type in FileType:
        if file_type.value in filename:
            return file_type
    raise ValueError(f"Unknown file type for file: {filepath}")

def validate_base_schema(data: Dict) -> None:
    """Validate the base schema that's common across all file types."""
    base_schema = {
        "type": "object",
        "required": ["id"],
        "properties": {
            "id": {"type": "string"}
        }
    }
    validate(instance=data, schema=base_schema)

def validate_multi_turn_format(filepath: str) -> Tuple[bool, List[str]]:
    """Validates multi-turn conversation data files."""
    errors = []
    schema = {
        "type": "object",
        "required": ["id", "question", "initial_config", "path", "involved_classes"],
        "properties": {
            "id": {"type": "string"},
            "question": {
                "type": "array",
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["role", "content"],
                        "properties": {
                            "role": {"type": "string"},
                            "content": {"type": "string"}
                        }
                    }
                }
            },
            "initial_config": {"type": "object"},
            "path": {
                "type": "array",
                "items": {"type": "string"}
            },
            "involved_classes": {
                "type": "array",
                "items": {"type": "string"}
            }
        }
    }
    return validate_file_against_schema(filepath, schema, errors)

def validate_live_simple_format(filepath: str) -> Tuple[bool, List[str]]:
    """Validates live simple format data files."""
    errors = []
    schema = {
        "type": "object",
        "required": ["id", "question", "function"],
        "properties": {
            "id": {"type": "string"},
            "question": {
                "type": "array",
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["role", "content"],
                        "properties": {
                            "role": {"type": "string"},
                            "content": {"type": "string"}
                        }
                    }
                }
            },
            "function": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "description", "parameters"],
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "parameters": {"type": "object"}
                    }
                }
            }
        }
    }
    return validate_file_against_schema(filepath, schema, errors)

def validate_parallel_format(filepath: str) -> Tuple[bool, List[str]]:
    """Validates parallel format data files."""
    errors = []
    schema = {
        "type": "object",
        "required": ["id", "question", "function"],
        "properties": {
            "id": {"type": "string"},
            "question": {
                "type": "array",
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["role", "content"],
                        "properties": {
                            "role": {"type": "string"},
                            "content": {"type": "string"}
                        }
                    }
                }
            },
            "function": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "description", "parameters"],
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "parameters": {"type": "object"}
                    }
                }
            }
        }
    }
    return validate_file_against_schema(filepath, schema, errors)

def validate_javascript_format(filepath: str) -> Tuple[bool, List[str]]:
    """Validates JavaScript format data files."""
    errors = []
    schema = {
        "type": "object",
        "required": ["id", "question", "function"],
        "properties": {
            "id": {"type": "string"},
            "question": {
                "type": "array",
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["role", "content"],
                        "properties": {
                            "role": {"type": "string"},
                            "content": {"type": "string"}
                        }
                    }
                }
            },
            "function": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "description", "parameters"],
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "parameters": {"type": "object"}
                    }
                }
            }
        }
    }
    return validate_file_against_schema(filepath, schema, errors)

def validate_file_against_schema(filepath: str, schema: Dict, errors: List[str]) -> Tuple[bool, List[str]]:
    """Helper function to validate a file against a given schema."""
    try:
        with open(filepath, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    validate(instance=data, schema=schema)
                except json.JSONDecodeError as e:
                    errors.append(f"Line {line_num}: JSON decode error - {str(e)}")
                except Exception as e:
                    errors.append(f"Line {line_num}: Validation error - {str(e)}")
        return len(errors) == 0, errors
    except Exception as e:
        errors.append(f"File read error - {str(e)}")
        return False, errors

def main():
    """Main function to run all validation checks."""
    validation_results = {}
    all_success = True
    
    # Define patterns for all file types
    patterns = [
        "berkeley-function-call-leaderboard/data/BFCL_v3_*.json"
    ]
    
    for pattern in patterns:
        files = glob(pattern)
        if not files:
            print(f"Warning: No files found matching pattern '{pattern}'")
            continue
        
        for filepath in files:
            try:
                file_type = get_file_type(filepath)
                print(f"\nValidating {file_type.value} file: {filepath}")
                
                if file_type == FileType.MULTI_TURN:
                    success, errors = validate_multi_turn_format(filepath)
                elif file_type == FileType.LIVE_SIMPLE:
                    success, errors = validate_live_simple_format(filepath)
                elif file_type == FileType.LIVE_PARALLEL:
                    success, errors = validate_parallel_format(filepath)
                elif file_type == FileType.PARALLEL:
                    success, errors = validate_parallel_format(filepath)
                elif file_type == FileType.JAVASCRIPT:
                    success, errors = validate_javascript_format(filepath)
                else:
                    print(f"Warning: Validation for {file_type.value} not yet implemented")
                    continue
                
                validation_results[filepath] = {
                    "success": success,
                    "file_type": file_type.value,
                    "errors": errors
                }
                
                if not success:
                    all_success = False
                    
            except ValueError as e:
                validation_results[filepath] = {
                    "success": False,
                    "file_type": "unknown",
                    "errors": [str(e)]
                }
                all_success = False
    
    # Write results to a JSON file for the workflow to use
    with open("validation_results.json", "w") as f:
        json.dump({
            "all_success": all_success,
            "results": validation_results
        }, f, indent=2)
    
    return 0 if all_success else 1

if __name__ == "__main__":
    sys.exit(main()) 