好的 👍 我来帮你分两步走：

1. 先写一个 **设计文档**，描述透明转换代理的需求、架构和设计。
2. 再给出一个 **Python 实现**（用 FastAPI/Flask + requests/httpx）。

---

# 设计文档：OpenAI ↔ Anthropic API 透明转换代理

## 一、背景与目标

* **背景**
  当前 LLM 生态中，存在不同的 API 风格：

  * **OpenAI 风格**：`/v1/chat/completions`，参数为 `messages`, `model`, `temperature`, `stream` 等。
  * **Anthropic 风格**：`/v1/messages`，参数为 `messages`, `max_tokens`, `system`, `temperature`, `stream` 等。

  开发者常常需要在两者之间切换，或者使用只支持 OpenAI SDK 的 CLI 工具调用 Anthropic 模型（或反之）。

* **目标**
  设计一个 **透明代理服务**：

  * CLI 工具只需设置：

    ```bash
    export OPENAI_BASE_URL="http://127.0.0.1:8000/proxy?target_baseurl=https://api.anthropic.com"
    export OPENAI_API_KEY="sk-xxx"
    ```
  * CLI 工具请求时：

    * 请求发送到代理。
    * 代理将请求翻译为目标 API 风格。
    * 将结果返回给 CLI，保证 CLI 认为自己在用 OpenAI API。

---

## 二、架构设计

### 1. 请求流转

```
CLI (OpenAI SDK风格)
   ↓
Transparent Proxy (转换代理)
   ↓
Target API (OpenAI或Anthropic)
   ↓
Transparent Proxy (结果转换)
   ↓
CLI
```

### 2. 功能点

1. **Base URL 转发**

   * 代理服务监听 `/proxy/*`。
   * CLI 请求中带 query 参数：`target_baseurl=https://api.anthropic.com/v1/messages`。
   * 代理解析出目标地址，转发。

2. **API Key 转发**

   * CLI 使用统一的 `OPENAI_API_KEY`。
   * 代理在请求头中加上 `x-api-key`（Anthropic）或 `Authorization: Bearer`（OpenAI）。

3. **请求体转换**

   * OpenAI → Anthropic：

     ```json
     {
       "model": "claude-3-opus-20240229",
       "messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}],
       "max_tokens": 2000,
       "temperature": 0.7
     }
     ```

     转换为：

     ```json
     {
       "model": "claude-3-opus-20240229",
       "system": "...",
       "messages": [{"role": "user", "content": "..."}],
       "max_tokens": 2000,
       "temperature": 0.7
     }
     ```
   * Anthropic → OpenAI：类似逆向转换。

4. **流式响应（SSE）**

   * 代理必须支持 SSE 转发，将目标 API 的 `event: delta` 转换为 OpenAI 的 `event: delta`。

---

## 三、模块划分

* `main.py`：代理入口，FastAPI 服务。
* `router.py`：请求路由，处理 `/proxy/*`。
* `translators.py`：请求体与响应体转换器（OpenAI ↔ Anthropic）。
* `auth.py`：API Key 管理与请求头组装。
* `client.py`：下游请求（httpx）。

---

## 四、使用方式

CLI 环境配置：

```bash
export OPENAI_BASE_URL="http://127.0.0.1:8000/proxy?target_baseurl=https://api.anthropic.com/v1"
export OPENAI_API_KEY="sk-anthropic-xxx"
```

调用 CLI：

```bash
openai api chat_completions.create -m claude-3-opus-20240229 -g "你好"
```

实际流程：

* CLI → Proxy (OpenAI 风格请求)
* Proxy 转换为 Anthropic 风格请求
* Anthropic 返回结果
* Proxy 转换回 OpenAI 风格返回
* CLI 正常运行

---

要不要我现在先给你写一个 **最小可运行的 FastAPI 版本**（支持 OpenAI→Anthropic 转换，非流式），然后再逐步增强？
