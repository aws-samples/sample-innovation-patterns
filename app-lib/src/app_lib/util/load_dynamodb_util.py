"""DynamoDB data loading utility.

This module provides a template for loading CSV data into DynamoDB tables.
It demonstrates the pattern using Titanic passenger data, but is designed
to be modified for your specific use case.

CUSTOMIZATION GUIDE:
--------------------
This class is intentionally NOT highly configurable via parameters.
Flexibility comes from modifying the code directly:

1. Change CSV_PATH to point to your dataset
2. Modify _parse_row() to map your CSV columns to your model
3. Replace TitanicPassengerTable with your PynamoDB model
4. Replace TitanicPassengerDataService with your data service

The simple, readable implementation makes it easy to adapt to any
DynamoDB table and CSV structure.

Example modification for a "products" table:
    CSV_PATH = "datasets/products.csv"

    def _parse_row(self, row: dict) -> ProductTable:
        return ProductTable(
            sku=row["sku"],
            name=row["product_name"],
            price=float(row["price"]),
        )
"""

import csv

from loguru import logger

from app_lib.model.ddb.ddb_titanic_passenger_table import TitanicPassengerTable
from app_lib.service.data.titanic_passenger.titanic_passenger_data_service import (
    TitanicPassengerDataService,
)
from app_lib.util.path_util import PathUtil


class LoadDynamoDbUtil:
    """Utility for loading CSV data into DynamoDB.

    This is a template implementation using Titanic data. Modify the
    CSV_PATH, _parse_row(), and repository to adapt to your use case.

    Usage:
        loader = LoadDynamoDbUtil()
        count = loader.load()
        print(f"Loaded {count} records")
    """

    # Path to CSV file relative to app_lib/assets/
    # MODIFY: Change this to your dataset path
    CSV_PATH = "datasets/titanic/walkthrough_titanic.csv"

    def __init__(self):
        """Initialize with repository service."""
        # MODIFY: Replace with your data service
        self.repository = TitanicPassengerDataService()

    def check_data_loaded(self) -> int:
        """Check if data exists in the table.

        Returns:
            Number of records in the table
        """
        return self.repository.count()

    def load(self) -> int:
        """Load all records from CSV into DynamoDB.

        Returns:
            Number of records loaded
        """
        csv_path = PathUtil.lib_assets(self.CSV_PATH)
        logger.info(f"Loading data from: {csv_path}")

        count = 0
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(
                reader, start=2
            ):  # Start at 2 (header is row 1)
                try:
                    record = self._parse_row(row)
                    self.repository.save(record)
                    count += 1

                    if count % 100 == 0:
                        logger.info(f"Loaded {count} records...")
                except Exception as e:
                    logger.error(
                        f"Row {row_num}: Failed to load record. Ticket: {row.get('ticket', 'N/A')}. Error: {e}"
                    )
                    raise ValueError(f"Row {row_num}: {e}") from e

        logger.info(f"Completed loading {count} records")
        return count

    def _parse_row(self, row: dict) -> TitanicPassengerTable:
        """Parse a CSV row into a DynamoDB model.

        MODIFY: Update this method to map your CSV columns to your model.
        Handle type conversions and null values as needed.

        Args:
            row: Dictionary from csv.DictReader

        Returns:
            PynamoDB model instance ready to save
        """

        # Helper for nullable numeric fields
        def parse_float(val: str) -> float | None:
            return float(val) if val and val != "?" else None

        def parse_int(val: str) -> int | None:
            return int(float(val)) if val and val != "?" else None

        def parse_str(val: str) -> str | None:
            return val if val and val != "?" else None

        return TitanicPassengerTable(
            ticket=row["ticket"],
            name=row["name"],
            pclass=int(row["pclass"]),
            survived=int(row["survived"]),
            sex=row["sex"],
            age=parse_float(row["age"]),
            sibsp=int(row["sibsp"]),
            parch=int(row["parch"]),
            fare=parse_float(row["fare"]),
            cabin=parse_str(row["cabin"]),
            embarked=parse_str(row["embarked"]),
            boat=parse_str(row["boat"]),
            body=parse_int(row["body"]),
            home_dest=parse_str(row["home.dest"]),
        )


if __name__ == "__main__":
    """
    Command-line execution for loading data.

    Usage:
        cd app-lib
        AWS_DEFAULT_REGION=us-east-1 python -m app_lib.util.load_dynamodb_util

    Or with profile:
        AWS_PROFILE=myprofile AWS_DEFAULT_REGION=us-east-1 python -m app_lib.util.load_dynamodb_util
    """
    import sys

    loader = LoadDynamoDbUtil()
    count = loader.load()
    print(f"Successfully loaded {count} records")
    sys.exit(0)
