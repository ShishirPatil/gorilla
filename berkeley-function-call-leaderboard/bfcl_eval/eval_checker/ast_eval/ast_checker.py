import ast
import keyword
import re
import warnings

from bfcl_eval.constants.enums import Language
from bfcl_eval.constants.model_config import MODEL_CONFIG_MAPPING
from bfcl_eval.constants.type_mappings import JAVA_TYPE_CONVERSION, JS_TYPE_CONVERSION
from bfcl_eval.eval_checker.ast_eval.type_convertor.java_type_converter import (
    java_type_converter,
)
from bfcl_eval.eval_checker.ast_eval.type_convertor.js_type_converter import (
    js_type_converter,
)

#### Constants ####
PYTHON_TYPE_MAPPING = {
    "string": str,
    "integer": int,
    "float": float,
    "boolean": bool,
    "array": list,
    "tuple": list,
    "dict": dict,
    "any": str,
}

# This is the list of types that we need to recursively check its values
PYTHON_NESTED_TYPE_CHECK_LIST = ["array", "tuple"]


NESTED_CONVERSION_TYPE_LIST = ["Array", "ArrayList", "array"]


#### Main function ####
def ast_checker(
    func_description,
    model_output,
    possible_answer,
    language: Language,
    test_category: str,
    model_name: str,
):
    if "parallel" in test_category:
        return parallel_function_checker_no_order(
            func_description, model_output, possible_answer, language, model_name
        )

    elif "multiple" in test_category:
        return multiple_function_checker(
            func_description, model_output, possible_answer, language, model_name
        )

    else:
        if len(model_output) != 1:
            return {
                "valid": False,
                "error": ["Wrong number of functions."],
                "error_type": "simple_function_checker:wrong_count",
            }

        return simple_function_checker(
            func_description[0], model_output[0], possible_answer[0], language, model_name
        )


#### Helper functions for AST ####
def find_description(func_descriptions, name):
    if type(func_descriptions) == list:
        for func_description in func_descriptions:
            if func_description["name"] == name:
                return func_description
        return None
    else:
        # it is a dict, there is only one function
        return func_descriptions


def get_possible_answer_type(possible_answer: list):
    for answer in possible_answer:
        if answer != "":  # Optional parameter
            return type(answer)
    return None


def convert_func_name(function_name, model_name: str):
    model_name_escaped = model_name.replace("_", "/")
    if "." in function_name:
        if MODEL_CONFIG_MAPPING[model_name_escaped].underscore_to_dot:
            # OAI does not support "." in the function name so we replace it with "_". ^[a-zA-Z0-9_-]{1,64}$ is the regex for the name.
            # This happens for OpenAI, Mistral, and Google models
            return re.sub(r"\.", "_", function_name)
    return function_name


def type_checker(
    param: str,
    value,
    possible_answer: list,
    expected_type_description: str,
    expected_type_converted,
    nested_type_converted,
):
    # NOTE: This type checker only supports nested type checking for one level deep.
    # We didn't implement recursive type checking for nested types, as it's not needed for the current use case and it's very complex.

    result = {
        "valid": True,
        "error": [],
        "is_variable": False,
        "error_type": "type_error:simple",
    }

    is_variable = False
    # check for the case where a variable is used instead of a actual value.
    # use the type in possible_answer as the expected type
    possible_answer_type = get_possible_answer_type(possible_answer)
    # if possible_answer only contains optional parameters, we can't determine the type
    if possible_answer_type != None:
        # we are being precise here.
        # in fact, possible_answer_type should always be string, as that's how we treat varibale in possible_answer
        if possible_answer_type != expected_type_converted:
            is_variable = True

    # value is the same type as in function description
    if type(value) == expected_type_converted:
        # We don't need to do recursive check for simple types
        if nested_type_converted == None:
            result["is_variable"] = is_variable
            return result
        else:
            for possible_answer_item in possible_answer:
                flag = True  # Each parameter should match to at least one possible answer type.
                # Here, we assume that each item should be the same type. We could also relax it.
                if type(possible_answer_item) == list:
                    for value_item in value:
                        checker_result = type_checker(
                            param,
                            value_item,
                            possible_answer_item,
                            str(nested_type_converted),
                            nested_type_converted,
                            None,
                        )
                        if not checker_result["valid"]:
                            flag = False
                            break

                if flag:
                    return {"valid": True, "error": [], "is_variable": is_variable}

            result["valid"] = False
            result["error"] = [
                f"Nested type checking failed for parameter {repr(param)}. Expected outer type {expected_type_description} with inner type {str(nested_type_converted)}. Parameter value: {repr(value)}."
            ]
            result["error_type"] = "type_error:nested"

    # value is not as expected, check for the case where a variable is used instead of a actual value
    # use the type in possible_answer as the expected type
    possible_answer_type = get_possible_answer_type(possible_answer)
    # if possible_answer only contains optional parameters, we can't determine the type
    if possible_answer_type != None:
        # we are being precise here.
        # in fact, possible_answer_type should always be string, as that's how we treat varibale in possible_answer
        if type(value) == possible_answer_type:
            result["is_variable"] = True
            return result

    result["valid"] = False
    result["error"].append(
        f"Incorrect type for parameter {repr(param)}. Expected type {expected_type_description}, got {type(value).__name__}. Parameter value: {repr(value)}."
    )
    result["error_type"] = "type_error:simple"
    return result


