from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Statistics:
    """
    Base statistics container.

    Provides utility methods to serialize dataclass content into
    dictionary or string representations.

    Intended for immutable statistical results or metrics objects.
    """

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the dataclass into a dictionary representation.

        Returns:
            Dictionary mapping field names to their values.
        """
        return asdict(self)

    def to_string(self) -> str:
        """
        Convert the dataclass into a human-readable string.

        Returns:
            String representation in the form: "key=value, key=value".
        """
        data = self.to_dict()
        return ", ".join(f"{k}={v}" for k, v in data.items())
