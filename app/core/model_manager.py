"""
模型映射管理器
处理不同 API 格式之间的模型映射
"""

from app.core.config import config

class ModelManager:
    """模型映射管理器"""
    
    def __init__(self, config_obj):
        self.config = config_obj
    
    def map_claude_to_openai_model(self, claude_model: str) -> str:
        """
        将 Claude 模型名映射到 OpenAI 模型名
        
        Args:
            claude_model: Claude 模型名
            
        Returns:
            对应的 OpenAI 模型名
        """
        # 如果已经是 OpenAI 模型，直接返回
        if claude_model.startswith("gpt-") or claude_model.startswith("o1-"):
            return claude_model
        
        # 如果是其他支持的模型，直接返回
        if (claude_model.startswith("ep-") or claude_model.startswith("doubao-") or 
            claude_model.startswith("deepseek-")):
            return claude_model
        
        # 根据模型名称模式映射
        model_lower = claude_model.lower()
        if 'haiku' in model_lower:
            return self.config.small_model
        elif 'sonnet' in model_lower:
            return self.config.middle_model
        elif 'opus' in model_lower:
            return self.config.big_model
        else:
            # 对于未知模型，默认使用大模型
            return self.config.big_model
    
    def map_openai_to_claude_model(self, openai_model: str) -> str:
        """
        将 OpenAI 模型名映射到 Claude 模型名
        
        Args:
            openai_model: OpenAI 模型名
            
        Returns:
            对应的 Claude 模型名
        """
        # 如果已经是 Claude 模型，直接返回
        if openai_model.startswith("claude-"):
            return openai_model
        
        # 根据配置的模型映射回 Claude 模型
        if openai_model == self.config.small_model:
            return "claude-3-haiku-20240307"
        elif openai_model == self.config.middle_model:
            return "claude-3-5-sonnet-20241022"
        elif openai_model == self.config.big_model:
            return "claude-3-opus-20240229"
        else:
            # 对于未知模型，默认使用 sonnet
            return "claude-3-5-sonnet-20241022"

# 全局模型管理器实例
model_manager = ModelManager(config)
