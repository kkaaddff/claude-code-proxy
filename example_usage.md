# 使用示例

## 启动服务

```bash
# 激活 conda 环境
conda activate mcp-atlassian

# 启动服务
python -m app.server
```

服务将在 `http://localhost:8000` 启动。

## 基本使用

### 1. 使用 OpenAI 格式调用 Anthropic API

```bash
curl -X POST "http://localhost:8000/proxy/v1/chat/completions?target_baseurl=https://api.anthropic.com/v1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-ant-your-anthropic-key" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "max_tokens": 100
  }'
```

### 2. 使用 Anthropic 格式调用 OpenAI API

```bash
curl -X POST "http://localhost:8000/proxy/v1/messages?target_baseurl=https://api.openai.com/v1" \
  -H "Content-Type: application/json" \
  -H "x-api-key: sk-your-openai-key" \
  -d '{
    "model": "claude-3-sonnet-20240229",
    "max_tokens": 100,
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ]
  }'
```

### 3. 流式响应

```bash
curl -X POST "http://localhost:8000/proxy/v1/chat/completions?target_baseurl=https://api.anthropic.com/v1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-ant-your-anthropic-key" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "Tell me a story"}
    ],
    "max_tokens": 200,
    "stream": true
  }' \
  --no-buffer
```

## CLI 工具集成

### OpenAI CLI 调用 Anthropic

```bash
# 设置环境变量
export OPENAI_BASE_URL="http://127.0.0.1:8000/proxy/v1/chat/completions?target_baseurl=https://api.anthropic.com/v1"
export OPENAI_API_KEY="sk-ant-your-anthropic-key"

# 使用 OpenAI CLI
openai api chat_completions.create \
  -m claude-3-sonnet-20240229 \
  -g "你好，请介绍一下自己"
```

### 自定义 CLI 工具

任何使用 OpenAI SDK 的工具都可以通过设置 `base_url` 来使用代理：

```python
from openai import OpenAI

# 配置客户端使用代理
client = OpenAI(
    base_url="http://127.0.0.1:8000/proxy/v1/chat/completions?target_baseurl=https://api.anthropic.com/v1",
    api_key="sk-ant-your-anthropic-key"
)

# 使用 OpenAI 接口调用 Anthropic API
response = client.chat.completions.create(
    model="claude-3-sonnet-20240229",
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    max_tokens=100
)

print(response.choices[0].message.content)
```

## 健康检查

```bash
# 检查服务状态
curl http://localhost:8000/health

# 检查代理状态
curl http://localhost:8000/proxy/health
```

## 环境变量配置

```bash
# 服务器配置
export HOST="0.0.0.0"
export PORT="8000"
export LOG_LEVEL="INFO"

# 默认 API 密钥（可选）
export OPENAI_API_KEY="sk-your-openai-key"
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-key"

# 模型映射配置
export BIG_MODEL="gpt-4o"
export MIDDLE_MODEL="gpt-4o"
export SMALL_MODEL="gpt-4o-mini"

# 启动服务
python -m app.server
```
