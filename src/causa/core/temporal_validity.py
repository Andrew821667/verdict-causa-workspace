from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ValidityWindow:
    valid_from: date | None = None
    valid_to: date | None = None

    def includes(self, moment: date) -> bool:
        if self.valid_from and moment < self.valid_from:
            return False
        if self.valid_to and moment > self.valid_to:
            return False
        return True
