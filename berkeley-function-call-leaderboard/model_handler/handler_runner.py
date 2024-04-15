import argparse
from model_handler.handler_map import handler_map

from tqdm import tqdm


def main():
    parser = argparse.ArgumentParser(
        description="Run model inference with model handler to generate result for evaluation.")

    # Add arguments for two lists of strings
    parser.add_argument(
        "--data-path", type=str, help="Input data path for inference"
    )
    parser.add_argument(
        "--model-path", type=str, help="Local model path for inference, e.g. /path_to_model/gorilla-llm/gorilla-openfunctions-v2"
    )
    parser.add_argument(
        "--model-name", type=str, help="Model name registered in handler map, e.g. gorilla-llm/gorilla-openfunctions-v2"
    )
    parser.add_argument(
        "--test-category",
        nargs="+",
        type=str,
        help="A list of test categories to run the evaluation on",
    )
    parser.add_argument(
        "--num-gpus", default=4, type=int, help="Number of total GPUs used for all vLLM instances"
    )

    args = parser.parse_args()

    if args.model_name not in handler_map:
        raise ValueError(
            f"Model name {args.model_name} is not in handler map.")

    model_handler = handler_map[args.model_name](args.model_path)
    result_json, _ = model_handler.inference(
        args.data_path, args.test_category, args.num_gpus)

    for index in tqdm(range(len(result_json))):
        model_handler.write(result_json[index], "result.json", args.model_name)


if __name__ == '__main__':
    main()
