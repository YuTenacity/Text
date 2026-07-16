# Library Management System — Design Spec

**Date:** 2026-07-16
**Type:** Python CLI Application
**Storage:** JSON files

## Overview

Menu-driven library management system with book CRUD, reader management, borrowing/returning, and statistics. Runs as interactive CLI, data persisted to JSON files.

## Directory Structure

```
GitHub/
├── library/
│   ├── __init__.py
│   ├── main.py          # Entry point, main menu loop
│   ├── cli.py           # Menu rendering and display formatting
│   ├── models.py        # Dataclasses: Book, Reader, BorrowRecord
│   ├── services.py      # Business logic: borrow/return rules, statistics
│   └── repositories.py  # JSON read/write, one Repo per entity
└── library_data/        # Auto-created at runtime
    ├── books.json
    ├── readers.json
    └── borrow_records.json
```

## Data Models

### Book
| Field | Type | Description |
|-------|------|-------------|
| book_id | str | Auto-increment "B001" |
| title | str | Book title |
| author | str | Author name |
| isbn | str | ISBN |
| category | str | Category (文学/科技/历史...) |
| stock | int | Copies available |
| created_at | str | ISO date |

### Reader
| Field | Type | Description |
|-------|------|-------------|
| reader_id | str | Auto-increment "R001" |
| name | str | Reader name |
| phone | str | Phone number |
| max_borrow | int | Max books allowed (default 3) |
| created_at | str | ISO date |

### BorrowRecord
| Field | Type | Description |
|-------|------|-------------|
| record_id | str | Auto-increment "BR001" |
| book_id | str | FK to Book |
| reader_id | str | FK to Reader |
| borrow_date | str | ISO date |
| due_date | str | borrow_date + 30 days |
| return_date | str \| None | None = not returned |
| status | str | "borrowed" / "returned" / "overdue" |

### ID Generation
Read max ID from existing JSON data, increment numeric part, pad to 3 digits.

## Menu Structure

```
=== 图书管理系统 ===
1. 图书管理
   1.1 添加图书    1.2 查询图书
   1.3 修改图书    1.4 删除图书
   1.5 图书列表    1.6 搜索图书（按书名/作者/分类）
2. 读者管理
   2.1 添加读者    2.2 查询读者
   2.3 修改读者    2.4 删除读者
3. 借阅管理
   3.1 借书        3.2 还书
   3.3 借阅记录查询
4. 统计报表
   4.1 热门图书 Top N    4.2 借阅趋势
   4.3 逾期未还清单      4.4 库存不足告警
0. 退出
```

## Business Rules

### Borrow
- Check stock > 0
- Check reader has no overdue books
- Check reader hasn't reached max_borrow limit
- On success: stock -= 1, create BorrowRecord with status "borrowed", due_date = today + 30 days

### Return
- On success: stock += 1, set return_date = today
- If return_date > due_date → status = "overdue"
- Else → status = "returned"

### Delete Guards
- Book: refuse if any borrow record with status "borrowed" or "overdue" references it
- Reader: refuse if has unreturned books

### Overdue Sync
On startup, scan all "borrowed" records — if due_date < today, set status = "overdue".

## Module Responsibilities

### models.py
Pure dataclasses. No logic. `to_dict()` / `from_dict()` serialization.

### repositories.py
- `BookRepository` — load/save books.json, CRUD + search
- `ReaderRepository` — load/save readers.json, CRUD + search
- `BorrowRepository` — load/save borrow_records.json, CRUD + filter
- Each Repo loads entire JSON on init, writes on save. Small datasets, no need for incremental writes.

### services.py
- `BookService` — delegates to BookRepo, validates ISBN uniqueness
- `ReaderService` — delegates to ReaderRepo, validates phone format
- `BorrowService` — borrow/return logic, due date calculation, overdue scan
- `StatsService` — aggregation queries: top books, trends, overdue list, low-stock alert

### cli.py
- Menu display functions, each returning to submenu or main
- Input validation loop (retry on invalid input)
- Formatted table output using string formatting

### main.py
- Init repos → init services → overdue sync → main menu loop
- Exit saves all data

## Error Handling

- JSON file not found → create empty data, continue
- Invalid user input → show error, retry
- Business rule violation → show specific message (e.g. "该书已被借出，无法删除")
- JSON parse error → backup corrupted file, start fresh

## Testing Strategy

- Unit tests per service with mock repos
- Integration tests for borrow/return flow
- Manual smoke test of all menu paths

## Scope

One-time build. No auth, no network, no concurrency. Single-user local CLI tool.
