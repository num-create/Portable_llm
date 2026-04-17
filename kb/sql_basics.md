# SQL 基础速查

## 常用查询

```sql
SELECT col1, col2 FROM table WHERE condition ORDER BY col DESC LIMIT 10;
SELECT DISTINCT col FROM table;
SELECT col, COUNT(*) FROM table GROUP BY col HAVING COUNT(*) > 5;
```

## JOIN 类型

| 类型 | 说明 |
|------|------|
| INNER JOIN | 两表匹配的行 |
| LEFT JOIN | 左表全部，右表无匹配为NULL |
| RIGHT JOIN | 右表全部 |
| FULL JOIN | 两表全部 |

```sql
SELECT a.*, b.* FROM table_a a LEFT JOIN table_b b ON a.id = b.a_id;
```

## 子查询

```sql
WHERE col > (SELECT AVG(col) FROM table)       -- 比平均值大
WHERE id IN (SELECT id FROM other_table)       -- IN子查询
WHERE EXISTS (SELECT 1 FROM t WHERE t.id = a.id)  -- EXISTS
```

## 聚合函数

```sql
COUNT(*) / COUNT(DISTINCT col)  -- 计数
SUM(col) / AVG(col)             -- 求和/平均
MAX(col) / MIN(col)             -- 最大/最小
```

## INSERT/UPDATE/DELETE

```sql
INSERT INTO table (col1, col2) VALUES (v1, v2), (v3, v4);  -- 批量插入
UPDATE table SET col = value WHERE condition;
DELETE FROM table WHERE condition;
TRUNCATE TABLE table;  -- 快速清空
```

## 表操作

```sql
CREATE TABLE t (id INT PRIMARY KEY, name VARCHAR(50) NOT NULL);
ALTER TABLE t ADD col VARCHAR(100);
ALTER TABLE t DROP COLUMN col;
DROP TABLE t;
```

## 索引

```sql
CREATE INDEX idx_name ON table(col);
CREATE UNIQUE INDEX idx_unique ON table(col);
CREATE INDEX idx_multi ON table(col1, col2);  -- 复合索引，遵循最左前缀
DROP INDEX idx_name;
```

## 常用函数

| 字符串 | 数值 | 日期 |
|--------|------|------|
| LENGTH(s) | ABS(n) | NOW() |
| UPPER/LOWER(s) | ROUND(n,2) | DATE_ADD(d, INTERVAL 1 DAY) |
| SUBSTR(s,1,3) | CEIL/FLOOR(n) | DATE_FORMAT(d, '%Y-%m-%d') |
| REPLACE(s,a,b) | MOD(a,b) | YEAR/MONTH/DAY(d) |
| CONCAT(a,b) | | |

## 条件表达式

```sql
CASE WHEN x > 10 THEN '高' WHEN x > 5 THEN '中' ELSE '低' END
IFNULL(col, 0)  -- NULL替换
COALESCE(a, b, c)  -- 返回第一个非空值
```

## 窗口函数

```sql
ROW_NUMBER() OVER (ORDER BY col)             -- 行号
RANK() OVER (ORDER BY col)                   -- 排名(有跳跃)
DENSE_RANK() OVER (ORDER BY col)             -- 排名(无跳跃)
SUM(col) OVER (PARTITION BY group)           -- 分组聚合
```

## 事务

```sql
BEGIN; COMMIT; ROLLBACK;
SAVEPOINT sp1; ROLLBACK TO sp1;
```

隔离级别：READ COMMITTED(默认) → REPEATABLE READ → SERIALIZABLE

## 性能优化要点

- 避免 SELECT *，只查需要的字段
- WHERE 中避免用函数（索引失效）
- LIKE 避免前导通配符 `%xxx`
- 小表驱动大表
- 用 EXISTS 替代 IN（大子查询时）