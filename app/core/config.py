import os

class Config:
    """服务配置类"""

    def __init__(self):
        # 服务器配置
        self.host = os.environ.get("HOST", "0.0.0.0")
        self.port = int(os.environ.get("PORT", "8000"))
        self.log_level = os.environ.get("LOG_LEVEL", "INFO")

        # 代理配置
        self.request_timeout = int(os.environ.get("REQUEST_TIMEOUT", "90"))
        self.max_retries = int(os.environ.get("MAX_RETRIES", "2"))

        # 默认 API 密钥 (可选，用于当客户端未提供时)
        self.default_openai_api_key = os.environ.get("OPENAI_API_KEY")
        self.default_anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")

        # 模型映射配置
        self.big_model = os.environ.get("BIG_MODEL", "gpt-4o")
        self.middle_model = os.environ.get("MIDDLE_MODEL", self.big_model)
        self.small_model = os.environ.get("SMALL_MODEL", "gpt-4o-mini")

        # Token 限制
        self.max_tokens_limit = int(os.environ.get("MAX_TOKENS_LIMIT", "4096"))
        self.min_tokens_limit = int(os.environ.get("MIN_TOKENS_LIMIT", "100"))


# 全局配置实例
config = Config()
