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
