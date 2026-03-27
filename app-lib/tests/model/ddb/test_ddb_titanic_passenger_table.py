"""Tests for TitanicPassengerTable model."""

import pytest

from app_lib.model.ddb.ddb_titanic_passenger_table import TitanicPassengerTable


@pytest.fixture
def passenger_data():
    """Sample passenger data."""
    return {
        "ticket": "24160",
        "name": "Allen, Miss. Elisabeth Walton",
        "pclass": 1,
        "survived": 1,
        "sex": "female",
        "age": 29,
        "sibsp": 0,
        "parch": 0,
        "fare": 211.3375,
        "cabin": "B5",
        "embarked": "S",
        "boat": "2",
        "body": None,
        "home_dest": "St Louis, MO",
    }


def test_passenger_model_attributes(passenger_data):
    """Test passenger model has correct attributes."""
    passenger = TitanicPassengerTable(**passenger_data)
    assert passenger.ticket == "24160"
    assert passenger.name == "Allen, Miss. Elisabeth Walton"
    assert passenger.pclass == 1
    assert passenger.survived == 1
    assert passenger.sex == "female"
    assert passenger.age == 29


def test_passenger_model_nullable_fields():
    """Test passenger model handles nullable fields."""
    passenger = TitanicPassengerTable(
        ticket="TEST123",
        name="Test Passenger",
        pclass=3,
        survived=0,
        sex="male",
        sibsp=0,
        parch=0,
        fare=7.25,
    )
    assert passenger.age is None
    assert passenger.cabin is None
    assert passenger.body is None
    assert passenger.analysis is None