def standardize_string(input_string: str):
    """
    This function standardizes the string by removing all the spaces, ",./-_*^" punctuation, and converting it to lowercase
    It will also convert all the single quotes to double quotes
    This is used to compare the model output with the possible answers
    We don't want to punish model for answer like April 1, 2024 vs April 1,2024, vs April 1 2024
    """
    regex_string = r"[ \,\.\/\-\_\*\^]"
    return re.sub(regex_string, "", input_string).lower().replace("'", '"')


# standardize_string deletes spaces and ",./-_*^" and lowercases. This tolerance accommodates formatting variants in
# descriptive values such as names, places and titles ("Washington, D.C." and "Washington DC"). In some values those
# characters carry the meaning, and deleting them makes different values compare equal: "19.216.81.10" and
# "192.168.1.10", "2x-2" and "2x**2", or the separator "-" and the separator " ". The values below are compared
# without deleting them.
_IPV4 = r"(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}"
_BARE_IPV4 = re.compile(_IPV4)  # with fullmatch: the whole value is an address
_IPV4_IN_TEXT = re.compile(r"(?<![\d.])" + _IPV4 + r"(?![\d.])")  # an address inside a longer value
# With fullmatch, the whole value is a URL: scheme, authority, path, then query and fragment. No whitespace.
_BARE_URL = re.compile(r"([A-Za-z][A-Za-z0-9+.\-]*)://([^/?#\s]*)([^?#\s]*)([?#]\S*)?")
# A URL inside a quoted string: scheme, authority, path. It ends at whitespace or a quote.
_URL_IN_TEXT = re.compile(r"([A-Za-z][A-Za-z0-9+.\-]*)://([^/?#\s'\"]*)([^?#\s'\"]*)")
_IDENTIFIER = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*")  # with fullmatch
_EXPRESSION_PARAMS = {"function", "func", "function1", "function2", "equation", "expression", "formula", "polynomial"}
_COMMAND_PARAMS = {"command"}
# A shell command starts with an ASCII program name or path. That tells the cmd.exe commands of cmd_controller.execute
# apart from descriptive values of other parameters named "command", such as "거실, 에어컨, 실행".
_SHELL_PROGRAM = re.compile(r"\s*[\x21-\x7e]*[A-Za-z0-9][\x21-\x7e]*(?:\s|$)")
_KEYWORDS_LOWER = {word.lower() for word in keyword.kwlist}
_STRING = r"""'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*\""""  # a backslash escapes the next character
_NUMBER = r"(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?"
_EXPRESSION_TOKEN = re.compile(
    rf"""(?P<space>\s+)
      | (?P<string>{_STRING})
      | (?P<number>{_NUMBER})
      | (?P<name>[^\W\d]\w*)
      | (?P<op>\*\*|//|==|!=|<=|>=|<<|>>|->|\S)""",
    re.VERBOSE,
)
# Java and JavaScript operators, matched longest first, so that "a++ + b" and "a + ++b" give different tokens
_CODE_OPERATORS = sorted(
    [">>>=", "<<=", ">>=", ">>>", "===", "!==", "**=", "...", "->", "::", "=>", "++", "--", "+=", "-=", "*=", "/=",
     "%=", "&=", "|=", "^=", "==", "!=", "<=", ">=", "&&", "||", "<<", ">>", "**", "?.", "??"],
    key=len, reverse=True,
)
_CODE_TOKEN = re.compile(
    rf"""(?P<space>\s+)
      | (?P<url>[A-Za-z][A-Za-z0-9+.\-]*://[^\s'"]*)
      | (?P<string>{_STRING}|`(?:[^`\\]|\\.)*`)
      | (?P<ip>(?<![\d.]){_IPV4}(?![\d.]))
      | (?P<number>{_NUMBER})
      | (?P<name>(?:[^\W\d]|\$)[\w$]*)
      | (?P<op>{"|".join(re.escape(op) for op in _CODE_OPERATORS)}|\S)""",
    re.VERBOSE,
)
# Java or JavaScript code, not a literal or an identifier: a call, constructor, array, lambda or method reference
_JAVA_CODE = re.compile(r"[(\[{]|::|->|=>|^\s*new\s")
# A cmd.exe argument that names a Windows file or path, whose case Windows ignores: it has a backslash, a drive
# letter or a file extension, as in C:\\Users, d:/scripts/test.py or Code.exe
_WINDOWS_PATH = re.compile(r'\\|(?:^|")[A-Za-z]:|\w\.[A-Za-z][A-Za-z0-9]*"?$')
# A Windows-style switch, / followed by letters, as in /IM or /f: Windows commands ignore its case
_WINDOWS_SWITCH = re.compile(r"/[A-Za-z]+")
# A URL inside a cmd.exe word: scheme, authority, path, then query and fragment. It ends at whitespace or a double quote.
_URL_IN_WORD = re.compile(r"([A-Za-z][A-Za-z0-9+.\-]*)://([^/?#\s\"]*)([^?#\s\"]*)([?#][^\s\"]*)?")
# How each kind of accepted value is compared, for the error message. None is the tolerant comparison.
_COMPARISONS = {
    None: "case-insensitively, ignoring spaces and ,./-_*^",
    "exact": "exactly",
    "url": "as a URL, ignoring the case of its scheme and host",
    "code": "token by token, with operators matched longest first and a quoted string read the same whatever its "
            "quotes (but a Java char literal is not a string), ignoring whitespace between tokens and the case of a "
            "URL's scheme and host",
    "command": "word by word, split at whitespace outside double quotes, with quotes and ^ escapes counting; case is "
               "ignored only in the program name, in /-switches, in arguments that name a Windows file or path, and "
               "in a URL's scheme and host",
    "expression": "token by token, ignoring whitespace and case, with ^ read as ** and implicit multiplication made "
                  "explicit",
    "callable": "as a Python syntax tree, so formatting is ignored and case counts; a value that isn't valid Python "
                "is first rewritten with ^ read as ** and implicit multiplication made explicit",
}


