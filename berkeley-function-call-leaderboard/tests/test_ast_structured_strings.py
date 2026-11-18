import json
import unittest
from pathlib import Path

import bfcl_eval
from bfcl_eval.constants.enums import Language
from bfcl_eval.eval_checker.ast_eval.ast_checker import ast_checker

DATA = Path(bfcl_eval.__file__).resolve().parent / "data"
MODEL = "gorilla-openfunctions-v2"


def load(file_name: str, entry_id: str, answers: bool = False) -> dict:
    path = DATA / ("possible_answer/" if answers else "") / file_name
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entry = json.loads(line)
            if entry["id"] == entry_id:
                return entry
    raise KeyError(entry_id)


def check(file_name, entry_id, category, language, output):
    entry, answer = load(file_name, entry_id), load(file_name, entry_id, answers=True)["ground_truth"]
    return ast_checker(entry["function"], output, answer, language, category, MODEL)["valid"]


def derivative(function):
    return check("BFCL_v4_multiple.json", "multiple_99", "multiple", Language.PYTHON,
                 [{"calculus.derivative": {"function": function, "value": 1, "function_variable": "x"}}])


def dummy_server(sa, ssl_context="testSSLContext"):
    return check("BFCL_v4_simple_java.json", "simple_java_48", "simple_java", Language.JAVA,
                 [{"CookieHeaderTest.create": {"sa": sa, "sslContext": ssl_context}}])


def full_name(separator):
    return check("BFCL_v4_live_simple.json", "live_simple_125-81-0", "live_simple", Language.PYTHON,
                 [{"concat_strings": {"strings": ["John", "Doe"], "separator": separator}}])


def gluten_free_dinner(**ingredients):
    return check("BFCL_v4_simple_python.json", "simple_python_353", "simple_python", Language.PYTHON,
                 [{"find_recipes": {"diet": "gluten-free", "meal_type": "dinner", **ingredients}}])


def recommendations(url):
    return check("BFCL_v4_live_simple.json", "live_simple_133-86-0", "live_simple", Language.PYTHON,
                 [{"requests.get": {"url": url, "params": {"advisoryId": "dac"}}}])


def fabric_nodes(url):
    return check("BFCL_v4_live_simple.json", "live_simple_128-83-0", "live_simple", Language.PYTHON,
                 [{"requests.get": {"url": url, "fabricName": "PEK-ACI"}}])


def estimate_derivative(function):
    return check("BFCL_v4_live_parallel_multiple.json", "live_parallel_multiple_13-11-0", "live_parallel_multiple",
                 Language.PYTHON, [{"math_gcd": {"a": 48, "b": 36}},
                                   {"estimate_derivative": {"function": function, "x": 5.0}}])


def open_hugging_face(command):
    return check("BFCL_v4_live_simple.json", "live_simple_146-95-3", "live_simple", Language.PYTHON,
                 [{"cmd_controller.execute": {"command": command}}])


def service_config(endpoint):
    return check("BFCL_v4_live_multiple.json", "live_multiple_996-227-0", "live_multiple", Language.PYTHON,
                 [{"add_service_config": {"service_name": "fdsa", "configurations": {
                     "timeout": 30, "retry_count": 5, "endpoint": endpoint, "auth_required": True}}}])


def copy_backup(destination):
    return check("BFCL_v4_simple_java.json", "simple_java_7", "simple_java", Language.JAVA,
                 [{"EFSNIOResource.copy": {"destination": destination, "force": "true", "monitor": "progressTracker"}}])


def end_element(element):
    return check("BFCL_v4_simple_java.json", "simple_java_70", "simple_java", Language.JAVA,
                 [{"XMLNamespaceBinder.endElement": {"element": element, "augs": "augmentations"}}])


def run_command(entry_id, command):
    return check("BFCL_v4_live_simple.json", entry_id, "live_simple", Language.PYTHON,
                 [{"cmd_controller.execute": {"command": command}}])


def command_ok(model_output, accepted):
    return string_ok("command", model_output, [accepted])


