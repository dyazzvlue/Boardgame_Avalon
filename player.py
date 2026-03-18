from __future__ import annotations
from dataclasses import dataclass
from constants import Role, Alignment, ROLE_ALIGNMENT

@dataclass
class AvalonPlayer:
    name:      str
    idx:       int
    is_human:  bool = True
    role:      object = None
    alignment: object = None

    def assign_role(self, role: Role) -> None:
        self.role = role
        self.alignment = ROLE_ALIGNMENT[role]

    @property
    def is_good(self) -> bool:
        return self.alignment == Alignment.GOOD

    @property
    def is_evil(self) -> bool:
        return self.alignment == Alignment.EVIL