def _url_parts_form(scheme: str, authority: str, path: str) -> str:
    """A URL with its scheme and host lowercased."""
    userinfo, at, host = authority.rpartition("@")
    return scheme.lower() + "://" + userinfo + at + host.lower() + path


def _url_form(text: str) -> str:
    """A value that is a URL as a whole, with its scheme and host lowercased, so that "HTTPS://Example.com/a" equals
    "https://example.com/a". The path, query and fragment keep their case, and a trailing slash counts. Any other
    value, such as a URL with whitespace in it, is returned unchanged."""
    match = _BARE_URL.fullmatch(text)
    if not match:
        return text
    scheme, authority, path, rest = match.groups()
    return _url_parts_form(scheme, authority, path) + (rest or "")


def _literal_form(token: str, language=None) -> str:
    """A quoted literal, read the same whatever its quotes: 'a' and "a" are both the string a, as in Python and
    JavaScript and as the answer keys write Java strings ('item' isn't a Java literal). In Java, a single-quoted single
    character or escape is a char literal, which is not a string. A template literal (backquotes) keeps its quotes."""
    quote, body = token[0], token[1:-1]
    if quote == "`":
        return token
    unescaped = body.replace("\\'", "'").replace('\\"', '"')
    if quote == "'" and language == Language.JAVA and re.fullmatch(r"\\u[0-9a-fA-F]{4}|\\?.", body, re.S):
        return "char:" + unescaped
    return "string:" + _URL_IN_TEXT.sub(lambda m: _url_parts_form(*m.groups()), unescaped)


