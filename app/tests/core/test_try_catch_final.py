from pydantic import BaseModel

from app.core.try_catch_final import try_catch_final


class test_try_catch_final_schema(BaseModel):
    i: int


def test_try_catch_final():
    x = lambda a: a.i + 10
    ex = lambda: 5
    y = try_catch_final(x, try_args=test_try_catch_final_schema(i=8))
    assert y == 18

    ex = lambda: 5
    y = try_catch_final(raise_exception, ex, finally_func)
    assert y == "fe"


def raise_exception():
    raise Exception()


def on_exception():
    return "ee"


def finally_func(e: dict = {}):
    return "fe"
