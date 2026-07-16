"""Data models for the library management system."""
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Book:
    book_id: str
    title: str
    author: str
    isbn: str
    category: str
    stock: int
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Book":
        return cls(**d)


@dataclass
class Reader:
    reader_id: str
    name: str
    phone: str
    max_borrow: int = 3
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Reader":
        return cls(**d)


@dataclass
class BorrowRecord:
    record_id: str
    book_id: str
    reader_id: str
    borrow_date: str
    due_date: str
    return_date: Optional[str] = None
    status: str = "borrowed"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BorrowRecord":
        return cls(**d)
