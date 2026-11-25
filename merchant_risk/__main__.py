import argparse
import json
from pathlib import Path

import pandas as pd

from .data import read_olist
from .model import score_seller, train_and_evaluate


def main() -> None:
    parser = argparse.ArgumentParser(description="Train or inspect the Olist merchant risk model.")
    commands = parser.add_subparsers(dest="command", required=True)

    train = commands.add_parser("train", help="Train candidates and evaluate the selected model.")
    train.add_argument("--data-dir", type=Path, default=Path("data/olist"))
    train.add_argument("--output-dir", type=Path, default=Path("artifacts"))

    score = commands.add_parser("score", help="Score a seller at a historical month-end.")
    score.add_argument("--data-dir", type=Path, default=Path("data/olist"))
    score.add_argument("--model", type=Path, default=Path("artifacts/model.joblib"))
    score.add_argument("--seller-id", required=True)
    score.add_argument("--as-of", required=True, metavar="YYYY-MM-DD")
    score.add_argument("--group-by", choices=["category", "product_id"], default="category")

    args = parser.parse_args()
    try:
        if args.command == "train":
            report = train_and_evaluate(*read_olist(args.data_dir), args.output_dir)
            summary = {key: report[key] for key in ("selected_model", "splits", "held_out_test")}
            print(json.dumps(summary, indent=2))
        else:
            date = pd.Timestamp(args.as_of).normalize()
            if not date.is_month_end or date.tz is not None:
                raise ValueError("--as-of must be a calendar month-end date in YYYY-MM-DD format.")
            print(json.dumps(score_seller(
                *read_olist(args.data_dir), args.model, args.seller_id, date, args.group_by,
            ), indent=2))
    except (ValueError, FileNotFoundError) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    main()
