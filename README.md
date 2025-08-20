# 透明转换代理服务

一个支持 OpenAI ↔ Anthropic API 格式透明转换的代理服务。允许 CLI 工具通过统一的接口访问不同的 LLM API，无需修改客户端代码。

## 功能特性

- **透明格式转换**: 自动检测并转换 OpenAI 和 Anthropic API 格式
- **流式响应支持**: 完整的 SSE 流式响应转换
- **多模态支持**: 支持文本和图像输入
- **工具调用支持**: 完整的 function calling 支持
- **错误处理**: 全面的错误处理和日志记录
- **灵活配置**: 支持环境变量配置

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 可选：设置默认 API 密钥
export OPENAI_API_KEY="sk-your-openai-key"
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-key"

# 可选：服务器配置
export HOST="0.0.0.0"
export PORT="8000"
export LOG_LEVEL="INFO"
```

### 3. 启动服务

```bash
conda activate mcp-atlassian
python -m app.server
```

### 4. 使用代理服务

#### 使用 OpenAI 格式调用 Anthropic API

```bash
curl -X POST "http://localhost:8000/proxy/v1/chat/completions?target_baseurl=https://api.anthropic.com/v1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-ant-your-anthropic-key" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "max_tokens": 100
  }'
```

#### 使用 Anthropic 格式调用 OpenAI API

```bash
curl -X POST "http://localhost:8000/proxy/v1/messages?target_baseurl=https://api.openai.com/v1" \
  -H "Content-Type: application/json" \
  -H "x-api-key: sk-your-openai-key" \
  -d '{
    "model": "claude-3-sonnet-20240229",
    "max_tokens": 100,
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

#### CLI 工具集成

配置环境变量后，CLI 工具可以透明地使用代理：

```bash
# 让 OpenAI CLI 调用 Anthropic API
export OPENAI_BASE_URL="http://127.0.0.1:8000/proxy/v1/chat/completions?target_baseurl=https://api.anthropic.com/v1"
export OPENAI_API_KEY="sk-ant-your-anthropic-key"

# 现在可以直接使用 OpenAI CLI
openai api chat_completions.create -m claude-3-sonnet-20240229 -g "你好"
```

## API 端点

### 代理端点

- `POST /proxy/{api_path}?target_baseurl={target_url}` - 透明代理请求

### 服务端点

- `GET /` - 服务信息
- `GET /health` - 健康检查
- `GET /proxy/health` - 代理健康检查

## 配置

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `HOST` | `0.0.0.0` | 服务器主机 |
| `PORT` | `8000` | 服务器端口 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `REQUEST_TIMEOUT` | `90` | 请求超时时间（秒） |
| `MAX_RETRIES` | `2` | 最大重试次数 |

### API 密钥配置

| 变量名 | 说明 |
|--------|------|
| `OPENAI_API_KEY` | 默认 OpenAI API 密钥 |
| `ANTHROPIC_API_KEY` | 默认 Anthropic API 密钥 |

### 模型映射配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `BIG_MODEL` | `gpt-4o` | 大模型映射 |
| `MIDDLE_MODEL` | `gpt-4o` | 中等模型映射 |
| `SMALL_MODEL` | `gpt-4o-mini` | 小模型映射 |

## 工作原理

1. **请求接收**: 代理接收带有 `target_baseurl` 参数的请求
2. **格式检测**: 自动检测请求格式（OpenAI 或 Anthropic）
3. **目标检测**: 根据目标 URL 确定目标 API 格式
4. **格式转换**: 如果格式不匹配，自动进行转换
5. **请求转发**: 将转换后的请求发送到目标 API
6. **响应转换**: 将目标 API 的响应转换回原始格式
7. **结果返回**: 返回转换后的响应给客户端

## 支持的转换

### 请求格式转换

- OpenAI → Anthropic
  - `messages` 数组处理
  - `system` 消息提取
  - `tools` 和 `tool_choice` 转换
  - 多模态内容转换

- Anthropic → OpenAI
  - `system` 消息合并到 `messages`
  - `max_tokens` 参数处理
  - 工具结果消息转换

### 响应格式转换

- 消息内容转换
- 工具调用格式转换
- 停止原因映射
- 使用统计转换

### 流式响应转换

- SSE 事件格式转换
- 增量内容转换
- 工具调用流式处理

## 错误处理

代理服务提供详细的错误信息和分类：

- **400**: 请求参数错误
- **401**: 认证失败
- **403**: 权限不足
- **404**: 资源未找到
- **429**: 请求过于频繁
- **500**: 内部服务器错误
- **502**: 目标服务器错误
- **503**: 服务不可用

## 开发

### 项目结构

```
app/
├── __init__.py
├── __main__.py          # 应用入口点
├── server.py            # 服务器配置
├── api/                 # API 路由
│   ├── __init__.py
│   └── proxy.py         # 代理路由
├── clients/             # HTTP 客户端
│   ├── __init__.py
│   └── http_client.py   # 异步 HTTP 客户端
├── converters/          # 格式转换器
│   ├── __init__.py
│   ├── openai_to_anthropic.py
│   ├── anthropic_to_openai.py
│   └── response_converter.py
└── core/                # 核心模块
    ├── __init__.py
    ├── config.py        # 配置管理
    ├── constants.py     # 常量定义
    ├── detector.py      # 格式检测器
    ├── logging.py       # 日志配置
    └── model_manager.py # 模型映射管理
```

### 运行测试

```bash
# 安装开发依赖
pip install -r requirements.txt

# 运行代码格式化
black app/
isort app/

# 类型检查
mypy app/
```

## 许可证

MIT 许可证