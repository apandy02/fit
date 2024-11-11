#!/usr/bin/env python3

import argparse
from fit.llm.nutritionist import NutritionTracker
from fit.trackers.whoop import Whoop


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Fitness tracking CLI tool")
    parser.add_argument("--model", type=str, default="gpt-4o-2024-08-06", help="The LLM to use")
    parser.add_argument("--password", type=str, help="The password for the Whoop API")
    parser.add_argument("--username", type=str, help="The username for the Whoop API")
    
    return parser.parse_args()


def main():
    """Main entry point for the CLI tool."""
    args = parse_args()

    # Add main logic here
    nutritionist = NutritionTracker(model=args.model)
    whoop = Whoop()
if __name__ == "__main__":
    main()