def _code_tokens(text: str, language=None) -> list:
    """A value such as Java code as a list of tokens: URLs (as in _url_form), quoted literals (as in _literal_form,
    with a URL inside one as in _url_parts_form), IPv4 addresses, numbers, names, and operators matched longest first,
    with whitespace dropped. Spacing between tokens is ignored, so '("a", 1)' equals '( "a" , 1 )', but "new Foo" and
    "newFoo", "80 80" and "8080", and "a++ + b" and "a + ++b" differ."""
    tokens = []
    for match in _CODE_TOKEN.finditer(text):
        kind, token = match.lastgroup, match.group()
        if kind == "space":
            continue
        if kind == "url":
            token = _url_form(token)
        elif kind == "string":
            token = _literal_form(token, language)
        tokens.append(token)
    return tokens


def _command_words(text: str) -> list:
    """A cmd.exe command line split into words at whitespace outside double quotes. A double-quoted part runs to the
    next double quote (or the end) and keeps its quotes. ^ outside double quotes escapes the next character and is
    kept. Single quotes and backslashes are ordinary characters, so "C:\\Users" keeps its backslash. A word keeps its
    quotes and escapes, so 'a b' and "a b", a^&b and a&b, a-b and a - b, and echo.>x and echo. > x differ."""
    words, word, i, in_quote = [], "", 0, False
    while i < len(text):
        ch = text[i]
        if in_quote:
            word += ch
            in_quote = ch != '"'
        elif ch == '"':
            word += ch
            in_quote = True
        elif ch == "^" and i + 1 < len(text):
            word += text[i : i + 2]
            i += 2
            continue
        elif ch.isspace():
            if word:
                words.append(word)
            word = ""
        else:
            word += ch
        i += 1
    if word:
        words.append(word)
    return words


def _command_word_form(word: str) -> str:
    """A cmd.exe argument. Each URL in it (inside or outside quotes) has its scheme and host lowercased and keeps the
    case of its path, query and fragment. A Windows-style switch (_WINDOWS_SWITCH, such as /F) and an argument without
    a URL that names a Windows file or path (_WINDOWS_PATH) are lowercased; any other argument, such as --version, is
    case-sensitive."""
    if _WINDOWS_SWITCH.fullmatch(word):
        return word.lower()
    if not _URL_IN_WORD.search(word):
        return word.lower() if _WINDOWS_PATH.search(word) else word
    out, position = [], 0
    for match in _URL_IN_WORD.finditer(word):
        scheme, authority, path, rest = match.groups()
        out.append(word[position : match.start()])
        out.append(_url_parts_form(scheme, authority, path) + (rest or ""))
        position = match.end()
    out.append(word[position:])
    return "".join(out)


def _command_form(text: str) -> list:
    """A command's words: the program name (the first word) ignoring case, the arguments as in _command_word_form."""
    words = [_command_word_form(word) for word in _command_words(text)]
    return [words[0].lower()] + words[1:] if words else words


def _expression_tokens(text: str, case_sensitive: bool = False) -> list:
    """A math expression as a list of tokens: whitespace dropped, numbers (and, unless case_sensitive, names)
    lowercased, ^ read as **, and implicit multiplication made explicit (a number followed by a name or "(", or ")"
    followed by a name, a number or "("), except before a Python keyword. "2*x**2" and "2 * x ** 2" give the same
    tokens, as do "3x + 2" and "3*x+2", and "x^3" and "x**3". "log10(x)" and "log10*(x)", "1e3*x" and "1*e3*x",
    "2*x**2" and "2*x* *2", "lambda x:" and "lambdax:", "2 3" and "2*3", and "2 if x else 3" and "2*if x else 3" do
    not."""
    tokens = []
    for match in _EXPRESSION_TOKEN.finditer(text):
        kind, token = match.lastgroup, match.group()
        if kind == "space":
            continue
        if kind == "number" or (kind == "name" and not case_sensitive):
            token = token.lower()
        elif token == "^":
            token = "**"
        is_keyword = kind == "name" and (keyword.iskeyword(token) if case_sensitive else token in _KEYWORDS_LOWER)
        if tokens and not is_keyword:
            previous_kind, previous = tokens[-1]
            if (previous_kind == "number" and (kind == "name" or token == "(")) or (
                previous == ")" and (kind in ("name", "number") or token == "(")
            ):
                tokens.append(("op", "*"))
        tokens.append((kind, token))
    return [token for _, token in tokens]


def _has_lambda(text: str) -> bool:
    """Whether the text holds a Python lambda outside string literals, anywhere in it: the name lambda followed later
    by ":", as in "lambda x: x**2", "(lambda x: x**2)" or "f(lambda x: g(lambda y: y))"."""
    tokens = [(m.lastgroup, m.group()) for m in _EXPRESSION_TOKEN.finditer(text) if m.lastgroup not in ("space", "string")]
    return any(
        kind == "name" and token == "lambda" and ("op", ":") in tokens[i + 1 :] for i, (kind, token) in enumerate(tokens)
    )


