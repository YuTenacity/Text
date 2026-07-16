"""图书管理系统 - Library Management System"""
from library.models import Book, Reader, BorrowRecord
from library.repositories import BookRepository, ReaderRepository, BorrowRepository
from library.services import BookService, ReaderService, BorrowService, StatsService
from library.cli import LibraryCLI
