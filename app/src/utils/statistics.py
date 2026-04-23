from dataclasses import dataclass


@dataclass
class Statistics:
    def to_dict(self) -> dict:
        """Cast the dataclass to a dictionary whose
        keys are attributes of the dataclass and
        values are values of the attributes."""
        return self.__dict__

    def to_string(self) -> str:
        """Create a string containing values of all attributes."""
        strs = [f"{k}={v}" for k, v in self.__dict__.items()]
        return ", ".join(strs)
