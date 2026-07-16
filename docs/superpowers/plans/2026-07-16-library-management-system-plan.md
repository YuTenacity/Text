# 图书管理系统 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a menu-driven library management CLI with book CRUD, reader management, borrowing/returning, and statistics, persisted to JSON files.

**Architecture:** Repository pattern — each entity (Book, Reader, BorrowRecord) has its own Repository for JSON I/O, Service layer for business rules, CLI layer for menus/display. Single entry point `main.py` wires everything together.

**Tech Stack:** Python 3.10+, standard library only (dataclasses, json, datetime, os, pathlib). No external dependencies.

## Global Constraints

- Storage: JSON files under `library_data/` directory, auto-created at runtime
- IDs: auto-increment with prefix (B, R, BR) + 3-digit numeric part
- Due date: borrow_date + 30 days
- No auth, no network, no concurrency — single-user local CLI
- All user-facing text in Chinese

---

### Task 1: Package structure and data models

**Files:**
- Create: `library/__init__.py`
- Create: `library/models.py`

**Interfaces:**
- Produces: `Book`, `Reader`, `BorrowRecord` dataclasses with `to_dict()` / `from_dict()` methods

- [ ] **Step 1: Create package directory**

```bash
mkdir -p library
```

- [ ] **Step 2: Write `library/__init__.py`**

```python
"""图书管理系统 - Library Management System"""
```

- [ ] **Step 3: Write `library/models.py`**

```python
"""Data models for the library management system."""
from dataclasses import dataclass, field, asdict
from datetime import date
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
```

- [ ] **Step 4: Verify models import correctly**

```bash
cd "d:/Python测试/GitHub" && python -c "from library.models import Book, Reader, BorrowRecord; b = Book('B001', '三体', '刘慈欣', '9787535469382', '科幻', 5, '2026-07-16'); print(b.to_dict())"
```

Expected: `{'book_id': 'B001', 'title': '三体', ...}`

- [ ] **Step 5: Commit**

```bash
git add library/__init__.py library/models.py
git commit -m "feat: add package structure and data models"
```

---

### Task 2: Repositories — JSON storage layer

**Files:**
- Create: `library/repositories.py`

**Interfaces:**
- Consumes: `Book`, `Reader`, `BorrowRecord` from `library.models`
- Produces: `BookRepository`, `ReaderRepository`, `BorrowRepository` classes

- [ ] **Step 1: Write `library/repositories.py`**

```python
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
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


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
        max_num = max(int(b.book_id[1:]) for b in books)
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
        max_num = max(int(r.reader_id[1:]) for r in readers)
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
        max_num = max(int(r.record_id[2:]) for r in records)
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
        return [r for r in self._load() if r.reader_id == reader_id and r.status in ("borrowed", "overdue")]

    def get_active_by_book(self, book_id: str) -> list[BorrowRecord]:
        return [r for r in self._load() if r.book_id == book_id and r.status in ("borrowed", "overdue")]

    def get_overdue(self) -> list[BorrowRecord]:
        return [r for r in self._load() if r.status == "overdue"]

    def update(self, record: BorrowRecord) -> bool:
        records = self._load()
        for i, r in enumerate(records):
            if r.record_id == record.record_id:
                records[i] = record
                self._save(records)
                return True
        return False
```

- [ ] **Step 2: Quick smoke test — create repo, add, get, search, delete**

```bash
cd "d:/Python测试/GitHub" && python -c "
from library.repositories import BookRepository
from library.models import Book
import tempfile, os

d = tempfile.mkdtemp()
repo = BookRepository(data_dir=d)
b = repo.add(Book('', '三体', '刘慈欣', '9787535469382', '科幻', 5, '2026-07-16'))
assert b.book_id == 'B001', f'Expected B001, got {b.book_id}'
b2 = repo.get_by_id('B001')
assert b2.title == '三体'
results = repo.search(keyword='三体')
assert len(results) == 1
assert repo.delete('B001') == True
assert repo.get_by_id('B001') is None
print('All repository tests passed')
"
```

