import argparse
from src.pipelines.run_full_pipeline import run_full_pipeline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)

    args = parser.parse_args()

    run_full_pipeline(args.input)


if __name__ == "__main__":
    main()