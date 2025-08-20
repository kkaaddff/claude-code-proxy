"""
HTTP 客户端
用于向目标 API 发送请求
"""

import asyncio
import json
from typing import Dict, Any, Optional, AsyncGenerator
import httpx
from fastapi import HTTPException
from app.core.config import config
from app.core.logging import logger

class HTTPClient:
    """异步 HTTP 客户端"""
    
    def __init__(self):
        self.timeout = httpx.Timeout(config.request_timeout)
        self.limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
    
    async def send_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        data: Dict[str, Any],
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        发送 HTTP 请求
        
        Args:
            method: HTTP 方法
            url: 目标 URL
            headers: 请求头
            data: 请求数据
            stream: 是否流式请求
            
        Returns:
            响应数据
        """
        async with httpx.AsyncClient(timeout=self.timeout, limits=self.limits) as client:
            try:
                if stream:
                    # 流式请求
                    async with client.stream(
                        method,
                        url,
                        headers=headers,
                        json=data
                    ) as response:
                        response.raise_for_status()
                        return response
                else:
                    # 普通请求
                    response = await client.request(
                        method,
                        url,
                        headers=headers,
                        json=data
                    )
                    response.raise_for_status()
                    return response.json()
            
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP 状态错误: {e.response.status_code} - {e.response.text}")
                self._handle_http_error(e.response.status_code, e.response.text)
            except httpx.RequestError as e:
                logger.error(f"请求错误: {str(e)}")
                raise HTTPException(status_code=503, detail=f"请求失败: {str(e)}")
            except Exception as e:
                logger.error(f"未知错误: {str(e)}")
                raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")
    
    async def send_stream_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        data: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """
        发送流式 HTTP 请求
        
        Args:
            method: HTTP 方法
            url: 目标 URL
            headers: 请求头
            data: 请求数据
            
        Yields:
            流式响应数据
        """
        async with httpx.AsyncClient(timeout=self.timeout, limits=self.limits) as client:
            try:
                async with client.stream(
                    method,
                    url,
                    headers=headers,
                    json=data
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.strip():
                            yield line
            
            except httpx.HTTPStatusError as e:
                logger.error(f"流式请求 HTTP 状态错误: {e.response.status_code} - {e.response.text}")
                self._handle_http_error(e.response.status_code, e.response.text)
            except httpx.RequestError as e:
                logger.error(f"流式请求错误: {str(e)}")
                raise HTTPException(status_code=503, detail=f"流式请求失败: {str(e)}")
            except Exception as e:
                logger.error(f"流式请求未知错误: {str(e)}")
                raise HTTPException(status_code=500, detail=f"流式请求内部错误: {str(e)}")
    
    def _handle_http_error(self, status_code: int, response_text: str):
        """处理 HTTP 错误"""
        try:
            error_data = json.loads(response_text)
            error_message = error_data.get("error", {}).get("message", response_text)
        except:
            error_message = response_text
        
        # 根据状态码分类错误
        if status_code == 400:
            raise HTTPException(status_code=400, detail=f"请求参数错误: {error_message}")
        elif status_code == 401:
            raise HTTPException(status_code=401, detail=f"认证失败: {error_message}")
        elif status_code == 403:
            raise HTTPException(status_code=403, detail=f"权限不足: {error_message}")
        elif status_code == 404:
            raise HTTPException(status_code=404, detail=f"资源未找到: {error_message}")
        elif status_code == 429:
            raise HTTPException(status_code=429, detail=f"请求过于频繁: {error_message}")
        elif status_code >= 500:
            raise HTTPException(status_code=502, detail=f"目标服务器错误: {error_message}")
        else:
            raise HTTPException(status_code=status_code, detail=error_message)
    
    def build_headers(self, target_baseurl: str, api_key: Optional[str] = None) -> Dict[str, str]:
        """
        构建请求头
        
        Args:
            target_baseurl: 目标 API 基础 URL
            api_key: API 密钥
            
        Returns:
            请求头字典
        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Transparent-Proxy/1.0.0"
        }
        
        if api_key:
            if "anthropic.com" in target_baseurl:
                # Anthropic API 使用 x-api-key
                headers["x-api-key"] = api_key
                headers["anthropic-version"] = "2023-06-01"
            else:
                # OpenAI 及兼容 API 使用 Authorization
                headers["Authorization"] = f"Bearer {api_key}"
        
        return headers

# 全局 HTTP 客户端实例
http_client = HTTPClient()
