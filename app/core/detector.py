"""
API 格式检测器
用于检测请求是 OpenAI 格式还是 Anthropic 格式
"""

from typing import Dict, Any
from app.core.constants import APIFormat

class APIFormatDetector:
    """API 格式检测器"""
    
    @staticmethod
    def detect_request_format(request_data: Dict[str, Any], path: str) -> str:
        """
        检测请求格式
        
        Args:
            request_data: 请求数据
            path: 请求路径
            
        Returns:
            APIFormat.OPENAI 或 APIFormat.ANTHROPIC
        """
        # 根据路径判断
        if "/chat/completions" in path:
            return APIFormat.OPENAI
        elif "/messages" in path:
            return APIFormat.ANTHROPIC
            
        # 根据请求体特征判断
        if "max_tokens" in request_data and "system" in request_data:
            # Anthropic 格式通常有 max_tokens 和可能有 system
            return APIFormat.ANTHROPIC
        elif "messages" in request_data and "model" in request_data:
            # 两种格式都有这些字段，需要进一步判断
            if "max_tokens" in request_data:
                return APIFormat.ANTHROPIC
            else:
                return APIFormat.OPENAI
        
        # 默认返回 OpenAI 格式
        return APIFormat.OPENAI
    
    @staticmethod
    def detect_target_format(target_baseurl: str) -> str:
        """
        根据目标 URL 检测目标 API 格式
        
        Args:
            target_baseurl: 目标 API 基础 URL
            
        Returns:
            APIFormat.OPENAI 或 APIFormat.ANTHROPIC
        """
        if "anthropic.com" in target_baseurl:
            return APIFormat.ANTHROPIC
        else:
            # 默认认为是 OpenAI 兼容格式
            return APIFormat.OPENAI
