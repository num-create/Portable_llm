# PortableLLM - 便携式本地AI助手

一款无需安装、拷贝即用的本地大语言模型聊天工具。支持知识库问答，适合U盘携带、无网络环境使用。

## 特性

- **零依赖**：无需安装 Python 或任何依赖包
- **便携使用**：解压后直接运行，可放U盘随身携带
- **离线运行**：完全本地化，无需联网
- **知识库支持**：放入专业文档，AI可基于知识库回答
- **多行输入**：支持粘贴多行文本内容
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

双击 `PortableLLM.exe`，选择模型即可开始对话。

## 目录结构

```
PortableLLM/
├── PortableLLM.exe      # 主程序
├── config.json          # 配置文件
├── models/              # 存放 .gguf 模型文件
│   └── your-model.gguf
├── kb/                  # 知识库目录
│   ├── sql_basics.md
│   └── dameng_database.md
└── _internal/           # 程序依赖（勿修改）
    ├── llama-server.exe
    └── ...
```

## 知识库使用

将 `.txt` 或 `.md` 文件放入 `kb/` 目录，AI会在回答时参考这些文档。

### 知识库命令

在聊天中输入 `/kb` 相关命令：

| 命令 | 说明 |
|------|------|
| `/kb` | 列出所有知识库文件及状态 |
| `/kb on <文件名>` | 启用指定知识库 |
| `/kb off <文件名>` | 禁用指定知识库 |
| `/kb all` | 启用所有知识库 |
| `/kb none` | 禁用所有知识库 |
| `/kb reload` | 重新扫描 kb 目录 |

### 示例

```
You: /kb
  KB Files:
    [ON] sql_basics.md
    [OFF] dameng_database.md

You: /kb on dameng_database.md
  Enabled: dameng_database.md

You: 达梦数据库怎么查看表结构？
Assistant: 根据知识库，可以使用 DESC 表名 或查询 USER_TAB_COLUMNS...
```

## 聊天命令

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助信息 |
| `/quit` 或 `/exit` | 退出程序 |
| `/reset` | 清空对话历史 |
| `/config` | 显示当前配置 |
| `"""` | 多行输入模式（以 `"""` 开始和结束） |

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
    "model_path": "",           // 默认模型文件名（空则手动选择）
    "n_ctx": 2048,              // 上下文长度
    "max_tokens": 512,          // 最大回复长度
    "temperature": 0.7,         // 创造性（0-1，越高越随机）
    "top_p": 0.9,               // 采样范围
    "repeat_penalty": 1.1,      // 重复惩罚
    "system_prompt": "You are a helpful assistant.",  // 系统提示词
    "n_threads": 0,             // CPU线程数（0=自动）
    "n_gpu_layers": 0,          // GPU层数（0=纯CPU）
    "max_history_messages": 16  // 历史消息保留数
}
```

### 参数说明

| 参数 | 说明 | 建议 |
|------|------|------|
| `n_ctx` | 上下文窗口大小 | 大模型需更大值，但占用更多内存 |
| `temperature` | 回复随机性 | 问答用0.3-0.5，创意用0.7-0.9 |
| `n_threads` | CPU线程 | 设为CPU核心数的一半较佳 |
| `n_gpu_layers` | GPU加速层数 | 设为-1全部用GPU，0纯CPU |

## GPU 加速（实验性）

如果你的电脑有 NVIDIA GPU 并安装了 CUDA：

1. 下载 GPU 版本的 llama.cpp（含 `cuBLAS` 支持）
2. 替换 `_internal/` 中的 `llama-server.exe` 和相关 DLL
3. 在 `config.json` 中设置 `n_gpu_layers`：
   - `-1`：全部层使用 GPU
   - `0`：纯 CPU 模式（默认）
   - `正数`：指定层数使用 GPU

注意：GPU 版本需要额外的 CUDA DLL 文件。

## 自行构建

### 环境要求

- Python 3.10+
- PyInstaller

### 构建步骤

```bash
# 1. 安装 PyInstaller
pip install PyInstaller

# 2. 运行构建脚本
python build.bat

# 或手动构建
pyinstaller --onedir --name PortableLLM scripts/chat.py
```

构建产物位于 `dist/PortableLLM/`。

## 常见问题

### Q: 启动时提示 "Server startup timed out"

**原因**：模型加载时间过长（U盘读取慢或模型太大）。

**解决**：
- 使用更小的模型（如 1.5B）
- 将程序复制到硬盘而非U盘运行
- 程序已设置 180秒超时，耐心等待

### Q: 提示 "No models found"

**原因**：`models/` 目录没有 `.gguf` 文件。

**解决**：下载模型文件放入 `models/` 目录。

### Q: 回复速度很慢

**原因**：纯CPU运行，大模型计算量大。

**解决**：
- 使用更小的模型
- 增加 `n_threads` 线程数
- 尝试 GPU 加速

### Q: 中文回复质量差

**原因**：使用了英文模型或模型太小。

**解决**：使用 Qwen 等中文优化模型。

### Q: 如何添加自定义知识库？

直接将 `.txt` 或 `.md` 文件放入 `kb/` 目录即可。

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