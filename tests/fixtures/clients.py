"""Client doubles used by offline retrieval tests."""

from typing import Any, Dict, List, Optional, Tuple


class FakeCMADaaSClient:
    """Record retrieval calls and return a pre-built synthetic result."""

    def __init__(self, result: Any):
        self.result = result
        self.calls: List[Tuple[str, Dict[str, Any]]] = []

    def callAPI_to_array2D(
        self,
        interface_id: str,
        params: Dict[str, Any],
        server_id: Optional[str] = None,
    ) -> Any:
        self.calls.append((interface_id, params.copy()))
        return self.result

    def callAPI_to_gridArray2D(
        self,
        interface_id: str,
        params: Dict[str, Any],
        server_id: Optional[str] = None,
    ) -> Any:
        self.calls.append((interface_id, params.copy()))
        return self.result
