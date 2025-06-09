import unittest
from bfcl.model_handler.api_inference.nemotron import NemotronHandler

class TestNemotronHandler(unittest.TestCase):
    def setUp(self):
        self.handler = NemotronHandler("nvidia/llama-3.1-nemotron-ultra-253b-v1", 0.0)

    def test_format_system_prompt(self):
        functions = [
            {
                "name": "test_function",
                "description": "A test function",
                "parameters": {
                    "properties": {
                        "param1": {"type": "string", "description": "First parameter"},
                        "param2": {"type": "integer", "description": "Second parameter"}
                    },
                    "required": ["param1"]
                }
            }
        ]
        
        prompt = self.handler._format_system_prompt(functions)
        
        # Check that the prompt contains the required XML tags
        self.assertIn("<TOOLCALL>", prompt)
        self.assertIn("</TOOLCALL>", prompt)
        self.assertIn("<AVAILABLE_TOOLS>", prompt)
        self.assertIn("</AVAILABLE_TOOLS>", prompt)
        
        # Check that the functions are properly formatted
        self.assertIn("test_function", prompt)
        self.assertIn("param1", prompt)
        self.assertIn("param2", prompt)

    def test_decode_ast(self):
        # Test with valid XML response
        response = '<TOOLCALL>[test_function(param1="value1", param2=42)]</TOOLCALL>'
        result = self.handler.decode_ast(response)
        self.assertEqual(len(result), 1)
        self.assertIn("test_function", result[0])
        self.assertEqual(result[0]["test_function"]["param1"], "value1")
        self.assertEqual(result[0]["test_function"]["param2"], 42)

        # Test with invalid XML response
        response = "Invalid response"
        result = self.handler.decode_ast(response)
        self.assertEqual(result, [])

        # Test with empty TOOLCALL tags
        response = "<TOOLCALL></TOOLCALL>"
        result = self.handler.decode_ast(response)
        self.assertEqual(result, [])

    def test_decode_execute(self):
        # Test with valid XML response
        response = '<TOOLCALL>[test_function(param1="value1", param2=42)]</TOOLCALL>'
        result = self.handler.decode_execute(response)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 'test_function(param1="value1", param2=42)')

        # Test with multiple function calls
        response = '<TOOLCALL>[test_function1(param1="value1"), test_function2(param2=42)]</TOOLCALL>'
        result = self.handler.decode_execute(response)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], 'test_function1(param1="value1")')
        self.assertEqual(result[1], 'test_function2(param2=42)')

if __name__ == '__main__':
    unittest.main() 