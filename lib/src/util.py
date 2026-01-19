from abc import ABC, abstractmethod
from typing import BinaryIO, Type, TypeVar
from pathlib import Path

T = TypeVar("T", bound="Saveable")


class Saveable(ABC):
    @classmethod
    @abstractmethod
    def load(cls: Type[T], reader: BinaryIO) -> T:
        pass

    @abstractmethod
    def save(self, writer: BinaryIO) -> None:
        pass

    def save_to_file(self, path: Path | str) -> None:
        with open(path, "wb") as f:
            self.save(f)

    @classmethod
    def load_from_file(cls: Type[T], path: Path | str) -> T:
        with open(path, "rb") as f:
            return cls.load(f)