Expected: `All repository tests passed`

- [ ] **Step 3: Commit**

```bash
git add library/repositories.py
git commit -m "feat: add JSON repositories for books, readers, borrow records"
```

---

### Task 3: Services — business logic layer

**Files:**
- Create: `library/services.py`

**Interfaces:**
- Consumes: models from `library.models`, repos from `library.repositories`
- Produces: `BookService`, `ReaderService`, `BorrowService`, `StatsService`

- [ ] **Step 1: Write `library/services.py`**

```python
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

        # Update book stock
        book.stock -= 1
        self.book_repo.update(book)

        # Create record
        record = BorrowRecord(
            record_id="",
            book_id=book_id,
            reader_id=reader_id,
            borrow_date=today.isoformat(),
            due_date=due.isoformat(),
        )
        return self.borrow_repo.add(record)

    def return_book(self, record_id: str) -> BorrowRecord:
        record = self.borrow_repo.get_by_id(record_id)
        if not record:
            raise ValueError(f"借阅记录 {record_id} 不存在")
        if record.status not in ("borrowed", "overdue"):
            raise ValueError(f"该记录状态为 {record.status}，无需归还")

        # Restore stock
        book = self.book_repo.get_by_id(record.book_id)
        if book:
            book.stock += 1
            self.book_repo.update(book)

        # Update record
        today = date.today()
        record.return_date = today.isoformat()
        record.status = "overdue" if date.fromisoformat(record.due_date) < today else "returned"
        self.borrow_repo.update(record)
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
        active = self.borrow_repo.get_overdue() + [
            r for r in records if r.status == "borrowed"
        ]
        return {
            "total_books": len(books),
            "total_readers": len(readers),
            "total_borrowed": len(active),
            "total_overdue": len(self.borrow_repo.get_overdue()),
            "total_records": len(records),
        }
```

- [ ] **Step 2: Smoke test services**

```bash
cd "d:/Python测试/GitHub" && python -c "
from library.repositories import BookRepository, ReaderRepository, BorrowRepository
from library.services import BookService, ReaderService, BorrowService, StatsService
import tempfile, os

d = tempfile.mkdtemp()
br = BookRepository(d)
rr = ReaderRepository(d)
bor = BorrowRepository(d)

bs = BookService(br)
rs = ReaderService(rr)
bors = BorrowService(bor, br, rr)
ss = StatsService(bor, br, rr)

# Add book and reader
book = bs.add_book('三体', '刘慈欣', '9787535469382', '科幻', 5)
reader = rs.add_reader('张三', '13800138000')
assert book.book_id == 'B001'
assert reader.reader_id == 'R001'

# Borrow
record = bors.borrow('B001', 'R001')
assert record.status == 'borrowed'
book2 = bs.get_book('B001')
assert book2.stock == 4

# Return
bors.return_book(record.record_id)
book3 = bs.get_book('B001')
assert book3.stock == 5

# Stats
s = ss.summary()
assert s['total_books'] == 1
assert s['total_readers'] == 1
assert s['total_records'] == 1

# Delete guard
record2 = bors.borrow('B001', 'R001')
try:
    bs.delete_book('B001', bor)
    assert False, 'Should have raised'
except ValueError:
    pass  # expected

print('All service tests passed')
"
```

Expected: `All service tests passed`

- [ ] **Step 3: Commit**

```bash
git add library/services.py
git commit -m "feat: add business logic services"
```

---

### Task 4: CLI — menu and display layer

**Files:**
- Create: `library/cli.py`

**Interfaces:**
- Consumes: `BookService`, `ReaderService`, `BorrowService`, `StatsService`
- Produces: `LibraryCLI` class with `run()` method

- [ ] **Step 1: Write `library/cli.py`**

