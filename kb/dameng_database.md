# 达梦数据库速查

## 基础信息

- 默认端口：5236
- 超级管理员：SYSDBA
- JDBC：`jdbc:dm://host:5236`，驱动：`dm.jdbc.driver.DmDriver`

## 标识符规则

- 不用引号：自动转大写存储
- 用双引号 `"name"`：保持原大小写，查询时必须加引号

## 数据类型

| 类型 | 说明 |
|------|------|
| INT/BIGINT | 整数 |
| DECIMAL(p,s)/NUMBER(p,s) | 定点数 |
| VARCHAR(n) | 变长字符，最大8188字节 |
| TEXT/CLOB | 大文本 |
| DATE/TIMESTAMP | 日期时间 |

## 常用函数

```sql
-- 字符
LENGTH('文本') / LENGTHB('文本')    -- 字符数/字节数
SUBSTR('文本', 1, 2)                -- 截取
INSTR('abc', 'b')                   -- 位置
REPLACE('abc', 'b', 'x')            -- 替换
'Hello' || ' World'                 -- 连接

-- 日期
SYSDATE / SYSTIMESTAMP              -- 当前时间
TO_CHAR(SYSDATE, 'YYYY-MM-DD')      -- 格式化
TO_DATE('2024-01-01', 'YYYY-MM-DD') -- 字符转日期
ADD_MONTHS(SYSDATE, 1)              -- 加月
LAST_DAY(SYSDATE)                   -- 月末

-- NULL
NVL(col, '默认值')
NVL2(col, '有值', '无值')
COALESCE(a, b, c)

-- 条件
CASE WHEN x>1 THEN 'a' ELSE 'b' END
DECODE(status, 1, '活跃', 0, '停用', '未知')
```

## 常用查询

```sql
-- 系统信息
SELECT * FROM V$VERSION;           -- 版本
SELECT STATUS FROM V$INSTANCE;     -- 状态
SELECT USER;                       -- 当前用户

-- 表信息
DESC table_name;                   -- 表结构
SELECT TABLE_NAME FROM USER_TABLES;  -- 我的表
SELECT * FROM USER_TAB_COLUMNS WHERE TABLE_NAME='表名';

-- 序列
CREATE SEQUENCE seq_name START WITH 1 INCREMENT BY 1;
SELECT seq_name.NEXTVAL;           -- 下一个值
SELECT seq_name.CURRVAL;           -- 当前值
```

## 分页

```sql
-- LIMIT方式（推荐）
SELECT * FROM t ORDER BY id LIMIT 10 OFFSET 20;

-- ROWNUM方式
SELECT * FROM (SELECT *, ROWNUM rn FROM t WHERE ROWNUM<=30) WHERE rn>20;
```

## 存储过程

```sql
CREATE OR REPLACE PROCEDURE proc_name(p_id INT, p_out OUT VARCHAR)
AS
BEGIN
    SELECT name INTO p_out FROM t WHERE id = p_id;
EXCEPTION
    WHEN NO_DATA_FOUND THEN p_out := NULL;
END;

-- 调用
CALL proc_name(1, v_result);
```

## 函数

```sql
CREATE OR REPLACE FUNCTION func_name(p_id INT)
RETURNS VARCHAR AS
BEGIN
    RETURN 'result';
END;

SELECT func_name(1) FROM DUAL;
```

## 触发器

```sql
CREATE OR REPLACE TRIGGER trg_name
BEFORE INSERT ON t FOR EACH ROW
BEGIN
    :NEW.id := seq_name.NEXTVAL;
END;
```

## 用户权限

```sql
CREATE USER user_name IDENTIFIED BY "password";
GRANT CONNECT TO user_name;
GRANT SELECT ON table_name TO user_name;
REVOKE SELECT ON table_name FROM user_name;
```

## 与Oracle差异对比

| 功能 | Oracle | 达梦 | MySQL |
|------|--------|------|-------|
| 分页 | ROWNUM | LIMIT/ROWNUM | LIMIT |
| 序列 | SEQ.NEXTVAL | 同Oracle | AUTO_INCREMENT |
| NULL | NVL() | NVL() | IFNULL() |
| 连接 | \|\| | \|\|/CONCAT() | CONCAT() |

## 常见问题

1. **大小写敏感**：创建时用引号，查询也要用
2. **中文乱码**：确保编码一致（UTF-8/GB18030）
3. **连接失败**：检查端口5236和防火墙
4. **锁等待**：`SELECT * FROM V$LOCKED_OBJECTS`