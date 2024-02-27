import ast

def process_ast_node(node):
    # Check if the node is a function call
    if isinstance(node, ast.Call):
        # Return a string representation of the function call
        return ast.unparse(node) 
    else:
        # Convert the node to source code and evaluate to get the value
        node_str = ast.unparse(node)
        return eval(node_str)

        
def parse_python_function_call(call_str):
    tree = ast.parse(call_str)
    expr = tree.body[0]

    call_node = expr.value
    function_name = (
        call_node.func.id
        if isinstance(call_node.func, ast.Name)
        else str(call_node.func)
    )

    parameters = {}
    noNameParam = []

    # Process positional arguments
    for arg in call_node.args:
        noNameParam.append(process_ast_node(arg))

    # Process keyword arguments
    for kw in call_node.keywords:
        parameters[kw.arg] = process_ast_node(kw.value)

    if noNameParam:
        parameters["None"] = noNameParam
        
    function_dict = {"name": function_name, "arguments": parameters}
    return function_dict

if __name__ == "__main__":
    call_str = "func(1, [1, 2], 3, a=4, b=5)"
    print(parse_python_function_call(call_str))

    call_str = "func('cde', x=1, b='2', c=[1, 2, {'a': 1, 'b': 2}])"
    print(parse_python_function_call(call_str))

    call_str = "get_current_weather(location='Boston, MA', api_key=123456789, unit='fahrenheit')"
    print(parse_python_function_call(call_str))