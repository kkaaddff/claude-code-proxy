# Claude代码代理

一个代理服务器，使**Claude代码**能够与OpenAI兼容的API提供商配合使用。 将Claude API请求转换为OpenAI API调用，允许您通过Claude代码CLI使用各种LLM提供商。

![Claude Code Proxy](demo.png)

## 功能特性

- **完整的Claude API兼容性**: Complete `/v1/messages` endpoint support
- **多提供商支持**: OpenAI、Azure OpenAI、本地模型（Ollama）以及任何OpenAI兼容的API
- **智能模型映射**: 通过环境变量配置大模型和小模型
- **函数调用**: 完整的工具使用支持和正确的转换
- **流式响应**: 实时SSE流式支持
- **图像支持**: Base64编码的图像输入
- **错误处理**: 全面的错误处理和日志记录

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

```bash
cp .env.example .env
# 编辑.env并添加您的API配置
```

### 3. 启动服务器

```bash
source .env
python start_proxy.py
```

### 4. 与Claude代码一起使用

```bash
# 如果代理中未设置ANTHROPIC_API_KEY：
ANTHROPIC_BASE_URL=http://localhost:8082 ANTHROPIC_API_KEY="any-value" claude

# 如果代理中设置了ANTHROPIC_API_KEY：
ANTHROPIC_BASE_URL=http://localhost:8082 ANTHROPIC_API_KEY="exact-matching-key" claude
```

## 配置

### 环境变量

**必需：**

- `OPENAI_API_KEY` - 目标提供商的API密钥

**安全性：**

- `ANTHROPIC_API_KEY` - 预期的Anthropic API密钥用于客户端验证
  - 如果设置，客户端必须提供此确切的API密钥来访问代理
  - 如果未设置，任何API密钥都将被接受

**模型配置：**

- `BIG_MODEL` - 用于Claude opus请求的模型 (默认： `gpt-4o`)
- `MIDDLE_MODEL` - 用于Claude opus请求的模型 (默认： `gpt-4o`)
- `SMALL_MODEL` - 用于Claude haiku请求的模型 (默认： `gpt-4o-mini`)

**API配置：**

- `OPENAI_BASE_URL` - API基础URL (默认： `https://api.openai.com/v1`)

**服务器设置：**

- `HOST` - 服务器主机 (默认： `0.0.0.0`)
- `PORT` - 服务器端口 (默认： `8082`)
- `LOG_LEVEL` - 日志级别 (默认： `WARNING`)

**性能：**

- `MAX_TOKENS_LIMIT` - Token限制 (默认： `4096`)
- `REQUEST_TIMEOUT` - 请求超时时间（秒） (默认： `90`)

### 模型映射

代理将Claude模型请求映射到您配置的模型：

| Claude请求                 | 映射到     | 环境变量   |
| ------------------------------ | ------------- | ---------------------- |
| 包含"haiku"的模型            | `SMALL_MODEL` | 默认： `gpt-4o-mini` |
| 包含"sonnet"的模型           | `MIDDLE_MODEL`| 默认： `BIG_MODEL`   |
| 包含"opus"的模型             | `BIG_MODEL`   | 默认： `gpt-4o`      |

### 提供商示例

#### OpenAI

```bash
OPENAI_API_KEY="sk-your-openai-key"
OPENAI_BASE_URL="https://api.openai.com/v1"
BIG_MODEL="gpt-4o"
MIDDLE_MODEL="gpt-4o"
SMALL_MODEL="gpt-4o-mini"
```

#### Azure OpenAI

```bash
OPENAI_API_KEY="your-azure-key"
OPENAI_BASE_URL="https://your-resource.openai.azure.com/openai/deployments/your-deployment"
BIG_MODEL="gpt-4"
MIDDLE_MODEL="gpt-4"
SMALL_MODEL="gpt-35-turbo"
```

#### 本地模型（Ollama）

```bash
OPENAI_API_KEY="dummy-key"  # 必需但可以是虚拟值
OPENAI_BASE_URL="http://localhost:11434/v1"
BIG_MODEL="llama3.1:70b"
MIDDLE_MODEL="llama3.1:70b"
SMALL_MODEL="llama3.1:8b"
```

#### 其他提供商

任何OpenAI兼容的API都可以通过设置适当的`OPENAI_BASE_URL`来使用.

## 使用示例

### 基本聊天

```python
import httpx

response = httpx.post(
    "http://localhost:8082/v1/messages",
    json={
        "model": "claude-3-5-sonnet-20241022",  # Maps to MIDDLE_MODEL
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": "Hello!"}
        ]
    }
)
```

## 与Claude代码集成

此代理旨在与Claude代码CLI无缝配合：

```bash
# 启动代理
python start_proxy.py

# 使用Claude代码与代理
ANTHROPIC_BASE_URL=http://localhost:8082 claude

# 或永久设置
export ANTHROPIC_BASE_URL=http://localhost:8082
claude
```

## 测试

测试代理功能：

```bash
# 运行全面测试
python tests/test_main.py
```

## 开发

```bash
# 格式化代码
black src/
isort src/

# 类型检查
mypy src/

# 运行测试
pytest tests/test_main.py -v
```

### 项目结构

```
claude-code-proxy/
├── src/
│   ├── main.py  # 主服务器
│   ├── test_claude_to_openai.py    # 测试
│   └── [other modules...]
├── start_proxy.py                  # 启动脚本
├── .env.example                    # 配置模板
└── README.md                       # 此文件
```

## 性能

- **异步/等待**以实现高并发
- **连接池**以提高效率
- **流式支持**以实现实时响应
- **可配置的超时**和重试
- **智能错误处理**和详细日志

## 许可证

MIT许可证