FABRIC_NODES = "https://192.168.11.33/sedgeapi/v1/cisco-nir/api/api/telemetry/flowrules/nodes"


class StructuredStringTest(unittest.TestCase):
    def test_different_ip_address_fails(self):
        self.assertFalse(dummy_server('new InetSocketAddress("19.216.81.10", 8080)'))
        self.assertFalse(dummy_server('new InetSocketAddress("192-168-1-10", 8080)'))

    def test_same_ip_address_passes(self):
        self.assertTrue(dummy_server('new InetSocketAddress("192.168.1.10", 8080)'))
        self.assertTrue(dummy_server('new InetSocketAddress("192.168.1.10",8080)'))

    def test_different_identifier_fails(self):
        self.assertFalse(dummy_server('new InetSocketAddress("192.168.1.10", 8080)', "testSSL_Context"))
        self.assertFalse(dummy_server('new InetSocketAddress("192.168.1.10", 8080)', "test_SSL_Context"))
        self.assertFalse(dummy_server('new InetSocketAddress("192.168.1.10", 8080)', "testSSL-Context"))

    def test_separator_made_of_deleted_characters(self):
        self.assertTrue(full_name(" "))
        self.assertFalse(full_name("-"))
        self.assertFalse(full_name(""))

    def test_different_expression_fails(self):
        for function in ("2x-2", "2x/2", "2x*2"):
            self.assertFalse(derivative(function), function)

    def test_same_expression_in_other_notation_passes(self):
        for function in ("2x**2", "2*x**2", "2x^2", "2 * x ** 2", "lambda x: 2x**2", "lambda x : 2*x**2"):
            self.assertTrue(derivative(function), function)

    def test_expression_ignores_case(self):
        for function in ("2X**2", "2X^2"):
            self.assertTrue(derivative(function), function)

    def test_url_trailing_slash_counts(self):
        # Removed tolerance: no real answer needs a trailing slash ignored
        self.assertFalse(recommendations("https://api.example.com/recommendations/"))
        self.assertFalse(fabric_nodes(FABRIC_NODES + "/?fabricName=PEK-ACI"))
        self.assertTrue(fabric_nodes(FABRIC_NODES + "?fabricName=PEK-ACI"))

    def test_url_scheme_and_host_ignore_case(self):
        self.assertTrue(recommendations("HTTPS://API.Example.COM/recommendations"))

    def test_url_path_keeps_case(self):
        self.assertFalse(recommendations("https://api.example.com/Recommendations"))

    def test_empty_list_matches_the_optional_marker(self):
        # The key for `ingredients` is [""]: the parameter may be omitted, and an explicit [] also passes.
        self.assertTrue(gluten_free_dinner())
        self.assertTrue(gluten_free_dinner(ingredients=[]))

    def test_names_keep_the_tolerant_comparison(self):
        self.assertTrue(check("BFCL_v4_simple_python.json", "simple_python_85", "simple_python", Language.PYTHON,
                              [{"geo_distance.calculate": {"start_location": "Boston, MA", "end_location": "Washington, DC",
                                                       "units": "miles"}}]))


def string_ok(param, model_output, possible_answer):
    from bfcl_eval.eval_checker.ast_eval.ast_checker import string_checker

    return string_checker(param, model_output, possible_answer)["valid"]


def original_list_checker(param, model_output, possible_answer):
    """list_checker as it is at 6ea57973c7a6097fd7c5915698c54c17c5b1b6c8, for comparison."""
    from bfcl_eval.eval_checker.ast_eval.ast_checker import standardize_string

    standardize_model_output = list(model_output)
    for i in range(len(standardize_model_output)):
        if type(standardize_model_output[i]) == str:
            standardize_model_output[i] = standardize_string(model_output[i])
    standardize_possible_answer = []
    for i in range(len(possible_answer)):
        standardize_possible_answer.append([])
        for j in range(len(possible_answer[i])):
            if type(possible_answer[i][j]) == str:
                standardize_possible_answer[i].append(standardize_string(possible_answer[i][j]))
            else:
                standardize_possible_answer[i].append(possible_answer[i][j])
    return standardize_model_output in standardize_possible_answer


