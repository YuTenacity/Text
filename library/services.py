"""Business logic services."""
from datetime import date, timedelta, datetime
from typing import Optional

from library.models import Book, Reader, BorrowRecord
from library.repositories import BookRepository, ReaderRepository, BorrowRepository


class BookService:
    def __init__(self, repo: BookRepository):
        self.repo = repo

    def add_book(self, title: str, author: str, isbn: str, category: str, stock: int) -> Book:
        if not title.strip():
            raise ValueError("书名不能为空")
        if stock < 0:
            raise ValueError("库存不能为负数")
        today = date.today().isoformat()
        book = Book(book_id="", title=title.strip(), author=author.strip(),
                    isbn=isbn.strip(), category=category.strip(), stock=stock, created_at=today)
        return self.repo.add(book)

    def get_book(self, book_id: str) -> Optional[Book]:
        return self.repo.get_by_id(book_id)

    def list_books(self) -> list[Book]:
        return self.repo.get_all()

    def search_books(self, keyword: str = "", category: str = "") -> list[Book]:
        return self.repo.search(keyword=keyword, category=category)

    def update_book(self, book_id: str, **kwargs) -> Book:
        book = self.repo.get_by_id(book_id)
        if not book:
            raise ValueError(f"图书 {book_id} 不存在")
        for key, value in kwargs.items():
            if hasattr(book, key) and value != "":
                setattr(book, key, value)
        self.repo.update(book)
        return book

    def delete_book(self, book_id: str, borrow_repo: BorrowRepository) -> None:
        active = borrow_repo.get_active_by_book(book_id)
        if active:
            raise ValueError(f"该书有 {len(active)} 条未还记录，无法删除")
        self.repo.delete(book_id)


class ReaderService:
    def __init__(self, repo: ReaderRepository):
        self.repo = repo

    def add_reader(self, name: str, phone: str, max_borrow: int = 3) -> Reader:
        if not name.strip():
            raise ValueError("读者姓名不能为空")
        today = date.today().isoformat()
        reader = Reader(reader_id="", name=name.strip(), phone=phone.strip(),
                        max_borrow=max_borrow, created_at=today)
        return self.repo.add(reader)

    def get_reader(self, reader_id: str) -> Optional[Reader]:
        return self.repo.get_by_id(reader_id)

    def list_readers(self) -> list[Reader]:
        return self.repo.get_all()

    def search_readers(self, keyword: str = "") -> list[Reader]:
        return self.repo.search(keyword=keyword)

    def update_reader(self, reader_id: str, **kwargs) -> Reader:
        reader = self.repo.get_by_id(reader_id)
        if not reader:
            raise ValueError(f"读者 {reader_id} 不存在")
        for key, value in kwargs.items():
            if hasattr(reader, key) and value != "":
                if key == "max_borrow":
                    value = int(value)
                setattr(reader, key, value)
        self.repo.update(reader)
        return reader

    def delete_reader(self, reader_id: str, borrow_repo: BorrowRepository) -> None:
        active = borrow_repo.get_active_by_reader(reader_id)
        if active:
            raise ValueError(f"该读者有 {len(active)} 本书未还，无法删除")
        self.repo.delete(reader_id)