```python
"""CLI menu rendering and input handling."""
from datetime import date
from typing import Optional

from library.services import BookService, ReaderService, BorrowService, StatsService


class LibraryCLI:
    def __init__(self, book_service: BookService, reader_service: ReaderService,
                 borrow_service: BorrowService, stats_service: StatsService):
        self.bs = book_service
        self.rs = reader_service
        self.bors = borrow_service
        self.ss = stats_service

    # --- Helpers ---

    def _input(self, prompt: str) -> str:
        return input(prompt).strip()

    def _confirm(self, msg: str) -> bool:
        ans = input(f"{msg} (y/n): ").strip().lower()
        return ans == "y"

    def _wait(self):
        input("\n按回车键返回主菜单...")

    def _print_table(self, headers: list[str], rows: list[list[str]]):
        if not rows:
            print("  (暂无数据)")
            return
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        fmt = "  " + "  ".join(f"{{:<{w}}}" for w in col_widths)
        print(fmt.format(*headers))
        print("  " + "-" * (sum(col_widths) + 2 * (len(headers) - 1)))
        for row in rows:
            print(fmt.format(*[str(c) for c in row]))
        print(f"  共 {len(rows)} 条记录")

    # --- Main menu ---

    def run(self):
        while True:
            self._show_main_menu()
            choice = self._input("请选择: ")
            if choice == "1":
                self._book_menu()
            elif choice == "2":
                self._reader_menu()
            elif choice == "3":
                self._borrow_menu()
            elif choice == "4":
                self._stats_menu()
            elif choice == "0":
                print("再见！")
                break
            else:
                print("无效选择，请重新输入")

    def _show_main_menu(self):
        print("\n" + "=" * 50)
        print("        图 书 管 理 系 统")
        print("=" * 50)
        print("  1. 图书管理")
        print("  2. 读者管理")
        print("  3. 借阅管理")
        print("  4. 统计报表")
        print("  0. 退出")
        print("-" * 50)

    # --- Book menu ---

    def _book_menu(self):
        while True:
            print("\n--- 图书管理 ---")
            print("  1. 添加图书    2. 查询图书")
            print("  3. 修改图书    4. 删除图书")
            print("  5. 图书列表    6. 搜索图书")
            print("  0. 返回主菜单")
            choice = self._input("请选择: ")
            if choice == "1":
                self._add_book()
            elif choice == "2":
                self._get_book()
            elif choice == "3":
                self._update_book()
            elif choice == "4":
                self._delete_book()
            elif choice == "5":
                self._list_books()
            elif choice == "6":
                self._search_books()
            elif choice == "0":
                break
            else:
                print("无效选择")

    def _add_book(self):
        print("\n--- 添加图书 ---")
        try:
            title = self._input("书名: ")
            author = self._input("作者: ")
            isbn = self._input("ISBN: ")
            category = self._input("分类: ")
            stock = int(self._input("库存: ") or "0")
            book = self.bs.add_book(title, author, isbn, category, stock)
            print(f"添加成功！图书编号: {book.book_id}")
        except ValueError as e:
            print(f"错误: {e}")

    def _get_book(self):
        print("\n--- 查询图书 ---")
        book_id = self._input("图书编号: ")
        book = self.bs.get_book(book_id)
        if book:
            self._show_book_detail(book)
        else:
            print(f"未找到图书 {book_id}")

    def _show_book_detail(self, book):
        print(f"\n  编号: {book.book_id}")
        print(f"  书名: {book.title}")
        print(f"  作者: {book.author}")
        print(f"  ISBN: {book.isbn}")
        print(f"  分类: {book.category}")
        print(f"  库存: {book.stock}")
        print(f"  入库日期: {book.created_at}")

    def _update_book(self):
        print("\n--- 修改图书 ---")
        book_id = self._input("图书编号: ")
        book = self.bs.get_book(book_id)
        if not book:
            print(f"未找到图书 {book_id}")
            return
        print("(直接回车保留原值)")
        try:
            title = self._input(f"书名 [{book.title}]: ")
            author = self._input(f"作者 [{book.author}]: ")
            isbn = self._input(f"ISBN [{book.isbn}]: ")
            category = self._input(f"分类 [{book.category}]: ")
            stock = self._input(f"库存 [{book.stock}]: ")
            kwargs = {"title": title, "author": author, "isbn": isbn,
                      "category": category, "stock": int(stock) if stock else ""}
            self.bs.update_book(book_id, **{k: v for k, v in kwargs.items() if v != ""})
            print("修改成功！")
        except ValueError as e:
            print(f"错误: {e}")

    def _delete_book(self):
        print("\n--- 删除图书 ---")
        book_id = self._input("图书编号: ")
        book = self.bs.get_book(book_id)
        if not book:
            print(f"未找到图书 {book_id}")
            return
        self._show_book_detail(book)
        if not self._confirm(f"确认删除《{book.title}》?"):
            return
        try:
            self.bs.delete_book(book_id, self.bors.borrow_repo)
            print("删除成功！")
        except ValueError as e:
            print(f"错误: {e}")

    def _list_books(self):
        print("\n--- 图书列表 ---")
        books = self.bs.list_books()
        headers = ["编号", "书名", "作者", "分类", "库存"]
        rows = [[b.book_id, b.title, b.author, b.category, str(b.stock)] for b in books]
        self._print_table(headers, rows)
        self._wait()

    def _search_books(self):
        print("\n--- 搜索图书 ---")
        keyword = self._input("关键词（书名/作者，可留空）: ")
        category = self._input("分类（可留空）: ")
        books = self.bs.search_books(keyword=keyword, category=category)
        headers = ["编号", "书名", "作者", "分类", "库存"]
        rows = [[b.book_id, b.title, b.author, b.category, str(b.stock)] for b in books]
        self._print_table(headers, rows)
        self._wait()

    # --- Reader menu ---

    def _reader_menu(self):
        while True:
            print("\n--- 读者管理 ---")
            print("  1. 添加读者    2. 查询读者")
            print("  3. 修改读者    4. 删除读者")
            print("  5. 读者列表    6. 搜索读者")
            print("  0. 返回主菜单")
            choice = self._input("请选择: ")
            if choice == "1":
                self._add_reader()
            elif choice == "2":
                self._get_reader()
            elif choice == "3":
                self._update_reader()
            elif choice == "4":
                self._delete_reader()
            elif choice == "5":
                self._list_readers()
            elif choice == "6":
                self._search_readers()
            elif choice == "0":
                break
            else:
                print("无效选择")

    def _add_reader(self):
        print("\n--- 添加读者 ---")
        try:
            name = self._input("姓名: ")
            phone = self._input("电话: ")
            max_borrow = self._input("最大借阅数 [3]: ") or "3"
            reader = self.rs.add_reader(name, phone, int(max_borrow))
            print(f"添加成功！读者编号: {reader.reader_id}")
        except ValueError as e:
            print(f"错误: {e}")

    def _get_reader(self):
        print("\n--- 查询读者 ---")
        reader_id = self._input("读者编号: ")
        reader = self.rs.get_reader(reader_id)
        if reader:
            self._show_reader_detail(reader)
        else:
            print(f"未找到读者 {reader_id}")

    def _show_reader_detail(self, reader):
        print(f"\n  编号: {reader.reader_id}")
        print(f"  姓名: {reader.name}")
        print(f"  电话: {reader.phone}")
        print(f"  最大借阅数: {reader.max_borrow}")
        print(f"  注册日期: {reader.created_at}")
        active = self.bors.get_active_by_reader(reader.reader_id)
        print(f"  当前借阅: {len(active)} 本")

    def _update_reader(self):
        print("\n--- 修改读者 ---")
        reader_id = self._input("读者编号: ")
        reader = self.rs.get_reader(reader_id)
        if not reader:
            print(f"未找到读者 {reader_id}")
            return
        print("(直接回车保留原值)")
        try:
            name = self._input(f"姓名 [{reader.name}]: ")
            phone = self._input(f"电话 [{reader.phone}]: ")
            max_borrow = self._input(f"最大借阅数 [{reader.max_borrow}]: ")
            kwargs = {"name": name, "phone": phone, "max_borrow": max_borrow}
            self.rs.update_reader(reader_id, **{k: v for k, v in kwargs.items() if v != ""})
            print("修改成功！")
        except ValueError as e:
            print(f"错误: {e}")

    def _delete_reader(self):
        print("\n--- 删除读者 ---")
        reader_id = self._input("读者编号: ")
        reader = self.rs.get_reader(reader_id)
        if not reader:
            print(f"未找到读者 {reader_id}")
            return
        self._show_reader_detail(reader)
        if not self._confirm(f"确认删除读者 {reader.name}?"):
            return
        try:
            self.rs.delete_reader(reader_id, self.bors.borrow_repo)
            print("删除成功！")
        except ValueError as e:
            print(f"错误: {e}")

    def _list_readers(self):
        print("\n--- 读者列表 ---")
        readers = self.rs.list_readers()
        headers = ["编号", "姓名", "电话", "最大借阅数", "注册日期"]
        rows = [[r.reader_id, r.name, r.phone, str(r.max_borrow), r.created_at] for r in readers]
        self._print_table(headers, rows)
        self._wait()

    def _search_readers(self):
        print("\n--- 搜索读者 ---")
        keyword = self._input("关键词（姓名/编号，可留空）: ")
        readers = self.rs.search_readers(keyword=keyword)
        headers = ["编号", "姓名", "电话", "最大借阅数", "注册日期"]
        rows = [[r.reader_id, r.name, r.phone, str(r.max_borrow), r.created_at] for r in readers]
        self._print_table(headers, rows)
        self._wait()

    # --- Borrow menu ---

    def _borrow_menu(self):
        while True:
            print("\n--- 借阅管理 ---")
            print("  1. 借书        2. 还书")
            print("  3. 借阅记录查询")
            print("  0. 返回主菜单")
            choice = self._input("请选择: ")
            if choice == "1":
                self._borrow_book()
            elif choice == "2":
                self._return_book()
            elif choice == "3":
                self._borrow_records()
            elif choice == "0":
                break
            else:
                print("无效选择")

    def _borrow_book(self):
        print("\n--- 借书 ---")
        try:
            book_id = self._input("图书编号: ")
            reader_id = self._input("读者编号: ")
            record = self.bors.borrow(book_id, reader_id)
            print(f"借阅成功！记录编号: {record.record_id}")
            print(f"应还日期: {record.due_date}")
        except ValueError as e:
            print(f"错误: {e}")

    def _return_book(self):
        print("\n--- 还书 ---")
        try:
            record_id = self._input("借阅记录编号: ")
            record = self.bors.return_book(record_id)
            status_text = "逾期归还" if record.status == "overdue" else "正常归还"
            print(f"还书成功！状态: {status_text}")
        except ValueError as e:
            print(f"错误: {e}")

    def _borrow_records(self):
        print("\n--- 借阅记录查询 ---")
        print("(直接回车表示不过滤该条件)")
        book_id = self._input("图书编号: ")
        reader_id = self._input("读者编号: ")
        status = self._input("状态 (borrowed/returned/overdue): ")
        records = self.bors.list_records(book_id=book_id, reader_id=reader_id, status=status)
        headers = ["记录编号", "图书编号", "读者编号", "借阅日期", "应还日期", "归还日期", "状态"]
        rows = [[r.record_id, r.book_id, r.reader_id, r.borrow_date, r.due_date,
                 r.return_date or "-", r.status] for r in records]
        self._print_table(headers, rows)
        self._wait()

    # --- Stats menu ---

    def _stats_menu(self):
        while True:
            print("\n--- 统计报表 ---")
            print("  1. 热门图书    2. 借阅趋势")
            print("  3. 逾期清单    4. 库存告警")
            print("  5. 总体概览")
            print("  0. 返回主菜单")
            choice = self._input("请选择: ")
            if choice == "1":
                self._top_books()
            elif choice == "2":
                self._borrow_trend()
            elif choice == "3":
                self._overdue_list()
            elif choice == "4":
                self._low_stock()
            elif choice == "5":
                self._summary()
            elif choice == "0":
                break
            else:
                print("无效选择")

    def _top_books(self):
        print("\n--- 热门图书 ---")
        n = int(self._input("显示前几名 [10]: ") or "10")
        results = self.ss.top_books(n)
        headers = ["排名", "编号", "书名", "作者", "借阅次数"]
        rows = [[str(i + 1), b.book_id, b.title, b.author, str(c)] for i, (b, c) in enumerate(results)]
        self._print_table(headers, rows)
        self._wait()

    def _borrow_trend(self):
        print("\n--- 借阅趋势（按月） ---")
        trend = self.ss.borrow_trend()
        headers = ["月份", "借阅次数"]
        rows = [[month, str(count)] for month, count in trend]
        self._print_table(headers, rows)
        self._wait()

    def _overdue_list(self):
        print("\n--- 逾期未还清单 ---")
        items = self.ss.overdue_list()
        headers = ["记录编号", "书名", "借阅人", "应还日期", "逾期天数"]
        today = date.today()
        rows = []
        for r, book, reader in items:
            book_title = book.title if book else "?"
            reader_name = reader.name if reader else "?"
            days = (today - date.fromisoformat(r.due_date)).days
            rows.append([r.record_id, book_title, reader_name, r.due_date, str(days)])
        self._print_table(headers, rows)
        self._wait()

    def _low_stock(self):
        print("\n--- 库存不足告警（库存 <= 2） ---")
        books = self.ss.low_stock_books()
        headers = ["编号", "书名", "作者", "库存"]
        rows = [[b.book_id, b.title, b.author, str(b.stock)] for b in books]
        self._print_table(headers, rows)
        self._wait()

    def _summary(self):
        print("\n--- 总体概览 ---")
        s = self.ss.summary()
        print(f"  馆藏图书: {s['total_books']} 种")
        print(f"  注册读者: {s['total_readers']} 人")
        print(f"  借出/逾期: {s['total_borrowed']} 本")
        print(f"  逾期未还: {s['total_overdue']} 本")
        print(f"  历史借阅: {s['total_records']} 次")
        self._wait()
```