class ExpressionTokenTest(unittest.TestCase):
    """Expression parameters (not lambdas): token by token, ignoring whitespace and case, with ^ read as ** and implicit
    multiplication made explicit."""

    def assert_different(self, a, b):
        self.assertFalse(string_ok("function", a, [b]), f"{a!r} accepted for {b!r}")
        self.assertFalse(string_ok("function", b, [a]), f"{b!r} accepted for {a!r}")

    def test_function_call_is_not_a_product(self):
        self.assert_different("log10(x)", "log10*(x)")

    def test_scientific_notation_is_one_number(self):
        self.assert_different("1e3*x", "1*e3*x")

    def test_split_power_operator_is_not_a_power(self):
        self.assert_different("2*x**2", "2*x* *2")

    def test_space_between_names_is_kept(self):
        self.assert_different("lambda x: 2*x**2", "lambdax: 2*x**2")

    def test_spacing_between_tokens_is_ignored(self):
        self.assertTrue(string_ok("function", "2 * x ** 2", ["2*x**2"]))
        self.assertTrue(string_ok("function", "2*x**2", ["2 * x ** 2"]))

    def test_multiple_99_rejects_split_power_and_joined_lambda(self):
        self.assertFalse(derivative("2*x* *2"))
        self.assertFalse(derivative("lambdax: 2x**2"))

    def test_constants_and_single_variables_are_compared_by_token(self):
        self.assert_different("2 3", "2*3")
        self.assert_different("-x", "x")
        self.assert_different("--x", "x")
        self.assertTrue(string_ok("function", " x ", ["x"]))

    def test_no_implicit_product_next_to_a_keyword(self):
        self.assert_different("2 if x else 3", "2*if x else 3")
        self.assert_different("(1) if x else 3", "(1)*if x else 3")
        self.assert_different("3 in s", "3*in s")

    def test_expressions_are_not_compared_as_syntax_trees(self):
        # Removed tolerance: no real answer needs an expression compared as a syntax tree
        self.assertFalse(string_ok("function", "(x)**2", ["x**2"]))
        self.assertFalse(string_ok("function", "exp(-x**2,)", ["exp(-x**2)"]))
        self.assertFalse(string_ok("function", "x**2;", ["x**2"]))


class CallableTest(unittest.TestCase):
    """A value holding a lambda, anywhere in it and under any parameter, is compared as Python: by syntax tree when
    both values parse, so formatting is ignored and case counts."""

    def test_lambda_names_are_case_sensitive(self):
        self.assertTrue(estimate_derivative("lambda x: x**2"))
        self.assertFalse(estimate_derivative("lambda x: X**2"))
        self.assertFalse(estimate_derivative("lambda X: X**2"))
        self.assertFalse(derivative("LAMBDA X: 2X**2"))
        self.assertFalse(derivative("lambda X: 2X**2"))

    def test_lambda_is_compared_by_syntax_tree(self):
        self.assertTrue(estimate_derivative("lambda x : x ** 2"))
        self.assertTrue(estimate_derivative("(lambda x: x**2)"))
        self.assertFalse(estimate_derivative("lambda x: x^2"))  # ^ is XOR in Python
        self.assertFalse(string_ok("function", "lambda x: x^2", ["lambda x: x**2"]))

    def test_only_a_side_that_is_not_python_is_recovered(self):
        # The key "lambda x: 2x**2" isn't Python, so it is rewritten (implicit multiplication made explicit). A model
        # value that is Python keeps its own syntax tree: in "lambda x: 2*x^2", ^ is XOR
        self.assertTrue(derivative("lambda x: 2*x**2"))
        self.assertFalse(derivative("lambda x: 2*x^2"))
        self.assertTrue(derivative("lambda x: 2x^2"))  # not Python either, so rewritten too
        self.assertTrue(derivative("lambda x,: 2x**2"))  # the recovered value is compared as a syntax tree

    def test_lambda_is_parsed_as_an_expression_only(self):
        # Removed tolerance: no real answer needs a value parsed as statements
        self.assertFalse(string_ok("function", "y=(lambda x: x**2)", ["y = lambda x: x**2"]))
        self.assertFalse(string_ok("function", "lambda x: x**2;", ["lambda x: x**2"]))

    def test_lambda_anywhere(self):
        from bfcl_eval.eval_checker.ast_eval.ast_checker import dict_checker

        self.assertFalse(string_ok("function", "(lambda x: X**2)", ["(lambda x: x**2)"]))
        self.assertTrue(string_ok("function", "(lambda x: x**2)", ["lambda x: x**2"]))
        self.assertFalse(string_ok("function", "f(lambda y: Y)", ["f(lambda y: y)"]))
        self.assertFalse(string_ok("callback", "lambda x: x*2", ["lambda x: x**2"]))
        self.assertFalse(dict_checker("p", {"function": "(lambda x: X**2)"}, [{"function": ["(lambda x: x**2)"]}])["valid"])
        self.assertTrue(dict_checker("p", {"function": "lambda x:x**2"}, [{"function": ["(lambda x: x**2)"]}])["valid"])

    def test_lambda_inside_a_string_literal_is_not_code(self):
        self.assertTrue(string_ok("description", "Explain the lambda calculus", ["explain the lambda-calculus"]))


