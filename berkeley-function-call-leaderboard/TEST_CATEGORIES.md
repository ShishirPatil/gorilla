## Specifying Test Categories

When running tests, you can use the optional `--test-category` parameter to define which categories of tests to execute. You can provide multiple categories by separating them with spaces. If no category is specified, all available tests will run by default.

### Available Test Groups

You can specify a broad category (test group) to run multiple related tests at once (you can also use `bfcl test-categories` command to see this list):

- `all`: All test categories.
  - This is the default option if no test category is provided.
- `multi_turn`: All multi-turn test categories.
- `single_turn`: All single-turn test categories.
- `live`: All user-contributed live test categories.
- `non_live`: All not-user-contributed test categories (the opposite of `live`).
- `ast`: Abstract Syntax Tree tests.
- `executable`: Executable code evaluation tests.
- `python`: Tests specific to Python code.
- `non_python`: Tests for code in languages other than Python, such as Java and JavaScript.
- `python_ast`: Python Abstract Syntax Tree tests.

### Available Individual Test Categories

If you prefer more granular control, you can specify individual categories:

- `simple`: Simple function calls.
- `parallel`: Multiple function calls in parallel.
- `multiple`: Multiple function calls in sequence.
- `parallel_multiple`: Multiple function calls in parallel and in sequence.
- `java`: Java function calls.
- `javascript`: JavaScript function calls.
- `exec_simple`: Executable function calls.
- `exec_parallel`: Executable multiple function calls in parallel.
- `exec_multiple`: Executable multiple function calls in parallel.
- `exec_parallel_multiple`: Executable multiple function calls in parallel and in sequence.
- `rest`: REST API function calls.
- `irrelevance`: Function calls with irrelevant function documentation.
- `live_simple`: User-contributed simple function calls.
- `live_multiple`: User-contributed multiple function calls in sequence.
- `live_parallel`: User-contributed multiple function calls in parallel.
- `live_parallel_multiple`: User-contributed multiple function calls in parallel and in sequence.
- `live_irrelevance`: User-contributed function calls with irrelevant function documentation.
- `live_relevance`: User-contributed function calls with relevant function documentation.
- `multi_turn_base`: Base entries for multi-turn function calls.
- `multi_turn_miss_func`: Multi-turn function calls with missing function.
- `multi_turn_miss_param`: Multi-turn function calls with missing parameter.
- `multi_turn_long_context`: Multi-turn function calls with long context.

### Important Notes on REST API Testing

If you intend to run the following categories or groups—`all`, `single_turn`, `non_live`, `executable`, `python`, or `rest`—ensure that you have configured your REST API keys in the `.env` file. These categories test the model’s output against real-world APIs.

If you prefer not to provide REST API keys, select a test category that does not involve executable tests.

### API Sanity Checks

By adding the `--api-sanity-check` (or `-c`) flag, the evaluation process will perform preliminary REST API endpoint checks whenever executable test categories (those whose names contain `exec`) are included. If any endpoints fail to respond as expected, they will be flagged, but the testing will continue regardless.
