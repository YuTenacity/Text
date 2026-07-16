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
            stock_str = self._input("库存: ") or "0"
            if not stock_str.lstrip("-").isdigit():
                print("错误: 库存请输入数字")
                return
            stock = int(stock_str)
            if stock < 0:
                print("错误: 库存不能为负数")
                return
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
            if stock:
                if not stock.lstrip("-").isdigit():
                    print("错误: 库存请输入非负数字")
                    return
                if int(stock) < 0:
                    print("错误: 库存请输入非负数字")
                    return
                stock = int(stock)
            kwargs = {"title": title, "author": author, "isbn": isbn,
                      "category": category, "stock": stock}
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
            if not max_borrow.isdigit() or int(max_borrow) <= 0:
                print("错误: 最大借阅数请输入正整数")
                return
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
            if max_borrow:
                if not max_borrow.isdigit() or int(max_borrow) <= 0:
                    print("错误: 最大借阅数请输入正整数")
                    return
                max_borrow = int(max_borrow)
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
        self.bors.sync_overdue()
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
        try:
            n = int(self._input("显示前几名 [10]: ") or "10")
        except ValueError:
            print("错误: 请输入数字")
            return
        if n <= 0:
            print("错误: 请输入正整数")
            return
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
        self.bors.sync_overdue()
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
        self.bors.sync_overdue()
        print("\n--- 总体概览 ---")
        s = self.ss.summary()
        print(f"  馆藏图书: {s['total_books']} 种")
        print(f"  注册读者: {s['total_readers']} 人")
        print(f"  借出/逾期: {s['total_borrowed']} 本")
        print(f"  逾期未还: {s['total_overdue']} 本")
        print(f"  历史借阅: {s['total_records']} 次")
        self._wait()
