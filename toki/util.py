from typing import Any, List

def first(l: List) -> Any:
	return next(iter(l), None)
