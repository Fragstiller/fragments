from __future__ import annotations
from enum import Enum
from dataclasses import dataclass
from typing import TypeVar, Generic, Type, Optional

T = TypeVar("T")


@dataclass
class ParamCell(Generic[T]):
    bounds: tuple[int, int] | list[Enum]
    value: T

    def __eq__(self, other):
        raise TypeError("comparing against ParamCell is forbidden")

    def __ne__(self, other):
        raise TypeError("comparing against ParamCell is forbidden")


class ParamStorage:
    cells: list[ParamCell[int | Enum]]
    global_storage: ParamStorage
    global_storage_active: bool = False

    def __init__(self):
        self.cells = list()

    @classmethod
    def new_global(cls):
        cls.global_storage = ParamStorage()
        cls.global_storage_active = True

    def get_cell_bounds(self) -> list[tuple[int, int] | list[Enum]]:
        return [cell.bounds for cell in self.cells]

    def apply_cell_values(self, values: list[int | Enum]):
        if len(values) != len(self.cells):
            raise RuntimeError(
                f"length of list of values is {len(values)}, should be {len(self.cells)}"
            )
        for cell, value in zip(self.cells, values):
            cell.value = value

    def create_cell(
        self, bounds: tuple[int, int] | list[Enum], value: Optional[int | Enum] = None
    ) -> ParamCell:
        if value is None:
            self.cells.append(ParamCell(bounds, bounds[0]))
        else:
            self.cells.append(ParamCell(bounds, value))
        return self.cells[-1]

    def create_default_numerical_cell(self) -> ParamCell:
        self.cells.append(ParamCell((0, 1), 0))
        return self.cells[-1]

    def create_default_categorical_cell(self, enum: Type[Enum]) -> ParamCell:
        self.cells.append(
            ParamCell((j := [i for i in enum.__members__.values()]), j[0])
        )
        return self.cells[-1]
