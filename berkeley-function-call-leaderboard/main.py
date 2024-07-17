import subprocess
from multiprocessing import Pool


test_categories = {
    # "executable_simple": "gorilla_openfunctions_v1_test_executable_simple.json",
    # "executable_parallel_function": "gorilla_openfunctions_v1_test_executable_parallel_function.json",
    # "executable_multiple_function": "gorilla_openfunctions_v1_test_executable_multiple_function.json",
    # "executable_parallel_multiple_function": "gorilla_openfunctions_v1_test_executable_parallel_multiple_function.json",
    # "simple": "gorilla_openfunctions_v1_test_simple.json",
    # "relevance": "gorilla_openfunctions_v1_test_relevance.json",
    # "parallel_function": "gorilla_openfunctions_v1_test_parallel_function.json",
    # "multiple_function": "gorilla_openfunctions_v1_test_multiple_function.json",
    # "parallel_multiple_function": "gorilla_openfunctions_v1_test_parallel_multiple_function.json",
    "java": "gorilla_openfunctions_v1_test_java.json",
    # "javascript": "gorilla_openfunctions_v1_test_javascript.json",
    # "rest": "gorilla_openfunctions_v1_test_rest.json",
    # "sql": "gorilla_openfunctions_v1_test_sql.json",
}

MODELNAME = "v10-099-FC"

def run_script(category):
    print(category)
    cmd = f"python openfunctions_evaluation.py --model {MODELNAME} --test-category {category}"
    subprocess.run(cmd, shell=True)


def run_eval():
    cmd = f"""
    cd eval_checker/
    python eval_runner.py --model {MODELNAME}
    """
    subprocess.run(cmd, shell=True)


if __name__ == "__main__":
    with Pool(8) as pool:  # Limit the number of processes to 3 for a single 8xA800 instance
        pool.map(run_script, test_categories.keys())


    run_eval()
