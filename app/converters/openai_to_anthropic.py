"""
OpenAI 到 Anthropic 格式转换器
"""

import json
from typing import Dict, Any, List, Optional
from app.core.constants import Role, ContentType, Tool
from app.core.model_manager import model_manager

class OpenAIToAnthropicConverter:
    """OpenAI 到 Anthropic 格式转换器"""
    
    @staticmethod
    def convert_request(openai_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        将 OpenAI 请求转换为 Anthropic 格式
        
        Args:
            openai_request: OpenAI 格式的请求
            
        Returns:
            Anthropic 格式的请求
        """
        anthropic_request = {}
        
        # 转换模型
        if "model" in openai_request:
            anthropic_request["model"] = model_manager.map_openai_to_claude_model(
                openai_request["model"]
            )
        
        # 处理消息
        messages = openai_request.get("messages", [])
        system_message = None
        anthropic_messages = []
        
        for msg in messages:
            if msg.get("role") == Role.SYSTEM:
                # 提取系统消息
                system_message = msg.get("content", "")
            elif msg.get("role") == Role.USER:
                anthropic_messages.append(OpenAIToAnthropicConverter._convert_user_message(msg))
            elif msg.get("role") == Role.ASSISTANT:
                anthropic_messages.append(OpenAIToAnthropicConverter._convert_assistant_message(msg))
            elif msg.get("role") == Role.TOOL:
                # 工具响应消息需要特殊处理
                if anthropic_messages and anthropic_messages[-1].get("role") == Role.USER:
                    # 如果上一条是用户消息，添加到其内容中
                    if "content" not in anthropic_messages[-1]:
                        anthropic_messages[-1]["content"] = []
                    elif isinstance(anthropic_messages[-1]["content"], str):
                        anthropic_messages[-1]["content"] = [{"type": ContentType.TEXT, "text": anthropic_messages[-1]["content"]}]
                    
                    anthropic_messages[-1]["content"].append({
                        "type": ContentType.TOOL_RESULT,
                        "tool_use_id": msg.get("tool_call_id", ""),
                        "content": msg.get("content", "")
                    })
                else:
                    # 创建新的用户消息包含工具结果
                    anthropic_messages.append({
                        "role": Role.USER,
                        "content": [{
                            "type": ContentType.TOOL_RESULT,
                            "tool_use_id": msg.get("tool_call_id", ""),
                            "content": msg.get("content", "")
                        }]
                    })
        
        anthropic_request["messages"] = anthropic_messages
        
        # 添加系统消息
        if system_message:
            anthropic_request["system"] = system_message
        
        # 转换其他参数
        if "max_tokens" in openai_request:
            anthropic_request["max_tokens"] = openai_request["max_tokens"]
        else:
            # Anthropic 需要 max_tokens，设置默认值
            anthropic_request["max_tokens"] = 2000
        
        if "temperature" in openai_request:
            anthropic_request["temperature"] = openai_request["temperature"]
        
        if "top_p" in openai_request:
            anthropic_request["top_p"] = openai_request["top_p"]
        
        if "stream" in openai_request:
            anthropic_request["stream"] = openai_request["stream"]
        
        if "stop" in openai_request:
            anthropic_request["stop_sequences"] = openai_request["stop"]
        
        # 转换工具
        if "tools" in openai_request:
            anthropic_request["tools"] = OpenAIToAnthropicConverter._convert_tools(openai_request["tools"])
        
        if "tool_choice" in openai_request:
            anthropic_request["tool_choice"] = OpenAIToAnthropicConverter._convert_tool_choice(openai_request["tool_choice"])
        
        return anthropic_request
    
    @staticmethod
    def _convert_user_message(msg: Dict[str, Any]) -> Dict[str, Any]:
        """转换用户消息"""
        content = msg.get("content", "")
        
        if isinstance(content, str):
            return {"role": Role.USER, "content": content}
        elif isinstance(content, list):
            # 多模态内容
            anthropic_content = []
            for item in content:
                if item.get("type") == "text":
                    anthropic_content.append({
                        "type": ContentType.TEXT,
                        "text": item.get("text", "")
                    })
                elif item.get("type") == "image_url":
                    # 转换图像格式
                    image_url = item.get("image_url", {}).get("url", "")
                    if image_url.startswith("data:"):
                        # 解析 base64 图像
                        try:
                            header, data = image_url.split(",", 1)
                            media_type = header.split(":")[1].split(";")[0]
                            anthropic_content.append({
                                "type": ContentType.IMAGE,
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": data
                                }
                            })
                        except:
                            # 如果解析失败，跳过图像
                            pass
            
            return {"role": Role.USER, "content": anthropic_content}
        
        return {"role": Role.USER, "content": str(content)}
    
    @staticmethod
    def _convert_assistant_message(msg: Dict[str, Any]) -> Dict[str, Any]:
        """转换助手消息"""
        content = msg.get("content", "")
        tool_calls = msg.get("tool_calls", [])
        
        anthropic_content = []
        
        # 添加文本内容
        if content:
            anthropic_content.append({
                "type": ContentType.TEXT,
                "text": content
            })
        
        # 添加工具调用
        for tool_call in tool_calls:
            if tool_call.get("type") == Tool.FUNCTION:
                function = tool_call.get(Tool.FUNCTION, {})
                try:
                    arguments = json.loads(function.get("arguments", "{}"))
                except json.JSONDecodeError:
                    arguments = {"raw_arguments": function.get("arguments", "")}
                
                anthropic_content.append({
                    "type": ContentType.TOOL_USE,
                    "id": tool_call.get("id", ""),
                    "name": function.get("name", ""),
                    "input": arguments
                })
        
        return {"role": Role.ASSISTANT, "content": anthropic_content}
    
    @staticmethod
    def _convert_tools(openai_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """转换工具定义"""
        anthropic_tools = []
        
        for tool in openai_tools:
            if tool.get("type") == Tool.FUNCTION:
                function = tool.get(Tool.FUNCTION, {})
                anthropic_tools.append({
                    "name": function.get("name", ""),
                    "description": function.get("description", ""),
                    "input_schema": function.get("parameters", {})
                })
        
        return anthropic_tools
    
    @staticmethod
    def _convert_tool_choice(openai_tool_choice) -> Dict[str, Any]:
        """转换工具选择"""
        if openai_tool_choice == "auto":
            return {"type": "auto"}
        elif openai_tool_choice == "none":
            return {"type": "auto"}  # Anthropic 没有 none 选项
        elif isinstance(openai_tool_choice, dict):
            if openai_tool_choice.get("type") == Tool.FUNCTION:
                function = openai_tool_choice.get(Tool.FUNCTION, {})
                return {
                    "type": "tool",
                    "name": function.get("name", "")
                }
        
        return {"type": "auto"}