- [ ] **Step 2: Quick smoke test CLI import**

```bash
cd "d:/Python测试/GitHub" && python -c "from library.cli import LibraryCLI; print('CLI module OK')"
```

Expected: `CLI module OK`

- [ ] **Step 3: Commit**

```bash
git add library/cli.py
git commit -m "feat: add CLI menu and display layer"
```

---

### Task 5: Main entry point

**Files:**
- Create: `library/main.py`

**Interfaces:**
- Consumes: all modules from `library.*`
- Produces: `main()` function — CLI entry point

- [ ] **Step 1: Write `library/main.py`**

```python
"""Entry point for the library management system."""
import sys
from pathlib import Path

# Ensure library_data directory is relative to the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = str(PROJECT_ROOT / "library_data")

from library.repositories import BookRepository, ReaderRepository, BorrowRepository
from library.services import BookService, ReaderService, BorrowService, StatsService
from library.cli import LibraryCLI


def main():
    # Init repositories
    book_repo = BookRepository(data_dir=DATA_DIR)
    reader_repo = ReaderRepository(data_dir=DATA_DIR)
    borrow_repo = BorrowRepository(data_dir=DATA_DIR)

    # Init services
    book_service = BookService(book_repo)
    reader_service = ReaderService(reader_repo)
    borrow_service = BorrowService(borrow_repo, book_repo, reader_repo)
    stats_service = StatsService(borrow_repo, book_repo, reader_repo)

    # Sync overdue status
    borrow_service.sync_overdue()

    # Launch CLI
    cli = LibraryCLI(book_service, reader_service, borrow_service, stats_service)
    try:
        cli.run()
    except KeyboardInterrupt:
        print("\n\n再见！")
        sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify imports resolve**

```bash
cd "d:/Python测试/GitHub" && python -c "from library.main import main; print('Entry point OK')"
```

Expected: `Entry point OK`

- [ ] **Step 3: Commit**

```bash
git add library/main.py
git commit -m "feat: add main entry point"
```

---

### Task 6: End-to-end integration test

**Files:**
- Create: `tests/`
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration tests**

```bash
mkdir -p tests
```

Write `tests/test_integration.py`:

```python
"""Integration tests for the library management system."""
import tempfile
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from library.repositories import BookRepository, ReaderRepository, BorrowRepository
from library.services import BookService, ReaderService, BorrowService, StatsService


