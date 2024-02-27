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

    def traverse_node(node):
        """Traverse the node to collect texts for complex structures."""
        if node.type in ['identifier', 'class_literal', 'type_identifier', 'method_invocation']:
            return get_text(node)
        elif node.type == 'set':
            # Handling sets specifically
            items = [traverse_node(n) for n in node.children if n.type not in [',', 'set']]
            return '{' + ', '.join(items) + '}'
        elif node.child_count > 0:
            return ''.join(traverse_node(child) for child in node.children)
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
    
    # An invalid java source code case, our parse_java_function_call will return None
    # """SourceSectionFilter.isRootIncluded(providedTags={ExpressionTag.class, StatementTag.class}, rootSection=codeBlockSection, rootNode=rootNodeInstance, rootNodeBits=rootNodeBitMask);"""
    
    source_code = """FileSystemsTest.execute(a, b, node=testRootNode, node=testRootNode2, env=testEnv, contextArguments=new Object[]{'local', '/home/user', false, true, true}, frameArguments=new Object[]{})"""
    # expected: {"function": {"name": "execute", "parameters": {"null": ["a", "b"], "node": ["testRootNode", "testRootNode2"], "env": "testEnv", "contextArguments": "newObject[]{'local','/home/user',false,true,true}", "frameArguments": "newObject[]{}"}}}
    
    result = parse_java_function_call(source_code)
    print(json.dumps(result, indent=2))
