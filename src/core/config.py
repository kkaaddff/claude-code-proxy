import os
import sys

# 配置类
class Config:
    def __init__(self):
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("环境变量中未找到 OPENAI_API_KEY")
        
        # 添加 Anthropic API 密钥用于客户端验证
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.anthropic_api_key:
            print("警告：未设置 ANTHROPIC_API_KEY。客户端 API 密钥验证将被禁用。")
        
        self.openai_base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.azure_api_version = os.environ.get("AZURE_API_VERSION")  # 用于 Azure OpenAI
        self.host = os.environ.get("HOST", "0.0.0.0")
        self.port = int(os.environ.get("PORT", "8082"))
        self.log_level = os.environ.get("LOG_LEVEL", "INFO")
        self.max_tokens_limit = int(os.environ.get("MAX_TOKENS_LIMIT", "4096"))
        self.min_tokens_limit = int(os.environ.get("MIN_TOKENS_LIMIT", "100"))
        
        # 连接设置
        self.request_timeout = int(os.environ.get("REQUEST_TIMEOUT", "90"))
        self.max_retries = int(os.environ.get("MAX_RETRIES", "2"))
        
        # 模型设置 - 大模型和小模型
        self.big_model = os.environ.get("BIG_MODEL", "gpt-4o")
        self.middle_model = os.environ.get("MIDDLE_MODEL", self.big_model)
        self.small_model = os.environ.get("SMALL_MODEL", "gpt-4o-mini")
        
    def validate_api_key(self):
        """中文说明"""""
        if not self.openai_api_key:
            return False
        # OpenAI API 密钥的基本格式检查
        if not self.openai_api_key.startswith('sk-'):
            return False
        return True
        
    def validate_client_api_key(self, client_api_key):
        """中文说明"""""
        # 如果环境中未设置 ANTHROPIC_API_KEY，则跳过验证
        if not self.anthropic_api_key:
            return True
            
        # 检查客户端的 API 密钥是否与预期值匹配
        return client_api_key == self.anthropic_api_key

try:
    config = Config()
    print(f" 配置已加载: API_KEY={'*' * 20}..., BASE_URL='{config.openai_base_url}'")
except Exception as e:
    print(f"=4 配置错误: {e}")
    sys.exit(1)
