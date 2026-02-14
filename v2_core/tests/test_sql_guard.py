import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.api.services.sql_lab import validate_readonly_sql


def test_validate_readonly_sql_accepts_select():
    assert validate_readonly_sql("select 1") == "select 1"
    assert validate_readonly_sql("  with t as (select 1) select * from t;  ").startswith(
        "with t as"
    )


@pytest.mark.parametrize(
    "query",
    [
        "insert into x values (1)",
        "update x set y = 1",
        "delete from x",
        "drop table x",
        "select 1; select 2",
    ],
)
def test_validate_readonly_sql_rejects_mutations(query: str):
    with pytest.raises(ValueError):
        validate_readonly_sql(query)

