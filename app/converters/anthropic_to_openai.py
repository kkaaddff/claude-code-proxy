"""
Anthropic 到 OpenAI 格式转换器
"""

import json
from typing import Dict, Any, List, Optional
from app.core.constants import Role, ContentType, Tool
from app.core.model_manager import model_manager

class AnthropicToOpenAIConverter:
    """Anthropic 到 OpenAI 格式转换器"""
    
    @staticmethod
    def convert_request(anthropic_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        将 Anthropic 请求转换为 OpenAI 格式
        
        Args:
            anthropic_request: Anthropic 格式的请求
            
        Returns:
            OpenAI 格式的请求
        """
        openai_request = {}
        
        # 转换模型
        if "model" in anthropic_request:
            openai_request["model"] = model_manager.map_claude_to_openai_model(
                anthropic_request["model"]
            )
        
        # 处理消息
        messages = []
        
        # 添加系统消息
        if "system" in anthropic_request:
            system_content = anthropic_request["system"]
            if isinstance(system_content, str):
                messages.append({"role": Role.SYSTEM, "content": system_content})
            elif isinstance(system_content, list):
                # 处理结构化系统消息
                text_parts = []
                for block in system_content:
                    if isinstance(block, dict) and block.get("type") == ContentType.TEXT:
                        text_parts.append(block.get("text", ""))
                    elif isinstance(block, str):
                        text_parts.append(block)
                if text_parts:
                    messages.append({"role": Role.SYSTEM, "content": "\n\n".join(text_parts)})
        
        # 转换 Anthropic 消息
        anthropic_messages = anthropic_request.get("messages", [])
        i = 0
        while i < len(anthropic_messages):
            msg = anthropic_messages[i]
            
            if msg.get("role") == Role.USER:
                openai_msg = AnthropicToOpenAIConverter._convert_user_message(msg)
                messages.append(openai_msg)
            elif msg.get("role") == Role.ASSISTANT:
                openai_msg = AnthropicToOpenAIConverter._convert_assistant_message(msg)
                messages.append(openai_msg)
                
                # 检查下一条消息是否包含工具结果
                if i + 1 < len(anthropic_messages):
                    next_msg = anthropic_messages[i + 1]
                    if (next_msg.get("role") == Role.USER and 
                        AnthropicToOpenAIConverter._has_tool_results(next_msg)):
                        i += 1  # 跳到工具结果消息
                        tool_messages = AnthropicToOpenAIConverter._convert_tool_results(next_msg)
                        messages.extend(tool_messages)
            
            i += 1
        
        openai_request["messages"] = messages
        
        # 转换其他参数
        if "max_tokens" in anthropic_request:
            openai_request["max_tokens"] = anthropic_request["max_tokens"]
        
        if "temperature" in anthropic_request:
            openai_request["temperature"] = anthropic_request["temperature"]
        
        if "top_p" in anthropic_request:
            openai_request["top_p"] = anthropic_request["top_p"]
        
        if "stream" in anthropic_request:
            openai_request["stream"] = anthropic_request["stream"]
        
        if "stop_sequences" in anthropic_request:
            openai_request["stop"] = anthropic_request["stop_sequences"]
        
        # 转换工具
        if "tools" in anthropic_request:
            openai_request["tools"] = AnthropicToOpenAIConverter._convert_tools(anthropic_request["tools"])
        
        if "tool_choice" in anthropic_request:
            openai_request["tool_choice"] = AnthropicToOpenAIConverter._convert_tool_choice(anthropic_request["tool_choice"])
        
        return openai_request
    
    @staticmethod
    def _convert_user_message(msg: Dict[str, Any]) -> Dict[str, Any]:
        """转换用户消息"""
        content = msg.get("content", "")
        
        if isinstance(content, str):
            return {"role": Role.USER, "content": content}
        elif isinstance(content, list):
            # 多模态内容
            openai_content = []
            for item in content:
                if item.get("type") == ContentType.TEXT:
                    openai_content.append({
                        "type": "text",
                        "text": item.get("text", "")
                    })
                elif item.get("type") == ContentType.IMAGE:
                    # 转换图像格式
                    source = item.get("source", {})
                    if source.get("type") == "base64":
                        media_type = source.get("media_type", "image/jpeg")
                        data = source.get("data", "")
                        openai_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{data}"
                            }
                        })
            
            # 如果只有一个文本内容，直接返回字符串
            if len(openai_content) == 1 and openai_content[0]["type"] == "text":
                return {"role": Role.USER, "content": openai_content[0]["text"]}
            else:
                return {"role": Role.USER, "content": openai_content}
        
        return {"role": Role.USER, "content": str(content)}
    
    @staticmethod
    def _convert_assistant_message(msg: Dict[str, Any]) -> Dict[str, Any]:
        """转换助手消息"""
        content = msg.get("content", [])
        
        text_parts = []
        tool_calls = []
        
        if isinstance(content, str):
            return {"role": Role.ASSISTANT, "content": content}
        
        for item in content:
            if item.get("type") == ContentType.TEXT:
                text_parts.append(item.get("text", ""))
            elif item.get("type") == ContentType.TOOL_USE:
                tool_calls.append({
                    "id": item.get("id", ""),
                    "type": Tool.FUNCTION,
                    Tool.FUNCTION: {
                        "name": item.get("name", ""),
                        "arguments": json.dumps(item.get("input", {}), ensure_ascii=False)
                    }
                })
        
        openai_msg = {"role": Role.ASSISTANT}
        
        # 设置内容
        if text_parts:
            openai_msg["content"] = "".join(text_parts)
        else:
            openai_msg["content"] = None
        
        # 设置工具调用
        if tool_calls:
            openai_msg["tool_calls"] = tool_calls
        
        return openai_msg
    
    @staticmethod
    def _has_tool_results(msg: Dict[str, Any]) -> bool:
        """检查消息是否包含工具结果"""
        content = msg.get("content", [])
        if isinstance(content, list):
            return any(item.get("type") == ContentType.TOOL_RESULT for item in content)
        return False
    
    @staticmethod
    def _convert_tool_results(msg: Dict[str, Any]) -> List[Dict[str, Any]]:
        """转换工具结果"""
        tool_messages = []
        content = msg.get("content", [])
        
        if isinstance(content, list):
            for item in content:
                if item.get("type") == ContentType.TOOL_RESULT:
                    tool_messages.append({
                        "role": Role.TOOL,
                        "tool_call_id": item.get("tool_use_id", ""),
                        "content": AnthropicToOpenAIConverter._parse_tool_result_content(item.get("content"))
                    })
        
        return tool_messages
    
    @staticmethod
    def _parse_tool_result_content(content) -> str:
        """解析工具结果内容"""
        if content is None:
            return "No content provided"
        
        if isinstance(content, str):
            return content
        
        if isinstance(content, list):
            result_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == ContentType.TEXT:
                    result_parts.append(item.get("text", ""))
                elif isinstance(item, str):
                    result_parts.append(item)
                elif isinstance(item, dict):
                    if "text" in item:
                        result_parts.append(item.get("text", ""))
                    else:
                        try:
                            result_parts.append(json.dumps(item, ensure_ascii=False))
                        except:
                            result_parts.append(str(item))
            return "\n".join(result_parts).strip()
        
        if isinstance(content, dict):
            if content.get("type") == ContentType.TEXT:
                return content.get("text", "")
            try:
                return json.dumps(content, ensure_ascii=False)
            except:
                return str(content)
        
        try:
            return str(content)
        except:
            return "Unparseable content"
    
    @staticmethod
    def _convert_tools(anthropic_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """转换工具定义"""
        openai_tools = []
        
        for tool in anthropic_tools:
            if tool.get("name"):
                openai_tools.append({
                    "type": Tool.FUNCTION,
                    Tool.FUNCTION: {
                        "name": tool.get("name", ""),
                        "description": tool.get("description", ""),
                        "parameters": tool.get("input_schema", {})
                    }
                })
        
        return openai_tools
    
    @staticmethod
    def _convert_tool_choice(anthropic_tool_choice: Dict[str, Any]):
        """转换工具选择"""
        choice_type = anthropic_tool_choice.get("type")
        
        if choice_type == "auto":
            return "auto"
        elif choice_type == "any":
            return "auto"  # OpenAI 没有 any 选项
        elif choice_type == "tool" and "name" in anthropic_tool_choice:
            return {
                "type": Tool.FUNCTION,
                Tool.FUNCTION: {"name": anthropic_tool_choice["name"]}
            }
        else:
            return "auto"
