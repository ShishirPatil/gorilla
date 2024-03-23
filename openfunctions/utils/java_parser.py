import json
from tree_sitter import Language, Parser

# Load your language and initialize the parser as previously described
from tree_sitter import Language, Parser

Language.build_library(
    # Store the library in the `build` directory
    "build/tree_sitter.so",
    # Include one or more languages
    ["./tree-sitter-java"],
)
JAVA_LANGUAGE = Language("build/tree_sitter.so", "java")
parser = Parser()
parser.set_language(JAVA_LANGUAGE)

def parse_java_function_call(source_code):
    tree = parser.parse(bytes(source_code, "utf8"))
    root_node = tree.root_node
    sexp_result = root_node.sexp()
    
    if "ERROR" in sexp_result:
        return None

    def get_text(node):
        """Returns the text represented by the node."""
        return source_code[node.start_byte:node.end_byte]

    def traverse_node(node, nested=False):
        if node.type == 'string_literal':
            if nested:
                return get_text(node)
            # Strip surrounding quotes from string literals
            return get_text(node)[1:-1]
        elif node.type == 'character_literal':
            if nested:
                return get_text(node)
            # Strip surrounding single quotes from character literals
            return get_text(node)[1:-1]
        """Traverse the node to collect texts for complex structures."""
        if node.type in ['identifier', 'class_literal', 'type_identifier', 'method_invocation']:
            return get_text(node)
        elif node.type == 'array_creation_expression':
            # Handle array creation expression specifically
            type_node = node.child_by_field_name('type')
            value_node = node.child_by_field_name('value')
            type_text = traverse_node(type_node, True)
            value_text = traverse_node(value_node, True)
            return f"new {type_text}[]{value_text}"
        elif node.type == 'object_creation_expression':
            # Handle object creation expression specifically
            type_node = node.child_by_field_name('type')
            arguments_node = node.child_by_field_name('arguments')
            type_text = traverse_node(type_node, True)
            if arguments_node:
                arguments_text = traverse_node(arguments_node, True)
                return f"new {type_text}({arguments_text})"
            else:
                return f"new {type_text}()"
        elif node.type == 'set':
            # Handling sets specifically
            items = [traverse_node(n, True) for n in node.children if n.type not in [',', 'set']]
            return '{' + ', '.join(items) + '}'
        
        elif node.child_count > 0:
            return ''.join(traverse_node(child, True) for child in node.children)
        else:
            return get_text(node)

    def extract_arguments(args_node):
        arguments = {}
        for child in args_node.children:
            if child.type == 'assignment_expression':
                # For named parameters
                name_node, value_node = child.children[0], child.children[2]
                name = get_text(name_node)
                value = traverse_node(value_node)
                if name in arguments:
                    if not isinstance(arguments[name], list):
                        arguments[name] = [arguments[name]]
                    arguments[name].append(value)
                else:
                    arguments[name] = value
                # arguments.append({'name': name, 'value': value})
            elif child.type in ['identifier', 'class_literal', 'set']:
                # For unnamed parameters and handling sets
                value = traverse_node(child)
                if None in arguments:
                    if not isinstance(arguments[None], list):
                        arguments[None] = [arguments[None]]
                    arguments[None].append(value)
                else:
                    arguments[None] = value
        return arguments

    def traverse(node):
        if node.type == 'method_invocation':
            # Extract the function name and its arguments
            function_name = get_text(node.child_by_field_name('name'))
            arguments_node = node.child_by_field_name('arguments')
            if arguments_node:
                arguments = extract_arguments(arguments_node)
                return {'function': {'name': function_name, 'parameters': arguments}}
        else:
            for child in node.children:
                result = traverse(child)
                if result:
                    return result

    result = traverse(root_node)
    return result if result else {}

# Example usage
if __name__ == "__main__":
    # Assuming parser setup and language loading are done earlier
    
    # Valid Java source code
    source_code = """FileSystemsTest.execute(a, b, node=testRootNode, env=testEnv, contextArguments=new Object[]{'local', '/home/user', false, true, true}, frameArguments=new Object[]{}, arraylist=new ArrayList<>(Arrays.asList(\"include_defaults\", true, \"TOXCONTENT_SKIP_RUNTIME\", true)))"""
    
    # expected print output from `print(json.dumps(result, indent=2))`:
    """
        {
            "function": {
                "name": "execute",
                "parameters": {
                "null": [
                    "a",
                    "b"
                ],
                "node": "testRootNode",
                "env": "testEnv",
                "contextArguments": "new Object[]{'local','/home/user',false,true,true}",
                "frameArguments": "new Object[]{}",
                "arraylist": "new ArrayList<>((Arrays.asList(\"include_defaults\", true, \"TOXCONTENT_SKIP_RUNTIME\", true)))"
                }
            }
        }
    """
    
    # An invalid java source code case, our parse_java_function_call will return None
    """SourceSectionFilter.isRootIncluded(providedTags={ExpressionTag.class, StatementTag.class}, rootSection=codeBlockSection, rootNode=rootNodeInstance, rootNodeBits=rootNodeBitMask);"""
    
    # expected print output from `print(json.dumps(result, indent=2))`:
    """
        null
    """
    
    result = parse_java_function_call(source_code)
    print(json.dumps(result, indent=2))

    
   
