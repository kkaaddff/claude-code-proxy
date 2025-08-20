"""
透明代理 API 路由
处理代理请求和格式转换
"""

from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional, Dict, Any
import json
from urllib.parse import urlparse, parse_qs

from app.core.detector import APIFormatDetector
from app.core.constants import APIFormat
from app.core.config import config
from app.core.logging import logger
from app.clients.http_client import http_client
from app.converters.openai_to_anthropic import OpenAIToAnthropicConverter
from app.converters.anthropic_to_openai import AnthropicToOpenAIConverter
from app.converters.response_converter import ResponseConverter

router = APIRouter()

@router.api_route("/{path:path}", methods=["POST"])
async def proxy_request(
    path: str,
    request: Request,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None)
):
    """
    透明代理请求处理
    
    支持的 URL 格式:
    - /proxy/v1/chat/completions?target_baseurl=https://api.anthropic.com/v1
    - /proxy/v1/messages?target_baseurl=https://api.openai.com/v1
    """
    try:
        # 获取请求数据
        request_data = await request.json()
        query_params = dict(request.query_params)
        
        # 获取目标 URL
        target_baseurl = query_params.get("target_baseurl")
        if not target_baseurl:
            raise HTTPException(
                status_code=400, 
                detail="缺少 target_baseurl 参数。请在 URL 中指定目标 API 地址。"
            )
        
        # 提取 API 密钥
        client_api_key = None
        if authorization and authorization.startswith("Bearer "):
            client_api_key = authorization.replace("Bearer ", "")
        elif x_api_key:
            client_api_key = x_api_key
        
        # 获取合适的 API 密钥
        api_key = config.get_api_key_for_target(target_baseurl, client_api_key)
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="缺少 API 密钥。请在请求头中提供有效的 API 密钥。"
            )
        
        # 检测请求和目标格式
        source_format = APIFormatDetector.detect_request_format(request_data, path)
        target_format = APIFormatDetector.detect_target_format(target_baseurl)
        
        logger.info(f"代理请求: {source_format} -> {target_format}")
        logger.debug(f"目标 URL: {target_baseurl}")
        
        # 转换请求格式
        if source_format != target_format:
            if source_format == APIFormat.OPENAI and target_format == APIFormat.ANTHROPIC:
                converted_data = OpenAIToAnthropicConverter.convert_request(request_data)
                target_path = "/v1/messages"
            elif source_format == APIFormat.ANTHROPIC and target_format == APIFormat.OPENAI:
                converted_data = AnthropicToOpenAIConverter.convert_request(request_data)
                target_path = "/v1/chat/completions"
            else:
                converted_data = request_data
                target_path = f"/{path}"
        else:
            converted_data = request_data
            target_path = f"/{path}"
        
        # 构建完整的目标 URL
        target_url = f"{target_baseurl.rstrip('/')}{target_path}"
        
        # 构建请求头
        headers = http_client.build_headers(target_baseurl, api_key)
        
        # 检查是否是流式请求
        is_stream = converted_data.get("stream", False)
        
        if is_stream:
            # 处理流式请求
            return await _handle_stream_request(
                target_url, headers, converted_data, 
                source_format, target_format, request_data
            )
        else:
            # 处理普通请求
            return await _handle_normal_request(
                target_url, headers, converted_data,
                source_format, target_format, request_data
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"代理请求处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"代理请求失败: {str(e)}")

async def _handle_normal_request(
    target_url: str,
    headers: Dict[str, str],
    converted_data: Dict[str, Any],
    source_format: str,
    target_format: str,
    original_data: Dict[str, Any]
) -> JSONResponse:
    """处理普通请求"""
    
    # 发送请求到目标 API
    response_data = await http_client.send_request(
        "POST", target_url, headers, converted_data
    )
    
    # 转换响应格式
    if source_format != target_format:
        if source_format == APIFormat.OPENAI and target_format == APIFormat.ANTHROPIC:
            # 需要将 Anthropic 响应转换回 OpenAI 格式
            converted_response = ResponseConverter.convert_anthropic_to_openai_response(
                response_data, original_data.get("model", "unknown")
            )
        elif source_format == APIFormat.ANTHROPIC and target_format == APIFormat.OPENAI:
            # 需要将 OpenAI 响应转换回 Anthropic 格式
            converted_response = ResponseConverter.convert_openai_to_anthropic_response(
                response_data, original_data.get("model", "unknown")
            )
        else:
            converted_response = response_data
    else:
        converted_response = response_data
    
    return JSONResponse(content=converted_response)

async def _handle_stream_request(
    target_url: str,
    headers: Dict[str, str], 
    converted_data: Dict[str, Any],
    source_format: str,
    target_format: str,
    original_data: Dict[str, Any]
) -> StreamingResponse:
    """处理流式请求"""
    
    async def stream_generator():
        try:
            stream = http_client.send_stream_request(
                "POST", target_url, headers, converted_data
            )
            
            if source_format != target_format:
                if source_format == APIFormat.OPENAI and target_format == APIFormat.ANTHROPIC:
                    # 需要将 Anthropic 流式响应转换为 OpenAI 格式
                    async for chunk in ResponseConverter.convert_anthropic_stream_to_openai(
                        stream, original_data.get("model", "unknown")
                    ):
                        yield chunk
                elif source_format == APIFormat.ANTHROPIC and target_format == APIFormat.OPENAI:
                    # 需要将 OpenAI 流式响应转换为 Anthropic 格式
                    # 这里需要实现 OpenAI 到 Anthropic 的流式转换
                    async for line in stream:
                        # 简化处理：直接转发，实际应该做格式转换
                        yield line + "\n"
                else:
                    async for line in stream:
                        yield line + "\n"
            else:
                async for line in stream:
                    yield line + "\n"
        
        except Exception as e:
            logger.error(f"流式请求处理失败: {str(e)}")
            error_data = {
                "type": "error",
                "error": {"type": "api_error", "message": str(e)}
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@router.get("/health")
async def proxy_health():
    """代理健康检查"""
    return {
        "status": "healthy",
        "service": "透明转换代理",
        "version": "1.0.0",
        "supported_formats": ["OpenAI", "Anthropic"]
    }
