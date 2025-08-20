"""
响应格式转换器
用于转换 API 响应格式
"""

import json
import uuid
from typing import Dict, Any, AsyncGenerator
from app.core.constants import Role, ContentType, StopReason, SSEEvent, DeltaType

class ResponseConverter:
    """响应转换器"""
    
    @staticmethod
    def convert_openai_to_anthropic_response(openai_response: Dict[str, Any], original_model: str) -> Dict[str, Any]:
        """
        将 OpenAI 响应转换为 Anthropic 格式
        
        Args:
            openai_response: OpenAI 格式的响应
            original_model: 原始请求的模型名
            
        Returns:
            Anthropic 格式的响应
        """
        choices = openai_response.get("choices", [])
        if not choices:
            raise ValueError("No choices in OpenAI response")
        
        choice = choices[0]
        message = choice.get("message", {})
        
        # 构建 Claude 内容块
        content_blocks = []
        
        # 添加文本内容
        text_content = message.get("content")
        if text_content is not None:
            content_blocks.append({"type": ContentType.TEXT, "text": text_content})
        
        # 添加工具调用
        tool_calls = message.get("tool_calls", []) or []
        for tool_call in tool_calls:
            if tool_call.get("type") == "function":
                function_data = tool_call.get("function", {})
                try:
                    arguments = json.loads(function_data.get("arguments", "{}"))
                except json.JSONDecodeError:
                    arguments = {"raw_arguments": function_data.get("arguments", "")}
                
                content_blocks.append({
                    "type": ContentType.TOOL_USE,
                    "id": tool_call.get("id", f"tool_{uuid.uuid4()}"),
                    "name": function_data.get("name", ""),
                    "input": arguments
                })
        
        # 确保至少有一个内容块
        if not content_blocks:
            content_blocks.append({"type": ContentType.TEXT, "text": ""})
        
        # 映射停止原因
        finish_reason = choice.get("finish_reason", "stop")
        stop_reason = {
            "stop": StopReason.END_TURN,
            "length": StopReason.MAX_TOKENS,
            "tool_calls": StopReason.TOOL_USE,
            "function_call": StopReason.TOOL_USE,
        }.get(finish_reason, StopReason.END_TURN)
        
        # 构建 Anthropic 响应
        return {
            "id": openai_response.get("id", f"msg_{uuid.uuid4()}"),
            "type": "message",
            "role": Role.ASSISTANT,
            "model": original_model,
            "content": content_blocks,
            "stop_reason": stop_reason,
            "stop_sequence": None,
            "usage": {
                "input_tokens": openai_response.get("usage", {}).get("prompt_tokens", 0),
                "output_tokens": openai_response.get("usage", {}).get("completion_tokens", 0),
            },
        }
    
    @staticmethod
    def convert_anthropic_to_openai_response(anthropic_response: Dict[str, Any], original_model: str) -> Dict[str, Any]:
        """
        将 Anthropic 响应转换为 OpenAI 格式
        
        Args:
            anthropic_response: Anthropic 格式的响应
            original_model: 原始请求的模型名
            
        Returns:
            OpenAI 格式的响应
        """
        content_blocks = anthropic_response.get("content", [])
        
        # 提取文本内容和工具调用
        text_parts = []
        tool_calls = []
        
        for block in content_blocks:
            if block.get("type") == ContentType.TEXT:
                text_parts.append(block.get("text", ""))
            elif block.get("type") == ContentType.TOOL_USE:
                tool_calls.append({
                    "id": block.get("id", f"tool_{uuid.uuid4()}"),
                    "type": "function",
                    "function": {
                        "name": block.get("name", ""),
                        "arguments": json.dumps(block.get("input", {}), ensure_ascii=False)
                    }
                })
        
        # 构建消息内容
        content = "".join(text_parts) if text_parts else None
        
        # 映射停止原因
        stop_reason = anthropic_response.get("stop_reason", StopReason.END_TURN)
        finish_reason = {
            StopReason.END_TURN: "stop",
            StopReason.MAX_TOKENS: "length",
            StopReason.TOOL_USE: "tool_calls",
            StopReason.ERROR: "stop",
        }.get(stop_reason, "stop")
        
        # 构建 OpenAI 响应
        message = {
            "role": Role.ASSISTANT,
            "content": content
        }
        
        if tool_calls:
            message["tool_calls"] = tool_calls
        
        return {
            "id": anthropic_response.get("id", f"chatcmpl-{uuid.uuid4()}"),
            "object": "chat.completion",
            "created": int(uuid.uuid4().int >> 96),  # 简单的时间戳
            "model": original_model,
            "choices": [{
                "index": 0,
                "message": message,
                "finish_reason": finish_reason
            }],
            "usage": {
                "prompt_tokens": anthropic_response.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": anthropic_response.get("usage", {}).get("output_tokens", 0),
                "total_tokens": (
                    anthropic_response.get("usage", {}).get("input_tokens", 0) +
                    anthropic_response.get("usage", {}).get("output_tokens", 0)
                )
            }
        }
    
    @staticmethod
    async def convert_anthropic_stream_to_openai(
        anthropic_stream: AsyncGenerator[str, None], 
        original_model: str
    ) -> AsyncGenerator[str, None]:
        """
        将 Anthropic 流式响应转换为 OpenAI 格式
        
        Args:
            anthropic_stream: Anthropic 流式响应生成器
            original_model: 原始请求的模型名
            
        Yields:
            OpenAI 格式的流式响应
        """
        message_id = f"chatcmpl-{uuid.uuid4()}"
        created = int(uuid.uuid4().int >> 96)
        
        # 发送初始流式响应
        yield f"data: {json.dumps({'id': message_id, 'object': 'chat.completion.chunk', 'created': created, 'model': original_model, 'choices': [{'index': 0, 'delta': {'role': Role.ASSISTANT}, 'finish_reason': None}]})}\n\n"
        
        current_tool_calls = {}
        
        async for line in anthropic_stream:
            if line.strip():
                if line.startswith("event: "):
                    event_type = line[7:].strip()
                elif line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        
                        if data.get("type") == SSEEvent.CONTENT_BLOCK_DELTA:
                            delta = data.get("delta", {})
                            
                            if delta.get("type") == DeltaType.TEXT:
                                # 文本增量
                                chunk = {
                                    "id": message_id,
                                    "object": "chat.completion.chunk",
                                    "created": created,
                                    "model": original_model,
                                    "choices": [{
                                        "index": 0,
                                        "delta": {"content": delta.get("text", "")},
                                        "finish_reason": None
                                    }]
                                }
                                yield f"data: {json.dumps(chunk)}\n\n"
                            
                            elif delta.get("type") == DeltaType.INPUT_JSON:
                                # 工具调用参数增量
                                index = data.get("index", 0)
                                if index not in current_tool_calls:
                                    current_tool_calls[index] = {
                                        "id": f"call_{uuid.uuid4()}",
                                        "type": "function",
                                        "function": {"name": "", "arguments": ""}
                                    }
                                
                                # 更新参数
                                current_tool_calls[index]["function"]["arguments"] = delta.get("partial_json", "")
                                
                                chunk = {
                                    "id": message_id,
                                    "object": "chat.completion.chunk", 
                                    "created": created,
                                    "model": original_model,
                                    "choices": [{
                                        "index": 0,
                                        "delta": {"tool_calls": [current_tool_calls[index]]},
                                        "finish_reason": None
                                    }]
                                }
                                yield f"data: {json.dumps(chunk)}\n\n"
                        
                        elif data.get("type") == SSEEvent.CONTENT_BLOCK_START:
                            content_block = data.get("content_block", {})
                            if content_block.get("type") == ContentType.TOOL_USE:
                                # 开始工具调用
                                index = data.get("index", 0)
                                current_tool_calls[index] = {
                                    "id": content_block.get("id", f"call_{uuid.uuid4()}"),
                                    "type": "function", 
                                    "function": {
                                        "name": content_block.get("name", ""),
                                        "arguments": ""
                                    }
                                }
                        
                        elif data.get("type") == SSEEvent.MESSAGE_DELTA:
                            # 消息结束，发送最终状态
                            delta_data = data.get("delta", {})
                            stop_reason = delta_data.get("stop_reason")
                            
                            finish_reason = {
                                StopReason.END_TURN: "stop",
                                StopReason.MAX_TOKENS: "length",
                                StopReason.TOOL_USE: "tool_calls",
                            }.get(stop_reason, "stop")
                            
                            chunk = {
                                "id": message_id,
                                "object": "chat.completion.chunk",
                                "created": created,
                                "model": original_model,
                                "choices": [{
                                    "index": 0,
                                    "delta": {},
                                    "finish_reason": finish_reason
                                }]
                            }
                            yield f"data: {json.dumps(chunk)}\n\n"
                    
                    except json.JSONDecodeError:
                        continue
        
        # 发送结束标记
        yield "data: [DONE]\n\n"
