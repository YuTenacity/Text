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
    r1 = rs.add_reader("张三", "13800138000", max_borrow=2)
    r2 = rs.add_reader("李四", "13900139000", max_borrow=2)

    # Borrow
    rec1 = bors.borrow(b1.book_id, r1.reader_id)
    assert b1.book_id in rec1.book_id
    assert bs.get_book(b1.book_id).stock == 2

    rec2 = bors.borrow(b2.book_id, r1.reader_id)
    assert bs.get_book(b2.book_id).stock == 1

    rec3 = bors.borrow(b1.book_id, r2.reader_id)
    assert bs.get_book(b1.book_id).stock == 1

    # Reader at max borrow (2 active >= max_borrow 2), should fail
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
    assert len(low) == 2  # b2 stock=2, b3 stock=1 (after returns), both <= threshold 2

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