def _python_syntax(text: str):
    """The text's syntax tree as a string (ast.dump), parsed as an expression, or None if it isn't a valid Python
    expression. Nothing is run."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return ast.dump(ast.parse(text.strip(), mode="eval"))
    except Exception:  # not Python, such as "lambda x: 2x**2", or too large or deep to parse
        return None


def _callable_form(text: str):
    """A value holding a lambda, as its syntax tree if it is a valid Python expression, unchanged: "(lambda x: x**2)"
    and "lambda x : x ** 2" are the same, but not "lambda x: x^2" (^ is XOR) or "lambda x: X**2". Only a value that
    isn't Python, such as the key "lambda x: 2x**2", is rewritten with the tokens of _expression_tokens (^ read as **,
    implicit multiplication made explicit, case counting) and then parsed; if it still doesn't parse, its tokens."""
    syntax = _python_syntax(text)
    if syntax is not None:
        return ("syntax", syntax)
    tokens = _expression_tokens(text, case_sensitive=True)
    syntax = _python_syntax(" ".join(tokens))
    return ("syntax", syntax) if syntax is not None else ("tokens", tokens)


def _same_callable(model_output: str, accepted: str) -> bool:
    return _callable_form(model_output) == _callable_form(accepted)


def _structured_kind(param: str, accepted: str, language=None, declared_type=None):
    """How an accepted string value is compared (a key of _COMPARISONS); None is the tolerant comparison."""
    if _has_lambda(accepted):
        return "callable"  # a value holding a lambda, under any parameter: see _same_callable
    if param in _EXPRESSION_PARAMS:
        return "expression"  # every other value of an expression parameter: see _expression_tokens
    if param in _COMMAND_PARAMS and _SHELL_PROGRAM.match(accepted):
        return "command"  # a cmd.exe command: see _command_words
    if accepted and not standardize_string(accepted):
        return "exact"  # made only of characters standardize_string deletes, e.g. the separator " "
    if _BARE_URL.fullmatch(accepted):
        return "url"  # the whole value is a URL: see _url_form
    if _BARE_IPV4.fullmatch(accepted):
        return "exact"  # the whole value is an IPv4 address
    if _URL_IN_TEXT.search(accepted) or _IPV4_IN_TEXT.search(accepted):
        return "code"  # a URL or an IP address inside a longer value, such as Java code: see _code_tokens
    java = language in (Language.JAVA, Language.JAVASCRIPT) and (declared_type or "").lower() != "string"
    if java and _JAVA_CODE.search(accepted):
        return "code"  # Java or JavaScript code, such as a constructor call: see _code_tokens
    if java and _IDENTIFIER.fullmatch(accepted):
        return "exact"  # a Java or JavaScript identifier is case- and underscore-sensitive
    return None


def _same_string(param: str, model_output: str, accepted: str, language=None, declared_type=None) -> bool:
    kind = _structured_kind(param, accepted, language, declared_type)
    if kind == "exact":
        return model_output == accepted
    if kind == "url":
        return _url_form(model_output) == _url_form(accepted)
    if kind == "code":
        return _code_tokens(model_output, language) == _code_tokens(accepted, language)
    if kind == "command":
        return _command_form(model_output) == _command_form(accepted)
    if kind == "callable" or (kind == "expression" and _has_lambda(model_output)):
        return _same_callable(model_output, accepted)
    if kind == "expression":
        return _expression_tokens(model_output) == _expression_tokens(accepted)
    return standardize_string(model_output) == standardize_string(accepted)


def _same_item(param: str, model_item, accepted_item, language=None, declared_type=None) -> bool:
    """A list item or a dict value: strings with _same_string, anything else for equality."""
    if type(model_item) == str and type(accepted_item) == str:
        return _same_string(param, model_item, accepted_item, language, declared_type)
    return model_item == accepted_item


def _comparison_note(param: str, possible_answer: list, language=None, declared_type=None) -> str:
    """How the accepted strings were compared, for the error message. The optional marker "" is left out."""
    notes = []
    for accepted in possible_answer:
        if type(accepted) == str and accepted != "":
            note = _COMPARISONS[_structured_kind(param, accepted, language, declared_type)]
            if note not in notes:
                notes.append(note)
    return (" Compared " + "; or ".join(notes) + ".") if notes else ""


