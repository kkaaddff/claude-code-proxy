#!/usr/bin/env python3
"""
透明转换代理服务器
支持 OpenAI ↔ Anthropic API 格式的透明转换
"""

import uvicorn
from fastapi import FastAPI
from app.core.config import config
from app.api.proxy import router as proxy_router
from app.core.logging import logger


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title="透明转换代理服务",
        description="OpenAI ↔ Anthropic API 透明转换代理",
        version="1.0.0",
    )

    # 注册代理路由
    app.include_router(proxy_router, prefix="/proxy")

    # 根路径端点
    @app.get("/")
    async def root():
        return {
            "service": "透明转换代理",
            "version": "1.0.0",
            "description": "OpenAI ↔ Anthropic API 透明转换代理",
            "usage": {
                "endpoints": {
                    "openai_to_anthropic": "/proxy/anthropic?target_baseurl={target_url}",
                    "anthropic_to_openai": "/proxy/openai?target_baseurl={target_url}"
                },
                "examples": {
                    "openai_to_anthropic": "/proxy/anthropic?target_baseurl=https://qa.aiapi.amh-group.com/mid-qwen/v1/messages",
                    "anthropic_to_openai": "/proxy/openai?target_baseurl=https://qa.aiapi.amh-group.com/mid-claude/v1/chat/completions"
                },
                "description": "明确的转换端点，不支持自动格式检测"
            },
            "health": "/health"
        }

    # 健康检查端点
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": "透明转换代理",
            "version": "1.0.0"
        }

    return app


def main():
    """主启动函数"""
    logger.info("🚀 启动透明转换代理服务")
    logger.info(f"   服务地址: {config.host}:{config.port}")
    logger.info(f"   日志级别: {config.log_level}")

    app = create_app()

    # 解析日志级别
    log_level = config.log_level.split()[0].lower()
    valid_levels = ['debug', 'info', 'warning', 'error', 'critical']
    if log_level not in valid_levels:
        log_level = 'info'

    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level=log_level,
        reload=False,
    )


if __name__ == "__main__":
    main()