class CodeTokenTest(unittest.TestCase):
    """Java and JavaScript code, and a value that holds a URL or an IP address inside it, are compared token by token,
    with operators matched longest first."""

    def test_joined_or_split_tokens_fail(self):
        self.assertFalse(dummy_server('newInetSocketAddress("192.168.1.10", 8080)'))
        self.assertFalse(dummy_server('new InetSocketAddress("192.168.1.10", 80 80)'))

    def test_spacing_around_punctuation_is_ignored(self):
        self.assertTrue(dummy_server('new InetSocketAddress( "192.168.1.10" , 8080 )'))

    def test_java_operators_are_matched_longest_first(self):
        url = "http://www.example.com"
        self.assertFalse(string_ok("element", f'f("{url}", a++ + b)', [f'f("{url}", a + ++b)']))
        self.assertTrue(string_ok("element", f'f("{url}", a+++b)', [f'f("{url}", a++ + b)']))
        self.assertFalse(string_ok("element", f'f("{url}", a->b)', [f'f("{url}", a- >b)']))

    def test_java_code_without_a_url(self):
        # Part 2: Java code without a URL or an IP address had the tolerant comparison
        self.assertTrue(copy_backup("new Path('/backup/data.txt')"))
        self.assertTrue(copy_backup("\tnew Path( '/backup/data.txt' )"))
        self.assertFalse(copy_backup("newPath('/backup/data.txt')"))
        self.assertFalse(copy_backup("new Path('/backup/datatxt')"))
        self.assertFalse(copy_backup("new path('/backup/data.txt')"))

    def test_java_strings_whatever_their_quotes(self):
        # Part 2: the key writes Java strings in single quotes; a model's double-quoted Java string is the same string
        self.assertTrue(end_element('new QName("http://www.example.com", "item", "ex")'))
        self.assertTrue(end_element("new QName('http://www.example.com', 'item', 'ex')"))
        self.assertFalse(end_element('new QName("http://www.example.com", "Item", "ex")'))

    def test_java_char_literal_is_not_a_string(self):
        from bfcl_eval.eval_checker.ast_eval.ast_checker import _same_string

        self.assertFalse(_same_string("c", "f('a')", 'f("a")', Language.JAVA, "any"))
        self.assertTrue(_same_string("c", "f('a')", 'f("a")', Language.JAVASCRIPT, "any"))


