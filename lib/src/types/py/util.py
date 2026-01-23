from abc import ABC
from pathlib import Path
from typing import TypeVar
import cbor2
from pydantic import BaseModel

T = TypeVar("T", bound="BaseModel")


class CBORSerializable(ABC):

    def save(self: T, filename: Path) -> None:
        with open(filename, "wb") as f:
            cbor2.dump(self.model_dump(), f)

    @classmethod
    def load(cls: type[T], filename: Path) -> T:
        with open(filename, "rb") as f:
            data = cbor2.load(f)
        return cls(**data)

