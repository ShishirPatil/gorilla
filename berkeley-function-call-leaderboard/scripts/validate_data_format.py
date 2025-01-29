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
    LIVE_RELEVANCE = "live_relevance"
    LIVE_IRRELEVANCE = "live_irrelevance"
    SIMPLE = "simple"
    MULTIPLE = "multiple"
    PARALLEL = "parallel"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    SQL = "sql"
    REST = "rest"
    EXEC = "exec"
    CHATABLE = "chatable"
    IRRELEVANCE = "irrelevance"

def get_file_type(filepath: str) -> FileType:
    """Determine the file type based on filename."""
    filename = os.path.basename(filepath)
    
    # Special cases for live variants
    if "live_" in filename:
        for file_type in FileType:
            if f"live_{file_type.value}" in filename:
                return file_type
    
    # General case
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

def validate_exec_format(filepath: str) -> Tuple[bool, List[str]]:
    """Validates exec format data files."""
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

def validate_live_multiple_format(filepath: str) -> Tuple[bool, List[str]]:
    """Validates live multiple format data files."""
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

def validate_simple_format(filepath: str) -> Tuple[bool, List[str]]:
    """Validates simple format data files."""
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
                    error_msg = f"Line {line_num}: JSON decode error - {str(e)}"
                    print(f"❌ {error_msg}")
                    errors.append(error_msg)
                except Exception as e:
                    error_msg = f"Line {line_num}: Validation error - {str(e)}"
                    print(f"❌ {error_msg}")
                    errors.append(error_msg)
        return len(errors) == 0, errors
    except Exception as e:
        error_msg = f"File read error - {str(e)}"
        print(f"❌ {error_msg}")
        errors.append(error_msg)
        return False, errors

def validate_sql_format(filepath: str) -> Tuple[bool, List[str]]:
    """Validates SQL format data files."""
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

def main():
    """Main function to run all validation checks."""
    validation_results = {}
    all_success = True
    
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
                
                # Map file types to their validation functions
                validation_functions = {
                    FileType.MULTI_TURN: validate_multi_turn_format,
                    FileType.LIVE_SIMPLE: validate_live_simple_format,
                    FileType.LIVE_MULTIPLE: validate_live_multiple_format,
                    FileType.LIVE_PARALLEL: validate_parallel_format,
                    FileType.LIVE_RELEVANCE: validate_simple_format,  # Using simple format for now
                    FileType.LIVE_IRRELEVANCE: validate_simple_format,  # Using simple format for now
                    FileType.SIMPLE: validate_simple_format,
                    FileType.MULTIPLE: validate_simple_format,  # Using simple format for now
                    FileType.PARALLEL: validate_parallel_format,
                    FileType.JAVASCRIPT: validate_javascript_format,
                    FileType.JAVA: validate_simple_format,  # Using simple format for now
                    FileType.SQL: validate_sql_format,
                    FileType.REST: validate_simple_format,  # Using simple format for now
                    FileType.EXEC: validate_exec_format,
                    FileType.CHATABLE: validate_simple_format,  # Using simple format for now
                    FileType.IRRELEVANCE: validate_simple_format  # Using simple format for now
                }
                
                if file_type in validation_functions:
                    success, errors = validation_functions[file_type](filepath)
                    validation_results[filepath] = {
                        "success": success,
                        "file_type": file_type.value,
                        "errors": errors
                    }
                    
                    if success:
                        print(f"✅ Validation successful")
                    else:
                        print(f"❌ Validation failed with {len(errors)} errors")
                        all_success = False
                else:
                    error_msg = f"Validation not implemented for {file_type.value}"
                    print(f"❌ {error_msg}")
                    validation_results[filepath] = {
                        "success": False,
                        "file_type": file_type.value,
                        "errors": [error_msg]
                    }
                    all_success = False
                    
            except ValueError as e:
                error_msg = str(e)
                print(f"❌ {error_msg}")
                validation_results[filepath] = {
                    "success": False,
                    "file_type": "unknown",
                    "errors": [error_msg]
                }
                all_success = False
    
    # Write results to a JSON file for the workflow to use
    results = {
        "all_success": all_success,
        "results": validation_results
    }
    
    with open("validation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n=== Validation Summary ===")
    print(f"Total files checked: {len(validation_results)}")
    failed_files = [f for f, r in validation_results.items() if not r["success"]]
    if failed_files:
        print(f"\nFailed validations ({len(failed_files)}):")
        for failed_file in failed_files:
            print(f"\n{failed_file}:")
            for error in validation_results[failed_file]["errors"]:
                print(f"  - {error}")
    else:
        print("\n✅ All files passed validation!")
    
    return 0 if all_success else 1

if __name__ == "__main__":
    sys.exit(main()) 