class CommandTest(unittest.TestCase):
    """cmd_controller.execute runs Windows cmd.exe commands. A command is compared word by word, split at whitespace
    outside double quotes: double quotes and ^ escapes count, single quotes and backslashes are ordinary characters.
    Case is ignored only in the program name, in /-switches, in arguments that name a Windows file or path, and in a
    URL's scheme and host."""

    def test_quoted_url_keeps_the_case_of_its_path_and_query(self):
        self.assertFalse(command_ok('curl "https://example.com/Case?q=X"', 'curl "https://example.com/case?q=x"'))
        self.assertTrue(command_ok('CURL "HTTPS://EXAMPLE.COM/Case?q=X"', 'curl "https://example.com/Case?q=X"'))

    def test_word_boundaries_count(self):
        self.assertFalse(command_ok("echo a-b", "echo a - b"))
        self.assertTrue(command_ok("echo   a-b ", "echo a-b"))

    def test_cmd_quotes_and_escapes(self):
        # In cmd.exe single quotes are ordinary characters: echo 'hello world' prints the quotes
        self.assertFalse(command_ok("echo 'hello world'", 'echo "hello world"'))
        self.assertTrue(command_ok('echo  "hello world"', 'echo "hello world"'))
        self.assertFalse(command_ok("echo a^&b", "echo a&b"))
        self.assertFalse(command_ok("echo %date%", "echo ^%date^%"))

    def test_backslashes_are_kept(self):
        self.assertTrue(command_ok("DIR C:\\Users", "dir C:\\users"))
        self.assertFalse(command_ok("dir C:Users", "dir C:\\Users"))

    def test_spacing_around_operators_counts(self):
        # Removed tolerance: no real answer needs & | < > to separate words without spaces
        self.assertFalse(command_ok("echo. > C:\\testing.txt", "echo.>C:\\testing.txt"))
        self.assertFalse(command_ok("dir D:\\&&echo testing.txt", "dir D:\\ && echo testing.txt"))
        self.assertTrue(command_ok("dir  D:\\ &&  echo testing.txt", "dir D:\\ && echo testing.txt"))

    def test_program_name_ignores_case_and_arguments_do_not(self):
        self.assertTrue(run_command("live_simple_141-94-0", "docker --version"))
        self.assertTrue(run_command("live_simple_141-94-0", "Docker --version"))
        self.assertFalse(run_command("live_simple_141-94-0", "docker --VERSION"))

    def test_windows_file_names_and_paths_ignore_case(self):
        self.assertTrue(run_command("live_simple_158-95-15", "taskkill /IM Code.exe /F"))
        self.assertTrue(run_command("live_simple_158-95-15", "taskkill /F /IM CODE.EXE"))
        self.assertTrue(command_ok("dir C:\\", "dir c:\\"))
        self.assertTrue(command_ok("D:/Playground/test.py", "d:/playground/test.py"))

    def test_windows_switches_ignore_case(self):
        # Windows commands ignore the case of /-switches; Docker-style --flags stay case-sensitive
        self.assertTrue(run_command("live_simple_158-95-15", "taskkill /IM Code.exe /f"))
        self.assertTrue(run_command("live_simple_158-95-15", "taskkill /im code.exe /F"))
        self.assertFalse(run_command("live_simple_158-95-15", "taskkill /IMX Code.exe /F"))
        self.assertFalse(run_command("live_simple_158-95-15", "taskkill IM Code.exe /F"))
        self.assertFalse(run_command("live_simple_141-94-0", "docker --VERSION"))

    def test_descriptive_command_values_keep_the_tolerant_comparison(self):
        # ControlAppliance.execute's "command" is a comma-separated Korean description, not a shell command
        self.assertTrue(command_ok("거실,에어컨,실행", "거실, 에어컨, 실행"))

    def test_command_with_url(self):
        self.assertTrue(open_hugging_face("start https://huggingface.co"))
        self.assertFalse(open_hugging_face("starthttps://huggingface.co"))
        self.assertFalse(open_hugging_face("start https://hugging face.co"))
        self.assertFalse(string_ok("command", "start https://huggingface.co", ["starthttps://huggingface.co"]))

    def test_url_in_a_command(self):
        self.assertTrue(open_hugging_face("START HTTPS://HuggingFace.co"))
        self.assertFalse(open_hugging_face("start https://huggingface.co/"))  # a trailing slash counts
        self.assertFalse(string_ok("command", "start https://example.com/A", ["start https://example.com/a"]))


