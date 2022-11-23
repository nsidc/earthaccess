from typing import Any


def valid_dataset_parameters(**kwargs: Any) -> bool:
    if len(kwargs) == 0:
        return False
    return True
