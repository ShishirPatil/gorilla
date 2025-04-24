# Specifying Test Categories

When running tests, you can use the optional `--test-category` parameter to define which categories of tests to execute. You can provide multiple categories by separating them with spaces. If no category is specified, all available tests will run by default.

## Available Test Groups

You can specify a broad category (test group) to run multiple related tests at once (you can also use `bfcl test-categories` command to see this list):

- `all`: All test categories.
  - This is the default option if no test category is provided.
- `multi_turn`: All multi-turn test categories.
- `single_turn`: All single-turn test categories.
- `live`: All user-contributed live test categories.
- `non_live`: All not-user-contributed test categories (the opposite of `live`).
- `python`: Tests specific to Python code.
- `non_python`: Tests for code in languages other than Python, such as Java and JavaScript.

## Available Individual Test Categories

If you prefer more granular control, you can specify individual categories:

- `simple`: Simple function calls.
- `parallel`: Multiple function calls in parallel.
- `multiple`: Multiple function calls in sequence.
- `parallel_multiple`: Multiple function calls in parallel and in sequence.
- `java`: Java function calls.
- `javascript`: JavaScript function calls.
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