class DictValueTest(unittest.TestCase):
    """dict_checker compares string values with the same rules, named by their dict key."""

    def test_url_in_dict(self):
        self.assertTrue(service_config("https://api.fdsa-service.com"))
        self.assertTrue(service_config("HTTPS://API.FDSA-SERVICE.COM"))
        self.assertFalse(service_config("https://api.fdsa-service.com/"))
        self.assertFalse(service_config("https://api.fdsaservice.com"))

    def test_descriptive_dict_values_keep_the_tolerant_comparison(self):
        from bfcl_eval.eval_checker.ast_eval.ast_checker import dict_checker

        self.assertTrue(dict_checker("p", {"city": "washington dc"}, [{"city": ["Washington, D.C."]}])["valid"])
        self.assertTrue(dict_checker("p", {"city": "-"}, [{"city": ["", "Boston"]}])["valid"])
        self.assertFalse(dict_checker("p", {"city": "Boston"}, [{"city": ["Washington, D.C."]}])["valid"])


class ListItemTest(unittest.TestCase):
    """list_checker compares expression and identifier items with the same rules as single values."""

    def test_expression_items(self):
        from bfcl_eval.eval_checker.ast_eval.ast_checker import list_checker

        self.assertFalse(list_checker("function", ["2x-2"], [["2x**2"]])["valid"])
        self.assertTrue(list_checker("function", ["2*x**2"], [["2x**2"]])["valid"])

    def test_java_items_matching_the_identifier_pattern(self):
        # Items of a Java or JavaScript list whose item type isn't String are compared as single values are
        from bfcl_eval.eval_checker.ast_eval.ast_checker import list_checker

        self.assertFalse(list_checker("ids", ["user_ID", 42], [["userID", 42]], Language.JAVA, "any")["valid"])
        self.assertTrue(list_checker("ids", ["userID", 42], [["userID", 42]], Language.JAVA, "any")["valid"])
        self.assertTrue(list_checker("ids", ["user_ID"], [["userID"]], Language.JAVA, "String")["valid"])

    def test_python_items_keep_the_tolerant_comparison(self):
        from bfcl_eval.eval_checker.ast_eval.ast_checker import list_checker

        self.assertTrue(list_checker("names", ["user_ID"], [["userID"]])["valid"])


class EscapedQuoteTest(unittest.TestCase):
    """Whitespace inside a quoted string counts, also after an escaped quote."""

    QNAME = 'new QName("http://www.example.com", "a\\" b")'

    def test_whitespace_after_escaped_quote_counts(self):
        self.assertFalse(string_ok("element", 'new QName("http://www.example.com", "a\\"b")', [self.QNAME]))

    def test_whitespace_outside_quotes_is_still_ignored(self):
        self.assertTrue(string_ok("element", 'new QName("http://www.example.com","a\\" b")', [self.QNAME]))


class WholeValueTest(unittest.TestCase):
    """A value that is a URL, an IPv4 address or an identifier as a whole (fullmatch) is compared as one."""

    def test_url_with_whitespace_fails(self):
        self.assertFalse(recommendations("https://api.example.com/recom mendations"))
        self.assertFalse(recommendations("https://api.example.com/ recommendations"))
        self.assertFalse(recommendations("https://api.example.com/recommendations "))

    def test_ip_address_with_whitespace_fails(self):
        self.assertFalse(string_ok("host", "192.168.1.10 ", ["192.168.1.10"]))
        self.assertFalse(string_ok("host", "192.168. 1.10", ["192.168.1.10"]))
        self.assertTrue(string_ok("host", "192.168.1.10", ["192.168.1.10"]))

    def test_identifier_pattern_matches_the_whole_value(self):
        from bfcl_eval.eval_checker.ast_eval.ast_checker import _structured_kind

        self.assertEqual(_structured_kind("sslContext", "testSSLContext", Language.JAVA, "any"), "exact")
        # "$" in a match() pattern also matches before a final newline; fullmatch() does not.
        self.assertIsNone(_structured_kind("sslContext", "testSSLContext\n", Language.JAVA, "any"))


