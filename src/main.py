from fastapi import FastAPI
from src.api.endpoints import router as api_router
import uvicorn
import sys
from src.core.config import config

app = FastAPI(title="Claude到OpenAI API代理", version="1.0.0")

app.include_router(api_router)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Claude到OpenAI API代理 v1.0.0")
        print("")
        print("Usage: python src/main.py")
        print("")
        print("必需的环境变量：")
        print("  OPENAI_API_KEY - 您的OpenAI API密钥")
        print("")
        print("可选的环境变量：")
        print("  ANTHROPIC_API_KEY - 预期的Anthropic API密钥用于客户端验证")
        print("                      如果设置，客户端必须提供此确切的API密钥")
        print(
            f"  OPENAI_BASE_URL - OpenAI API基础URL (default: https://api.openai.com/v1)"
        )
        print(f"  BIG_MODEL - 用于opus请求的模型 (default: gpt-4o)")
        print(f"  MIDDLE_MODEL - 用于sonnet请求的模型 (default: gpt-4o)")
        print(f"  SMALL_MODEL - 用于haiku请求的模型 (default: gpt-4o-mini)")
        print(f"  HOST - 服务器主机 (default: 0.0.0.0)")
        print(f"  PORT - 服务器端口 (default: 8082)")
        print(f"  LOG_LEVEL - 日志级别 (default: WARNING)")
        print(f"  MAX_TOKENS_LIMIT - Token限制 (default: 4096)")
        print(f"  MIN_TOKENS_LIMIT - 最小token限制 (default: 100)")
        print(f"  REQUEST_TIMEOUT - 请求超时时间（秒） (default: 90)")
        print("")
        print("模型映射：")
        print(f"  Claude haiku模型 -> {config.small_model}")
        print(f"  Claude sonnet/opus模型 -> {config.big_model}")
        sys.exit(0)

    # 配置摘要
    print("🚀 Claude到OpenAI API代理 v1.0.0")
    print(f"✅ 配置加载成功")
    print(f"   OpenAI Base URL: {config.openai_base_url}")
    print(f"   Big Model (opus): {config.big_model}")
    print(f"   Middle Model (sonnet): {config.middle_model}")
    print(f"   Small Model (haiku): {config.small_model}")
    print(f"   Max Tokens Limit: {config.max_tokens_limit}")
    print(f"   Request Timeout: {config.request_timeout}s")
    print(f"   Server: {config.host}:{config.port}")
    print(f"   客户端API密钥验证: {'Enabled' if config.anthropic_api_key else 'Disabled'}")
    print("")

    # 解析日志级别 - 只提取第一个单词以处理注释
    log_level = config.log_level.split()[0].lower()
    
    # 如果无效则验证并设置默认值
    valid_levels = ['debug', 'info', 'warning', 'error', 'critical']
    if log_level not in valid_levels:
        log_level = 'info'

    # 启动服务器
    uvicorn.run(
        "src.main:app",
        host=config.host,
        port=config.port,
        log_level=log_level,
        reload=False,
    )


if __name__ == "__main__":
    main()