def string_checker(param: str, model_output: str, possible_answer: list, language=None, declared_type=None):
    if not any(
        type(accepted) == str and _same_string(param, model_output, accepted, language, declared_type)
        for accepted in possible_answer
    ):
        return {
            "valid": False,
            "error": [
                f"Invalid value for parameter {repr(param)}: {repr(model_output)}. Expected one of {possible_answer}."
                + _comparison_note(param, possible_answer, language, declared_type)
            ],
            "error_type": "value_error:string",
        }

    return {"valid": True, "error": []}


def list_checker(param: str, model_output: list, possible_answer: list, language=None, item_type=None):
    # Convert the tuple to a list

    model_list = list(model_output)

    # Read each possible answer item by item, as before, so that a possible answer "" (the optional marker) reads as
    # the empty list
    possible_lists = []
    for i in range(len(possible_answer)):
        possible_lists.append([possible_answer[i][j] for j in range(len(possible_answer[i]))])

    # Compare item by item: string items with _same_string, other items for equality
    if not any(
        len(accepted) == len(model_list)
        and all(_same_item(param, m, a, language, item_type) for m, a in zip(model_list, accepted))
        for accepted in possible_lists
    ):
        return {
            "valid": False,
            "error": [
                f"Invalid value for parameter {repr(param)}: {repr(model_output)}. Expected one of {possible_answer}."
            ],
            "error_type": "value_error:list/tuple",
        }

    return {"valid": True, "error": []}


def dict_checker(param: str, model_output: dict, possible_answers: list):
    # This function works for simple dictionaries, but not dictionaries with nested dictionaries.
    # The current dataset only contains simple dictionaries, so this is sufficient.

    result = {"valid": False, "error": [], "error_type": "dict_checker:unclear"}
    for i in range(len(possible_answers)):

        if possible_answers[i] == "":
            continue

        result = {"valid": False, "error": [], "error_type": "dict_checker:unclear"}

        flag = True

        possible_answer = possible_answers[i]
        # possible_anwer is a single dictionary

        for key, value in model_output.items():
            if key not in possible_answer:
                result["valid"] = False
                result["error"].append(f"Unexpected dict key parameter: '{key}'.")
                result["error_type"] = "value_error:dict_key"
                flag = False
                break

            # String values are compared with _same_string, under the dict key's name; other values for equality
            if not any(_same_item(key, value, accepted) for accepted in possible_answer[key]):
                result["valid"] = False
                result["error"].append(
                    f"Invalid value for parameter {repr(key)}: {repr(value)}. Expected one of {possible_answer[key]}."
                    + _comparison_note(key, possible_answer[key])
                )
                result["error_type"] = "value_error:dict_value"
                flag = False
                break

        for key, value in possible_answer.items():
            if key not in model_output and "" not in value:
                result["valid"] = False
                result["error"].append(f"Missing dict key parameter: '{key}'.")
                result["error_type"] = "value_error:dict_key"
                flag = False
                break

        if flag:
            return {"valid": True, "error": []}

    return result


def list_dict_checker(param: str, model_output: list, possible_answers: list):
    # This function takes in a list of dictionaries and checks if each dictionary is valid
    # The order of the dictionaries in the list must match the order of the possible answers

    result = {"valid": False, "error": [], "error_type": "list_dict_checker:unclear"}

    for answer_index in range(len(possible_answers)):
        flag = True  # True means so far, all dictionaries are valid

        # Only proceed if the number of dictionaries in the list matches the number of dictionaries in the possible answers
        if len(model_output) != len(possible_answers[answer_index]):
            result["valid"] = False
            result["error"] = ["Wrong number of dictionaries in the list."]
            result["error_type"] = "value_error:list_dict_count"
            flag = False
            continue

        for dict_index in range(len(model_output)):
            result = dict_checker(
                param,
                model_output[dict_index],
                [possible_answers[answer_index][dict_index]],
            )
            if not result["valid"]:
                flag = False
                break
        if flag:
            return {"valid": True, "error": []}

    return result