def test_full_borrow_return_flow():
    """End-to-end: add book, add reader, borrow, return, verify stock."""
    d = tempfile.mkdtemp()
    br = BookRepository(d)
    rr = ReaderRepository(d)
    bor = BorrowRepository(d)

    bs = BookService(br)
    rs = ReaderService(rr)
    bors = BorrowService(bor, br, rr)
    ss = StatsService(bor, br, rr)

    # Add 3 books
    b1 = bs.add_book("三体", "刘慈欣", "111", "科幻", 3)
    b2 = bs.add_book("活着", "余华", "222", "文学", 2)
    b3 = bs.add_book("三体2", "刘慈欣", "333", "科幻", 1)

    # Add 2 readers
    r1 = rs.add_reader("张三", "13800138000")
    r2 = rs.add_reader("李四", "13900139000", max_borrow=2)

    # Borrow
    rec1 = bors.borrow(b1.book_id, r1.reader_id)
    assert b1.book_id in rec1.book_id
    assert bs.get_book(b1.book_id).stock == 2

    rec2 = bors.borrow(b2.book_id, r1.reader_id)
    assert bs.get_book(b2.book_id).stock == 1

    rec3 = bors.borrow(b1.book_id, r2.reader_id)
    assert bs.get_book(b1.book_id).stock == 1

    # Reader at max borrow (3), should fail
    try:
        bors.borrow(b3.book_id, r1.reader_id)
        assert False, "Should raise — reader at max"
    except ValueError:
        pass

    # Return one, then borrow again
    bors.return_book(rec1.record_id)
    assert bs.get_book(b1.book_id).stock == 2
    rec4 = bors.borrow(b3.book_id, r1.reader_id)
    assert bs.get_book(b3.book_id).stock == 0

    # Stock 0, should fail
    try:
        bors.borrow(b3.book_id, r2.reader_id)
        assert False, "Should raise — out of stock"
    except ValueError:
        pass

    # Delete guard — book has active records
    try:
        bs.delete_book(b1.book_id, bor)
        assert False, "Should raise — has active borrows"
    except ValueError:
        pass

    # Delete guard — reader has active records
    try:
        rs.delete_reader(r1.reader_id, bor)
        assert False, "Should raise — has active borrows"
    except ValueError:
        pass

    # Return all, then delete should work
    bors.return_book(rec2.record_id)
    bors.return_book(rec3.record_id)
    bors.return_book(rec4.record_id)
    bs.delete_book(b1.book_id, bor)
    assert bs.get_book(b1.book_id) is None

    # Stats
    s = ss.summary()
    assert s["total_books"] == 2  # b1 deleted
    assert s["total_records"] == 4
    assert s["total_borrowed"] == 0

    # Low stock
    low = ss.low_stock_books()
    assert len(low) == 2  # b2 stock=1, b3 stock=0

    # Top books
    top = ss.top_books(10)
    assert len(top) == 2  # b2 and b3 only remain


