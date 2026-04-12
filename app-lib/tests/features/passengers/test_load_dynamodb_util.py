# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Unit tests for LoadDynamoDbUtil."""

from unittest.mock import patch

from app_lib.features.passengers.util.load_dynamodb_util import LoadDynamoDbUtil


class TestLoadDynamoDbUtil:
    """Test data loader utility."""

    @patch(
        "app_lib.features.passengers.util.load_dynamodb_util.TitanicPassengerDataService"
    )
    def test_parse_row_with_valid_values(self, mock_repo):
        """Test parsing row with all valid values."""
        loader = LoadDynamoDbUtil()

        row = {
            "ticket": "12345",
            "name": "Smith, Mr. John",
            "pclass": "1",
            "survived": "1",
            "sex": "male",
            "age": "30",
            "sibsp": "0",
            "parch": "0",
            "fare": "50.0",
            "cabin": "A10",
            "embarked": "S",
            "boat": "1",
            "body": "",
            "home.dest": "New York",
        }

        record = loader._parse_row(row)

        assert record.id == "12345"
        assert record.name == "Smith, Mr. John"
        assert record.age == 30.0
        assert record.fare == 50.0

    @patch(
        "app_lib.features.passengers.util.load_dynamodb_util.TitanicPassengerDataService"
    )
    def test_parse_row_with_question_marks(self, mock_repo):
        """Test parsing row with '?' for missing values."""
        loader = LoadDynamoDbUtil()

        row = {
            "ticket": "12345",
            "name": "Smith, Mr. John",
            "pclass": "3",
            "survived": "0",
            "sex": "male",
            "age": "?",
            "sibsp": "0",
            "parch": "0",
            "fare": "?",
            "cabin": "?",
            "embarked": "?",
            "boat": "?",
            "body": "?",
            "home.dest": "?",
        }

        record = loader._parse_row(row)

        assert record.age is None
        assert record.fare is None
        assert record.cabin is None
        assert record.embarked is None

    @patch(
        "app_lib.features.passengers.util.load_dynamodb_util.TitanicPassengerDataService"
    )
    def test_parse_row_with_empty_strings(self, mock_repo):
        """Test parsing row with empty strings."""
        loader = LoadDynamoDbUtil()

        row = {
            "ticket": "12345",
            "name": "Smith, Mr. John",
            "pclass": "2",
            "survived": "1",
            "sex": "female",
            "age": "",
            "sibsp": "1",
            "parch": "0",
            "fare": "",
            "cabin": "",
            "embarked": "C",
            "boat": "",
            "body": "",
            "home.dest": "",
        }

        record = loader._parse_row(row)

        assert record.age is None
        assert record.fare is None
        assert record.cabin is None
