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

## 借阅规则

- 借阅期限 30 天，逾期未还将无法继续借书
- 每位读者默认最多同时借 3 本（可单独设置）
- 图书/读者有未还记录时不可删除

## 数据存储

数据保存在 `library_data/` 目录下的 JSON 文件中：

- `books.json` — 图书数据
- `readers.json` — 读者数据
- `borrow_records.json` — 借阅记录

## 运行测试

```bash
python tests/test_integration.py
```
