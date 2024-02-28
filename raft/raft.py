import sys
import argparse

def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--datapath", type=str, default="")
    parser.add_argument("--output", type=str, default="./")
    parser.add_argument("--distractors", type=int, default=3)
    parser.add_argument("--questions", type=int, default=5)
    parser.add_argument("--chunk_size", type=int, default=512)
    parser.add_argument("--is_api", type=bool, default=False)


    args = parser.parse_args()
    return args


if __name__ == "__main__":
    # run code
    args = get_args()
    