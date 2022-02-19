from typing import Optional, Union

from pydantic import BaseModel


def try_catch_final(
        try_func: (),
        catch_func: () = None,
        final_func: () = None,
        *,
        try_args: Union[Optional[BaseModel], dict] = None,
        catch_args: Union[Optional[BaseModel], dict] = None,
        final_args: Union[Optional[BaseModel], dict] = None
):
    try:
        return try_func(try_args) if try_args else try_func()
    except Exception as e:
        if catch_func:
            catch_func(catch_args) if catch_args else catch_func()
    finally:
        if final_func:
            if 'e' in locals():
                if final_args is None:
                    final_args = {"error": e}
                elif type(final_args) == dict:
                    final_args["error"] = e
            f = final_func(final_args) if final_args else final_func()
            return f
