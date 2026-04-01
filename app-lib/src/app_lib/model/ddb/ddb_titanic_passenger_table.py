"""DynamoDB model for Titanic passenger data."""

from pynamodb.attributes import NumberAttribute, UnicodeAttribute
from pynamodb.models import Model

from app_lib.util.pynamodb_util import PynamodbUtil


class TitanicPassengerTable(Model):
    """Titanic passenger DynamoDB table model."""

    class Meta:
        """PynamoDB table configuration for Titanic passenger records."""

        table_name = PynamodbUtil.env_table_name("passengers")

    ticket = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute()
    pclass = NumberAttribute()
    survived = NumberAttribute()
    sex = UnicodeAttribute()
    age = NumberAttribute(null=True)
    sibsp = NumberAttribute()
    parch = NumberAttribute()
    fare = NumberAttribute(null=True)
    cabin = UnicodeAttribute(null=True)
    embarked = UnicodeAttribute(null=True)
    boat = UnicodeAttribute(null=True)
    body = NumberAttribute(null=True)
    home_dest = UnicodeAttribute(null=True)
    analysis = UnicodeAttribute(null=True)  # JSON string, set by background jobs
