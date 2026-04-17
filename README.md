# PortableLLM - 便携式本地AI助手

一款无需安装、拷贝即用的本地大语言模型聊天工具。支持知识库问答，适合U盘携带、无网络环境使用。

## 特性

- **零依赖**：无需安装 Python 或任何依赖包
- **便携使用**：解压后直接运行，可放U盘随身携带
- **离线运行**：完全本地化，无需联网
- **知识库支持**：放入专业文档，AI可基于知识库回答
- **智能缓存**：知识库加载后缓存，减少IO开销
- **自动记忆**：自动保存模型选择，下次启动直接使用
- **多行输入**：支持粘贴多行文本内容
- **进度提示**：加载时显示等待时间和KB状态
- **国产兼容**：支持达梦等国产数据库知识库

## 快速开始

### 1. 获取软件

下载 `PortableLLM` 文件夹，或自行构建（见下方说明）。

### 2. 下载模型

将 `.gguf` 格式的模型文件放入 `models/` 目录。

推荐模型：
- **Qwen2.5-1.5B-Instruct** (~1GB) - 中文友好，适合入门
- **Qwen2.5-3B-Instruct** (~2GB) - 性能更好
- **Llama-3.2-1B-Instruct** (~0.7GB) - 英文模型

下载地址：[HuggingFace GGUF Models](https://huggingface.co/models?search=gguf)

### 3. 运行程序

双击 `PortableLLM.exe`，选择模型即可开始对话。选择的模型会自动保存，下次启动直接加载。

## 目录结构

```
PortableLLM/
├── PortableLLM.exe      # 主程序
├── config.json          # 配置文件（自动保存模型选择）
├── README.md            # 使用说明
├── models/              # 存放 .gguf 模型文件
│   └── your-model.gguf
├── kb/                  # 知识库目录
│   ├── sql_basics.md    # SQL基础速查
│   └── dameng_database.md  # 达梦数据库速查
└── _internal/           # 程序依赖（勿修改）
    ├── llama-server.exe
    └── ...
```

## 知识库使用

将 `.txt` 或 `.md` 文件放入 `kb/` 目录，AI会在回答时参考这些文档。

**注意**：知识库文件不宜过大（建议每个文件 <5KB，总计 <10KB），否则可能超出模型上下文限制导致错误。

### 知识库命令

| 命令 | 说明 |
|------|------|
| `/kb` | 列出所有知识库文件及状态 |
| `/kb on <文件名>` | 启用指定知识库 |
| `/kb off <文件名>` | 禁用指定知识库 |
| `/kb all` | 启用所有知识库 |
| `/kb none` | 禁用所有知识库 |
| `/kb reload` | 重新扫描 kb 目录并刷新缓存 |

### KB状态显示

提示符会显示当前启用的KB数量：

```
You:              # 无KB
You [kb:2]:       # 启用了2个KB文件
```

### 示例

```
You [kb:2]: 达梦数据库怎么查看表结构？
Assistant: 根据知识库，可以使用 DESC 表名 或查询 USER_TAB_COLUMNS...

You [kb:2]: /kb none
  All KB files disabled

You: 数据库索引是什么？   # 提示符变了，无KB状态
Assistant: 数据库索引是...
```

## 聊天命令

| 命令 | 简写 | 说明 |
|------|------|------|
| `/help` | `/h` | 显示帮助信息 |
| `/quit` 或 `/exit` | `/q` | 退出程序 |
| `/reset` | `/r` | 清空对话历史 |
| `/clear` | `/c` | 清屏（保留对话历史） |
| `/config` | | 显示当前配置 |
| `/kb` | | 知识库管理 |
| `"""` | | 多行输入模式 |

### 多行输入示例

```
You: """
请分析以下SQL的问题：
SELECT * FROM users
WHERE name LIKE '%张%'
ORDER BY id
"""
Assistant: 这个SQL使用了前导通配符...
```

## 配置说明

编辑 `config.json` 可调整参数：

```json
{
    "model_path": "",           // 默认模型文件名（自动保存）
    "n_ctx": 2048,              // 上下文长度
    "max_tokens": 512,          // 最大回复长度
    "temperature": 0.7,         // 创造性（0-1，越高越随机）
    "top_p": 0.9,               // 采样范围
    "repeat_penalty": 1.1,      // 重复惩罚
    "system_prompt": "You are a helpful assistant.",  // 系统提示词
    "n_threads": 0,             // CPU线程数（0=自动）
    "max_history_messages": 16  // 历史消息保留数
}
```

### 参数说明

| 参数 | 说明 | 建议 |
|------|------|------|
| `n_ctx` | 上下文窗口大小 | 小模型用2048，大模型可用4096+ |
| `temperature` | 回复随机性 | 问答用0.3-0.5，创意用0.7-0.9 |
| `n_threads` | CPU线程 | 设为CPU核心数的一半较佳 |
| `max_history_messages` | 历史保留数 | 太大会占用更多上下文 |

## 自行构建

### 环境要求

- Python 3.10+
- PyInstaller

### 构建步骤

```bash
# 1. 安装 PyInstaller
pip install PyInstaller

# 2. 获取 llama.cpp 二进制文件
# 从 https://github.com/ggml-org/llama.cpp/releases 下载 Windows CPU 版本
# 解压后将 llama-server.exe 和 dll 文件放入 bin/ 目录

# 3. 运行构建
build.bat

# 或手动构建
pyinstaller --onedir --name PortableLLM \
    --add-data "bin/llama-server.exe;." \
    --add-data "bin/*.dll;." \
    scripts/chat.py
```

构建产物位于 `dist/PortableLLM/`。

## 常见问题

### Q: 启动时提示 "Server startup timed out"

**原因**：模型加载时间过长（U盘读取慢或模型太大）。

**解决**：
- 使用更小的模型（如 1.5B）
- 将程序复制到硬盘而非U盘运行
- 程序已设置 180秒超时，进度条会显示等待时间

### Q: 提示 HTTP 400 Bad Request

**原因**：知识库内容太多，超出模型上下文限制。

**解决**：
- 使用 `/kb none` 禁用知识库
- 精简知识库文件内容
- 使用更大上下文的模型

### Q: 提示 "No models found"

**原因**：`models/` 目录没有 `.gguf` 文件。

**解决**：下载模型文件放入 `models/` 目录。

### Q: 回复速度很慢

**原因**：纯CPU运行，大模型计算量大。

**解决**：
- 使用更小的模型（如 1.5B）
- 增加 `n_threads` 线程数

### Q: 中文回复质量差

**原因**：使用了英文模型或模型太小。

**解决**：使用 Qwen 等中文优化模型。

### Q: 如何添加自定义知识库？

直接将 `.txt` 或 `.md` 文件放入 `kb/` 目录，然后执行 `/kb reload`。

### Q: 如何切换默认模型？

修改 `config.json` 中的 `model_path` 为空，下次启动会重新选择。

## 技术架构

- **前端**：Python 标准库（无第三方依赖）
- **后端**：llama.cpp (llama-server)
- **模型**：GGUF 格式（支持量化压缩）
- **打包**：PyInstaller 单文件夹模式

## 许可证

本项目仅供学习和个人使用。

模型文件来自各模型作者，请遵循相应许可证。

llama.cpp 遵循 MIT 许可证。

## 相关资源

- [llama.cpp](https://github.com/ggml-org/llama.cpp) - 推理引擎
- [HuggingFace GGUF](https://huggingface.co/models?search=gguf) - 模型下载
- [Qwen 模型](https://huggingface.co/Qwen) - 中文推荐模型