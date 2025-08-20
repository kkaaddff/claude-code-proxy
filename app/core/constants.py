# API 格式常量
class APIFormat:
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

# 角色常量
class Role:
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

# 内容类型常量
class ContentType:
    TEXT = "text"
    IMAGE = "image"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"

# 工具常量
class Tool:
    FUNCTION = "function"

# 停止原因常量
class StopReason:
    END_TURN = "end_turn"
    MAX_TOKENS = "max_tokens" 
    TOOL_USE = "tool_use"
    ERROR = "error"

# SSE 事件常量
class SSEEvent:
    MESSAGE_START = "message_start"
    MESSAGE_STOP = "message_stop"
    MESSAGE_DELTA = "message_delta"
    CONTENT_BLOCK_START = "content_block_start"
    CONTENT_BLOCK_STOP = "content_block_stop"
    CONTENT_BLOCK_DELTA = "content_block_delta"
    PING = "ping"

# Delta 类型常量
class DeltaType:
    TEXT = "text_delta"
    INPUT_JSON = "input_json_delta"
