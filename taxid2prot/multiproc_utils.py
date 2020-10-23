"""Helper functions for multiprocessing."""
from typing import List, Any
import multiprocessing


def get_cpu_count() -> int:
    """Return cpu count."""

    return multiprocessing.cpu_count()


def get_batches(data: List[Any], processes_count: int) -> List[List[Any]]:
    """Split List[Any] to List[List[Any]] for using in multiprocessing."""

    result = []
    bath_size = round(len(data) / processes_count)
    for i in range(0, len(data), bath_size):
        result.append(data[i : i + bath_size])
    return result
