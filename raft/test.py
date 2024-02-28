import sys
import argparse

# Check if at least one argument is provided
if len(sys.argv) > 1:
    # Iterate over all arguments except the script name
    for i, arg in enumerate(sys.argv[1:], start=1):
        print(f"Argument {i}: {arg}")
else:
    print("No arguments provided.")