def test_overdue_sync():
    """Overdue records marked correctly on sync."""
    d = tempfile.mkdtemp()
    br = BookRepository(d)
    rr = ReaderRepository(d)
    bor = BorrowRepository(d)
    bors = BorrowService(bor, br, rr)

    bs = BookService(br)
    rs = ReaderService(rr)

    book = bs.add_book("测试", "作者", "000", "测试", 1)
    reader = rs.add_reader("测试人", "111")

    # Manually create an overdue record
    from library.models import BorrowRecord
    from datetime import date, timedelta
    past_date = (date.today() - timedelta(days=40)).isoformat()
    due_date = (date.today() - timedelta(days=10)).isoformat()
    record = BorrowRecord(
        record_id="",
        book_id=book.book_id,
        reader_id=reader.reader_id,
        borrow_date=past_date,
        due_date=due_date,
        status="borrowed",
    )
    bor.add(record)

    # Before sync: status is borrowed
    r = bor.get_all()[0]
    assert r.status == "borrowed"

    # Sync
    bors.sync_overdue()

    # After sync: status is overdue
    r = bor.get_all()[0]
    assert r.status == "overdue"

    # Reader with overdue cannot borrow
    book2 = bs.add_book("测试2", "作者2", "0002", "测试", 5)
    try:
        bors.borrow(book2.book_id, reader.reader_id)
        assert False, "Should raise — reader has overdue"
    except ValueError:
        pass


