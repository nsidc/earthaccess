from typing import Any


def valid_dataset_parameters(**kwargs: Any) -> bool:
    return len(kwargs) != 0