class ErrorMessageTest(unittest.TestCase):
    """The error message says how the value was compared, instead of "Case insensitive." for every value."""

    def message(self, param, model_output, possible_answer):
        from bfcl_eval.eval_checker.ast_eval.ast_checker import string_checker

        result = string_checker(param, model_output, possible_answer)
        self.assertFalse(result["valid"], f"{model_output!r} accepted for {possible_answer!r}")
        return result["error"][0]

    def test_structured_values(self):
        self.assertNotIn("Case insensitive", self.message("function", "2x-2", ["2x**2"]))
        self.assertIn("Compared token by token", self.message("function", "2x-2", ["2x**2"]))
        self.assertIn("Compared as a Python syntax tree", self.message("function", "lambda x: x", ["lambda x: x**2"]))
        self.assertIn("Compared exactly.", self.message("separator", "-", [" "]))
        self.assertIn("Compared as a URL", self.message("url", "https://example.com/b", ["https://example.com/a"]))

    def test_descriptive_values(self):
        self.assertIn("Compared case-insensitively, ignoring spaces and ,./-_*^.",
                      self.message("city", "Boston", ["Washington, DC"]))


class UrlToleranceTest(unittest.TestCase):
    """Kept: a URL's scheme and host ignore case. The path, query and fragment keep their case, and a trailing slash
    counts."""

    def test_host_case_is_ignored(self):
        self.assertTrue(recommendations("HTTPS://API.EXAMPLE.COM/recommendations"))

    def test_trailing_slash_counts(self):
        self.assertFalse(recommendations("HTTPS://API.EXAMPLE.COM/recommendations/"))
        self.assertFalse(string_ok("url", "https://Example.com/a/?q=X", ["https://example.com/a?q=X"]))
        self.assertFalse(end_element("new QName('http://www.example.com/', 'item', 'ex')"))
        self.assertTrue(end_element("new QName('HTTP://WWW.EXAMPLE.COM', 'item', 'ex')"))

    def test_query_keeps_case(self):
        self.assertFalse(string_ok("url", "https://example.com/a?q=x", ["https://example.com/a?q=X"]))


class CompatibilityTest(unittest.TestCase):
    """Existing three-argument calls remain supported."""

    def test_three_argument_calls(self):
        from bfcl_eval.eval_checker.ast_eval.ast_checker import dict_checker, list_checker, string_checker

        self.assertTrue(string_checker("city", "boston", ["Boston"])["valid"])
        self.assertTrue(list_checker("names", ["a", "b"], [["a", "b"]])["valid"])
        self.assertTrue(dict_checker("p", {"city": "boston"}, [{"city": ["Boston"]}])["valid"])


class OptionalMarkerTest(unittest.TestCase):
    """list_checker reads an accepted "" (the optional marker) as the empty list, exactly as the original code does."""

    def test_same_verdicts_as_the_original_list_checker(self):
        from bfcl_eval.eval_checker.ast_eval.ast_checker import list_checker

        possible_answers = [[""], ["", ["a", "b"]], [["a", "b"], ""], [["Hello World"], ""], [["a", 1], ""]]
        model_outputs = [[], [""], ["a", "b"], ["A", "B"], ("a", "b"), ["hello world"], ["a"], [" "], ["a", 1],
                         ["a", "1"]]
        for possible_answer in possible_answers:
            for model_output in model_outputs:
                with self.subTest(possible_answer=possible_answer, model_output=model_output):
                    self.assertEqual(list_checker("p", model_output, possible_answer)["valid"],
                                     original_list_checker("p", model_output, possible_answer))

    def test_empty_list_matches_the_marker(self):
        from bfcl_eval.eval_checker.ast_eval.ast_checker import list_checker

        self.assertTrue(list_checker("p", [], [""])["valid"])
        self.assertFalse(list_checker("p", [""], [""])["valid"])


if __name__ == "__main__":
    unittest.main()