if __name__ == "__main__":
    test_full_borrow_return_flow()
    test_overdue_sync()
    print("All integration tests passed!")
```

- [ ] **Step 2: Run integration tests**

```bash
cd "d:/Python测试/GitHub" && python tests/test_integration.py
```

Expected: `All integration tests passed!`

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests for borrow/return flow"
```

---

### Task 7: Add `__init__.py` convenience exports

**Files:**
- Modify: `library/__init__.py`

- [ ] **Step 1: Re-export key classes from `library/__init__.py`**

```python
"""图书管理系统 - Library Management System"""
from library.models import Book, Reader, BorrowRecord
from library.repositories import BookRepository, ReaderRepository, BorrowRepository
from library.services import BookService, ReaderService, BorrowService, StatsService
from library.cli import LibraryCLI
from library.main import main
```

- [ ] **Step 2: Verify all exports resolve**

```bash
cd "d:/Python测试/GitHub" && python -c "from library import Book, Reader, BorrowRecord, BookRepository, ReaderRepository, BorrowRepository, BookService, ReaderService, BorrowService, StatsService, LibraryCLI, main; print('All exports OK')"
```

Expected: `All exports OK`

- [ ] **Step 3: Commit**

```bash
git add library/__init__.py
git commit -m "refactor: add convenience exports to __init__.py"
```

---

### Task 8: README with usage instructions

**Files:**
- Create: `README.md` (or update existing)

- [ ] **Step 1: Write usage section**

Add to project root a README (check if one exists first). If none, create `README.md`:

```markdown
# 图书管理系统

Python CLI 图书管理系统，支持图书管理、读者管理、借阅管理和统计报表。

## 运行

```bash
python -m library.main
# 或
python library/main.py
```

## 功能

- **图书管理**: 添加、查询、修改、删除、搜索图书
- **读者管理**: 添加、查询、修改、删除、搜索读者
- **借阅管理**: 借书、还书、借阅记录查询
- **统计报表**: 热门图书、借阅趋势、逾期清单、库存告警、总体概览

## 数据存储

数据保存在 `library_data/` 目录下的 JSON 文件中：
- `books.json` — 图书数据
- `readers.json` — 读者数据
- `borrow_records.json` — 借阅记录

## 运行测试

```bash
python tests/test_integration.py
```
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with usage instructions"
```
