import argparse
import json 
from codebleu.parser import DFG_python,DFG_java,DFG_ruby,DFG_go,DFG_php,DFG_javascript,DFG_csharp
from codebleu.parser import (remove_comments_and_docstrings,
                   tree_to_token_index,
                   index_to_code_token,
                   tree_to_variable_index)
from tree_sitter import Language, Parser

dfg_function={
    'python':DFG_python,
    'java':DFG_java,
    'ruby':DFG_ruby,
    'go':DFG_go,
    'php':DFG_php,
    'javascript':DFG_javascript,
    'c_sharp':DFG_csharp,
}

# Get all the subtrees given a root_node
def get_all_sub_trees(root_node):
    node_stack = []
    sub_tree_sexp_list = []
    depth = 1
    text = root_node.text
    node_stack.append([root_node, depth])
    while len(node_stack) != 0:
        cur_node, cur_depth = node_stack.pop()
        if cur_node.child_count > 0:
            sub_tree_sexp_list.append([cur_node.sexp(), cur_depth, cur_node, cur_node.children[0].text])
        else:
            sub_tree_sexp_list.append([cur_node.sexp(), cur_depth, cur_node, None])
        for child_node in cur_node.children:
            if len(child_node.children) != 0:
                depth = cur_depth + 1
                node_stack.append([child_node, depth])
    return sub_tree_sexp_list

# Parse the program into AST trees
def ast_parse(candidate, lang='python'):
    LANGUAGE = Language('codebleu/parser/my-languages.so', lang)
    parser = Parser()
    parser.set_language(LANGUAGE)
    
    candidate_tree = parser.parse(bytes(candidate,'utf8')).root_node
    return candidate_tree

# Get all the arguments in the ast tree
def get_args(node):
    if node.child_count == 0:
        return []
    args_list = []
    for child in node.children[0].children[0].children[1].children:
        if 'model=' in child.text.decode() or 'model =' in child.text.decode():
            args_list.append(child.children[2].text)
        elif child.text.decode() != "(" and child.text.decode() != ")" and child.text.decode() != ",":
            args_list.append(child.text)
    return args_list

# Check if there is an api match 
def ast_check(candidate_subtree_list, base_tree_list):
    for idx, base_tree in enumerate(base_tree_list):
        if base_tree.children[0].children[0].child_count == 0:
            continue
        api_name = base_tree.children[0].children[0].children[0].text
        for candidate_tree in candidate_subtree_list:
            if candidate_tree[3] == api_name:
                break
        # Now we have a sub-tree
        candidate_tree = candidate_tree[2]
        args_list = get_args(base_tree)
        if len(args_list) == 0:
            continue
        ast_match = True
        for arg in args_list:
            if arg.decode().lstrip("'").rstrip("'") not in candidate_tree.text.decode():
                ast_match = False
                break
        if ast_match:
            return idx
    return -1

# Parse the dataset
def parse_dataset(args):
    # Read the api datasest
    api_database = []
    with open(args.api_dataset, 'r') as f:
        for line in f:
            api_database.append(json.loads(line))

    # Read the question answer pair datasest
    qa_pairs = []
    with open(args.apibench, 'r') as f:
        for line in f:
            qa_pairs.append(json.loads(line)["api_data"])
    
    # Read the language model response datasest
    llm_responses = []
    with open(args.llm_responses, 'r') as f:
        for line in f:
            llm_responses.append(json.loads(line))

    # Parse all apis to ast trees
    ast_database = []
    for data in api_database:
        ast_tree = ast_parse(data['api_call'])
        ast_database.append(ast_tree)

    return api_database, qa_pairs, llm_responses, ast_database

def main(args):
    # Read datsets
    api_database, qa_pairs, llm_responses, ast_database = parse_dataset(args)

    # Check correctness
    total_correct = 0
    total_hallucination = 0
    for idx, response in enumerate(llm_responses):
        try:
            output = response['text']
        except:
            print('Error: cannot parse line ', idx)
            continue

        # Index the "api_call" domain
        output = output.split("api_call")
        if len(output) == 1:
            # print('Error: line ', idx, ' is not the right format')
            # continue
            api_call = output[0]
        else:
            # Parse the output
            output = output[1].split("api_provider")[0]
            if ":" not in output:
                start = 0
            else:
                start = output.index(":")
            if ")" not in output:
                end = -2
            else:
                end = output.rindex(")")
            api_call = output[start+2:end+1]


        # Parse the api_call into AST tree
        ast_tree = ast_parse(api_call)
        # Search for a subtree
        ast_subtree_list = get_all_sub_trees(ast_tree)
        # Check which ast tree is matching
        database_index = ast_check(ast_subtree_list, ast_database)
        # We cannot index this ast in our database
        if database_index == -1: 
            total_hallucination += 1
            continue
        # We index our reference api_call
        ref_api_call = api_database[database_index]
        # Check for functionality
        if ref_api_call['domain'] == qa_pairs[response['question_id'] - 1]['domain']:
            total_correct += 1
        else:
            pass

    print('Final Functionality accuracy: ', total_correct / len(llm_responses))
    print('Final hallucination: ', total_hallucination/len(llm_responses))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api_dataset", type=str, default=None, help="path to your api dataset")
    parser.add_argument("--apibench", type=str, default=None, help="path to your apibench dataset including the question and answer pairs")
    parser.add_argument("--llm_responses", type=str, default=None, help="path to the language model responses")
    args = parser.parse_args()
    main(args)