"""JSON file repositories for each entity."""
import json
import os
from pathlib import Path
from typing import Optional

from library.models import Book, Reader, BorrowRecord


class BaseRepository:
    """Shared JSON read/write logic."""

    def __init__(self, filepath: str, default_data: list):
        self.filepath = filepath
        self.default_data = default_data
        self._ensure_file()

    def _ensure_file(self):
        """Create file with default data if not exists or corrupted."""
        path = Path(self.filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            self._save_raw(self.default_data)
            return
        try:
            self._load_raw()
        except (json.JSONDecodeError, FileNotFoundError):
            backup = str(path) + ".backup"
            path.rename(backup)
            self._save_raw(self.default_data)

    def _load_raw(self) -> list:
        with open(self.filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_raw(self, data: list):
        tmp_path = self.filepath + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self.filepath)


class BookRepository(BaseRepository):
    def __init__(self, data_dir: str = "library_data"):
        super().__init__(
            filepath=os.path.join(data_dir, "books.json"),
            default_data=[],
        )

    def _load(self) -> list[Book]:
        return [Book.from_dict(d) for d in self._load_raw()]

    def _save(self, books: list[Book]):
        self._save_raw([b.to_dict() for b in books])

    def _next_id(self, books: list[Book]) -> str:
        if not books:
            return "B001"
        nums = []
        for b in books:
            try:
                nums.append(int(b.book_id[1:]))
            except (ValueError, IndexError):
                continue
        max_num = max(nums) if nums else 0
        return f"B{max_num + 1:03d}"

    def add(self, book: Book) -> Book:
        books = self._load()
        book.book_id = self._next_id(books)
        books.append(book)
        self._save(books)
        return book

    def get_by_id(self, book_id: str) -> Optional[Book]:
        books = self._load()
        for b in books:
            if b.book_id == book_id:
                return b
        return None

    def get_all(self) -> list[Book]:
        return self._load()

    def search(self, keyword: str = "", category: str = "") -> list[Book]:
        books = self._load()
        results = books
        if keyword:
            kw = keyword.lower()
            results = [b for b in results if kw in b.title.lower() or kw in b.author.lower()]
        if category:
            results = [b for b in results if b.category == category]
        return results

    def update(self, book: Book) -> bool:
        books = self._load()
        for i, b in enumerate(books):
            if b.book_id == book.book_id:
                books[i] = book
                self._save(books)
                return True
        return False

    def delete(self, book_id: str) -> bool:
        books = self._load()
        for i, b in enumerate(books):
            if b.book_id == book_id:
                books.pop(i)
                self._save(books)
                return True
        return False


class ReaderRepository(BaseRepository):
    def __init__(self, data_dir: str = "library_data"):
        super().__init__(
            filepath=os.path.join(data_dir, "readers.json"),
            default_data=[],
        )

    def _load(self) -> list[Reader]:
        return [Reader.from_dict(d) for d in self._load_raw()]

    def _save(self, readers: list[Reader]):
        self._save_raw([r.to_dict() for r in readers])

    def _next_id(self, readers: list[Reader]) -> str:
        if not readers:
            return "R001"
        nums = []
        for r in readers:
            try:
                nums.append(int(r.reader_id[1:]))
            except (ValueError, IndexError):
                continue
        max_num = max(nums) if nums else 0
        return f"R{max_num + 1:03d}"

    def add(self, reader: Reader) -> Reader:
        readers = self._load()
        reader.reader_id = self._next_id(readers)
        readers.append(reader)
        self._save(readers)
        return reader

    def get_by_id(self, reader_id: str) -> Optional[Reader]:
        readers = self._load()
        for r in readers:
            if r.reader_id == reader_id:
                return r
        return None

    def get_all(self) -> list[Reader]:
        return self._load()

    def search(self, keyword: str = "") -> list[Reader]:
        readers = self._load()
        if not keyword:
            return readers
        kw = keyword.lower()
        return [r for r in readers if kw in r.name.lower() or kw in r.reader_id.lower()]

    def update(self, reader: Reader) -> bool:
        readers = self._load()
        for i, r in enumerate(readers):
            if r.reader_id == reader.reader_id:
                readers[i] = reader
                self._save(readers)
                return True
        return False

    def delete(self, reader_id: str) -> bool:
        readers = self._load()
        for i, r in enumerate(readers):
            if r.reader_id == reader_id:
                readers.pop(i)
                self._save(readers)
                return True
        return False


class BorrowRepository(BaseRepository):
    def __init__(self, data_dir: str = "library_data"):
        super().__init__(
            filepath=os.path.join(data_dir, "borrow_records.json"),
            default_data=[],
        )

    def _load(self) -> list[BorrowRecord]:
        return [BorrowRecord.from_dict(d) for d in self._load_raw()]

    def _save(self, records: list[BorrowRecord]):
        self._save_raw([r.to_dict() for r in records])

    def _next_id(self, records: list[BorrowRecord]) -> str:
        if not records:
            return "BR001"
        nums = []
        for r in records:
            try:
                nums.append(int(r.record_id[2:]))
            except (ValueError, IndexError):
                continue
        max_num = max(nums) if nums else 0
        return f"BR{max_num + 1:03d}"

    def add(self, record: BorrowRecord) -> BorrowRecord:
        records = self._load()
        record.record_id = self._next_id(records)
        records.append(record)
        self._save(records)
        return record

    def get_by_id(self, record_id: str) -> Optional[BorrowRecord]:
        records = self._load()
        for r in records:
            if r.record_id == record_id:
                return r
        return None

    def get_all(self) -> list[BorrowRecord]:
        return self._load()

    def get_by_book(self, book_id: str) -> list[BorrowRecord]:
        return [r for r in self._load() if r.book_id == book_id]

    def get_by_reader(self, reader_id: str) -> list[BorrowRecord]:
        return [r for r in self._load() if r.reader_id == reader_id]

    def get_active_by_reader(self, reader_id: str) -> list[BorrowRecord]:
        return [r for r in self._load() if r.reader_id == reader_id and r.return_date is None]

    def get_active_by_book(self, book_id: str) -> list[BorrowRecord]:
        return [r for r in self._load() if r.book_id == book_id and r.return_date is None]

    def get_overdue(self) -> list[BorrowRecord]:
        """Overdue AND not yet returned (逾期未还)."""
        return [r for r in self._load() if r.status == "overdue" and r.return_date is None]

    def update(self, record: BorrowRecord) -> bool:
        records = self._load()
        for i, r in enumerate(records):
            if r.record_id == record.record_id:
                records[i] = record
                self._save(records)
                return True
        return False