def simple_function_checker(
    func_description: dict,
    model_output: dict,
    possible_answer: dict,
    language: Language,
    model_name: str,
):
    possible_answer = list(possible_answer.values())[0]
    # Extract function name and parameters details
    func_name = func_description["name"]
    param_details = func_description["parameters"]["properties"]
    required_params = func_description["parameters"]["required"]

    # Initialize a result dictionary
    result = {
        "valid": True,
        "error": [],
        "error_type": "simple_function_checker:unclear",
    }

    func_name = convert_func_name(func_name, model_name)

    # Check if function name matches
    if func_name not in model_output:
        result["valid"] = False
        result["error"].append(
            f"Function name {repr(func_name)} not found in model output."
        )
        result["error_type"] = "simple_function_checker:wrong_func_name"
        return result

    model_params = model_output[func_name]

    # Check for required parameters in model output
    for param in required_params:
        if param not in model_params:
            result["valid"] = False
            result["error"].append(f"Missing required parameter: {repr(param)}.")
            result["error_type"] = "simple_function_checker:missing_required"
            return result

    # Validate types and values for each parameter in model output
    for param, value in model_params.items():
        if param not in param_details or param not in possible_answer:
            result["valid"] = False
            result["error"].append(f"Unexpected parameter: {repr(param)}.")
            result["error_type"] = "simple_function_checker:unexpected_param"
            return result

        full_param_details = param_details[param]
        expected_type_description = full_param_details["type"]  # This is a string
        is_variable = False
        nested_type_converted = None

        if language == Language.JAVA:
            expected_type_converted = JAVA_TYPE_CONVERSION[expected_type_description]

            if expected_type_description in JAVA_TYPE_CONVERSION:
                if type(value) != str:
                    result["valid"] = False
                    result["error"].append(
                        f"Incorrect type for parameter {repr(param)}. Expected type String, got {type(value).__name__}. Parameter value: {repr(value)}."
                    )
                    result["error_type"] = "type_error:java"
                    return result

                if expected_type_description in NESTED_CONVERSION_TYPE_LIST:
                    nested_type = param_details[param]["items"]["type"]
                    nested_type_converted = JAVA_TYPE_CONVERSION[nested_type]
                    value = java_type_converter(
                        value, expected_type_description, nested_type
                    )
                else:
                    value = java_type_converter(value, expected_type_description)

        elif language == Language.JAVASCRIPT:
            expected_type_converted = JS_TYPE_CONVERSION[expected_type_description]

            if expected_type_description in JS_TYPE_CONVERSION:
                if type(value) != str:
                    result["valid"] = False
                    result["error"].append(
                        f"Incorrect type for parameter {repr(param)}. Expected type String, got {type(value).__name__}. Parameter value: {repr(value)}."
                    )
                    result["error_type"] = "type_error:js"
                    return result

                if expected_type_description in NESTED_CONVERSION_TYPE_LIST:
                    nested_type = param_details[param]["items"]["type"]
                    nested_type_converted = JS_TYPE_CONVERSION[nested_type]
                    value = js_type_converter(value, expected_type_description, nested_type)
                else:
                    value = js_type_converter(value, expected_type_description)

        elif language == Language.PYTHON:
            expected_type_converted = PYTHON_TYPE_MAPPING[expected_type_description]
            if expected_type_description in PYTHON_NESTED_TYPE_CHECK_LIST:
                nested_type = param_details[param]["items"]["type"]
                nested_type_converted = PYTHON_TYPE_MAPPING[nested_type]

        else:
            raise ValueError(f"Unsupported language: {language}")

        # We convert all tuple value to list when the expected type is tuple.
        # The conversion is necessary because any tuple in the possible answer would become a list after being processed through json.dump() and json.load().
        # This does introduce some false positive (eg, when the model provides a list value instead of tuple). We hope to find a better solution in the future.
        if expected_type_description == "tuple" and type(value) == tuple:
            value = list(value)

        # Allow python auto conversion from int to float
        if (
            language == Language.PYTHON
            and expected_type_description == "float"
            and type(value) == int
        ):
            value = float(value)

        # Type checking
        # In fact, we only check for Python here.
        # Type check for other languages are handled by the type converter, and so their value (after conversion) is always correct.
        type_check_result = type_checker(
            param,
            value,
            possible_answer[param],
            expected_type_description,
            expected_type_converted,
            nested_type_converted,
        )
        is_variable = type_check_result["is_variable"]
        if not type_check_result["valid"]:
            return type_check_result

        # It doesn't make sense to special handle dictionaries and list of dictionaries if the value is a variable.
        # We can just treat the variable as a string and use the normal flow.
        if not is_variable:
            # Special handle for dictionaries
            if expected_type_converted == dict:
                result = dict_checker(param, value, possible_answer[param])
                if not result["valid"]:
                    return result
                continue

            # Special handle for list of dictionaries
            elif expected_type_converted == list and nested_type_converted == dict:
                result = list_dict_checker(param, value, possible_answer[param])
                if not result["valid"]:
                    return result
                continue

            # Special handle for strings
            elif expected_type_converted == str:
                # Descriptive strings ignore case and formatting; structured ones don't (see _structured_kind)
                result = string_checker(
                    param, value, possible_answer[param], language, expected_type_description
                )
                if not result["valid"]:
                    return result
                continue

            elif expected_type_converted == list:
                result = list_checker(
                    param, value, possible_answer[param], language, full_param_details.get("items", {}).get("type")
                )
                if not result["valid"]:
                    return result
                continue

        # Check if the value is within the possible answers
        if value not in possible_answer[param]:
            result["valid"] = False
            result["error"].append(
                f"Invalid value for parameter {repr(param)}: {repr(value)}. Expected one of {possible_answer[param]}."
            )
            result["error_type"] = "value_error:others"
            return result

    # Check for optional parameters not provided but allowed
    for param in possible_answer:
        if param not in model_params and "" not in possible_answer[param]:
            result["valid"] = False
            result["error"].append(
                f"Optional parameter {repr(param)} not provided and not marked as optional."
            )
            result["error_type"] = "simple_function_checker:missing_optional"
            return result

    return result