class BorrowService:
    BORROW_DAYS = 30

    def __init__(self, borrow_repo: BorrowRepository,
                 book_repo: BookRepository, reader_repo: ReaderRepository):
        self.borrow_repo = borrow_repo
        self.book_repo = book_repo
        self.reader_repo = reader_repo

    def sync_overdue(self):
        """Scan borrowed records, mark overdue if past due date."""
        today = date.today()
        records = self.borrow_repo.get_all()
        for r in records:
            if r.status == "borrowed":
                due = date.fromisoformat(r.due_date)
                if due < today:
                    r.status = "overdue"
                    self.borrow_repo.update(r)

    def borrow(self, book_id: str, reader_id: str) -> BorrowRecord:
        self.sync_overdue()

        book = self.book_repo.get_by_id(book_id)
        if not book:
            raise ValueError(f"图书 {book_id} 不存在")
        if book.stock <= 0:
            raise ValueError(f"《{book.title}》库存不足，当前库存: {book.stock}")

        reader = self.reader_repo.get_by_id(reader_id)
        if not reader:
            raise ValueError(f"读者 {reader_id} 不存在")

        # Check overdue
        active_records = self.borrow_repo.get_active_by_reader(reader_id)
        overdue_count = sum(1 for r in active_records if r.status == "overdue")
        if overdue_count > 0:
            raise ValueError(f"读者 {reader.name} 有 {overdue_count} 本书逾期未还，无法借阅")

        # Check max borrow
        if len(active_records) >= reader.max_borrow:
            raise ValueError(f"读者 {reader.name} 已达最大借阅数 ({reader.max_borrow})")

        today = date.today()
        due = today + timedelta(days=self.BORROW_DAYS)

        # Create record first
        record = BorrowRecord(
            record_id="",
            book_id=book_id,
            reader_id=reader_id,
            borrow_date=today.isoformat(),
            due_date=due.isoformat(),
        )
        record = self.borrow_repo.add(record)

        # Then update book stock
        book.stock -= 1
        self.book_repo.update(book)
        return record

    def return_book(self, record_id: str) -> BorrowRecord:
        record = self.borrow_repo.get_by_id(record_id)
        if not record:
            raise ValueError(f"借阅记录 {record_id} 不存在")
        if record.return_date is not None:
            raise ValueError("该记录已归还，无需重复操作")

        # Update record first (source of truth for "returned")
        today = date.today()
        record.return_date = today.isoformat()
        record.status = "overdue" if date.fromisoformat(record.due_date) < today else "returned"
        self.borrow_repo.update(record)

        # Then restore stock
        book = self.book_repo.get_by_id(record.book_id)
        if book:
            book.stock += 1
            self.book_repo.update(book)
        return record

    def list_records(self, book_id: str = "", reader_id: str = "",
                     status: str = "") -> list[BorrowRecord]:
        records = self.borrow_repo.get_all()
        if book_id:
            records = [r for r in records if r.book_id == book_id]
        if reader_id:
            records = [r for r in records if r.reader_id == reader_id]
        if status:
            records = [r for r in records if r.status == status]
        return records

    def get_active_by_reader(self, reader_id: str) -> list[BorrowRecord]:
        return self.borrow_repo.get_active_by_reader(reader_id)


class StatsService:
    def __init__(self, borrow_repo: BorrowRepository,
                 book_repo: BookRepository, reader_repo: ReaderRepository):
        self.borrow_repo = borrow_repo
        self.book_repo = book_repo
        self.reader_repo = reader_repo

    def top_books(self, n: int = 10) -> list[tuple[Book, int]]:
        """Most borrowed books by record count."""
        records = self.borrow_repo.get_all()
        counts: dict[str, int] = {}
        for r in records:
            counts[r.book_id] = counts.get(r.book_id, 0) + 1
        sorted_books = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        result = []
        for book_id, count in sorted_books[:n]:
            book = self.book_repo.get_by_id(book_id)
            if book:
                result.append((book, count))
        return result

    def overdue_list(self) -> list[tuple[BorrowRecord, Book, Reader]]:
        """All overdue records with book and reader info."""
        overdue = self.borrow_repo.get_overdue()
        result = []
        for r in overdue:
            book = self.book_repo.get_by_id(r.book_id)
            reader = self.reader_repo.get_by_id(r.reader_id)
            result.append((r, book, reader))
        return result

    def low_stock_books(self, threshold: int = 2) -> list[Book]:
        """Books with stock <= threshold."""
        return [b for b in self.book_repo.get_all() if b.stock <= threshold]

    def borrow_trend(self) -> list[tuple[str, int]]:
        """Borrow count grouped by month."""
        records = self.borrow_repo.get_all()
        counts: dict[str, int] = {}
        for r in records:
            month = r.borrow_date[:7]  # YYYY-MM
            counts[month] = counts.get(month, 0) + 1
        return sorted(counts.items())

    def summary(self) -> dict:
        """Overall statistics summary."""
        books = self.book_repo.get_all()
        readers = self.reader_repo.get_all()
        records = self.borrow_repo.get_all()
        active = [r for r in records if r.return_date is None]
        return {
            "total_books": len(books),
            "total_readers": len(readers),
            "total_borrowed": len(active),
            "total_overdue": len(self.borrow_repo.get_overdue()),
            "total_records": len(records),
        }
