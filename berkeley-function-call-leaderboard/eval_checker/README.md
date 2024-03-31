# Setup

## To run checker for Java, JavaScript test categories

Tree sitter is used for `/gorilla/berkeley-function-call-leaderboard/model_handler/java_parser.py` and `/gorilla/berkeley-function-call-leaderboard/model_handler/js_parser.py`. Thus, you need to install tree-sitter if you want to run the checker for Java and JavaScript test categories.

The git clones should be under `./gorilla/berkeley-function-call-leaderboard/eval_checker` folder.


```bash
pip3 install tree_sitter
git clone https://github.com/tree-sitter/tree-sitter-java.git
git clone https://github.com/tree-sitter/tree-sitter-javascript.git
```