def parallel_function_checker_enforce_order(
    func_descriptions: list,
    model_output: list,
    possible_answers: dict,
    language: Language,
    model_name: str,
):
    if len(model_output) != len(possible_answers):
        return {
            "valid": False,
            "error": ["Wrong number of functions."],
            "error_type": "parallel_function_checker_enforce_order:wrong_count",
        }

    func_name_list = list(possible_answers.keys())
    possible_answers_list = []

    for key, value in possible_answers.items():
        possible_answers_list.append({key: value})

    for i in range(len(possible_answers_list)):
        func_description = find_description(func_descriptions, func_name_list[i])

        result = simple_function_checker(
            func_description,
            model_output[i],
            possible_answers_list[i],
            language,
            model_name,
        )
        if not result["valid"]:
            return result

    return {"valid": True, "error": []}


def parallel_function_checker_no_order(
    func_descriptions: list,
    model_output: list,
    possible_answers: list,
    language: Language,
    model_name: str,
):
    if len(model_output) != len(possible_answers):
        return {
            "valid": False,
            "error": ["Wrong number of functions."],
            "error_type": "parallel_function_checker_no_order:wrong_count",
        }

    matched_indices = []

    # We go throught the possible answers one by one, and eliminate the model output that matches the possible answer
    # It must be this way because we need ground truth to fetch the correct function description
    for i in range(len(possible_answers)):
        # possible_answers[i] is a dictionary with only one key
        func_name_expected = list(possible_answers[i].keys())[0]
        func_description = find_description(func_descriptions, func_name_expected)

        all_errors = []

        for index in range(len(model_output)):
            if index in matched_indices:
                continue

            result = simple_function_checker(
                func_description,
                model_output[index],
                possible_answers[i],
                language,
                model_name,
            )

            if result["valid"]:
                matched_indices.append(index)
                break
            else:
                all_errors.append(
                    {
                        f"Model Result Index {index}": {
                            "sub_error": result["error"],
                            "sub_error_type": result["error_type"],
                            "model_output_item": model_output[index],
                            "possible_answer_item": possible_answers[i],
                        }
                    }
                )

        if not result["valid"]:
            considered_indices = [
                i for i in range(len(model_output)) if i not in matched_indices
            ]
            all_errors.insert(
                0,
                f"Could not find a matching function among index {considered_indices} of model output for index {i} of possible answers.",
            )
            return {
                "valid": False,
                "error": all_errors,
                "error_type": "parallel_function_checker_no_order:cannot_find_match",
            }

    return {"valid": True, "error": []}


def multiple_function_checker(
    func_descriptions: list,
    model_output: list,
    possible_answers: list,
    language: Language,
    model_name: str,
):
    if len(model_output) != len(possible_answers):
        return {
            "valid": False,
            "error": ["Wrong number of functions."],
            "error_type": "multiple_function_checker:wrong_count",
        }

    # possible_answers is a list of only one dictionary with only one key
    func_name_expected = list(possible_answers[0].keys())[0]
    func_description = find_description(func_descriptions, func_name_expected)
    return simple_function_checker(
        func_description,
        model_output[0],
        possible_answers[0],
        language,
        model_name,
    )
