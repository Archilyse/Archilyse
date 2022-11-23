import itertools
from typing import Any, Iterable


def chunker(iterable: Iterable[Any], size_of_chunk: int) -> Iterable[Any]:
    """Yield n-length chunks from an iterable.
    It works with iterables, and also it works with exceptions while the
    iterable is consumed
    Args:
        iterable: Iterable to split into chunks.
        size_of_chunk: Length of chunks. The last chunk will be smaller if
            the length of the iterable is not evenly divisible by n.
    Yields:
        chunks as list
    """
    fill_value = None
    args = [iter(iterable)] * size_of_chunk
    for chunk in itertools.zip_longest(*args, fillvalue=fill_value):
        chunk = list(chunk)
        if chunk[-1] is not fill_value:
            yield chunk
        else:
            yield list((item for item in chunk if item is not fill_value))
