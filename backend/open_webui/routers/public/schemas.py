"""
Pydantic schemas for OriAgent Public API v1.
These schemas define the public-facing request/response contracts.
They intentionally do NOT expose internal fields (e.g., local file paths, provider keys).
"""

from typing import Optional, Any, Literal, Union
from pydantic import BaseModel, Field


# ─── Common ──────────────────────────────────────────────────────────────────


class PublicError(BaseModel):
    code: str = Field(..., description="Machine-readable error code", examples=["invalid_request"])
    message: str = Field(..., description="Human-readable error message", examples=["Invalid request body"])
    type: str = Field(..., description="Error type category", examples=["bad_request"])


class PublicErrorResponse(BaseModel):
    success: bool = Field(False, description="Always false for errors")
    error: PublicError
    request_id: str = Field("", description="Unique request identifier for debugging")


class PublicSuccessResponse(BaseModel):
    success: bool = Field(True, description="Always true for successful responses")
    data: dict = Field(default_factory=dict, description="Response payload")
    request_id: str = Field("", description="Unique request identifier")


# ─── Health ──────────────────────────────────────────────────────────────────


class PublicHealthResponse(BaseModel):
    status: str = Field("ok", description="Service health status", examples=["ok"])
    service: str = Field("OriAgent Public API", description="Service name")
    version: str = Field("v1", description="API version")


# ─── Models ──────────────────────────────────────────────────────────────────


class PublicModelCapabilities(BaseModel):
    vision: bool = Field(False, description="Whether the model supports vision/image input")
    tools: bool = Field(False, description="Whether the model supports tool/function calling")
    file_upload: bool = Field(False, description="Whether the model supports file uploads in context")


class PublicModel(BaseModel):
    id: str = Field(..., description="Model identifier", examples=["qwen3.5:2b"])
    name: str = Field(..., description="Human-readable model name", examples=["Qwen 3.5 2B"])
    provider: str = Field("", description="Model provider (ollama, openai, etc.)", examples=["ollama"])
    capabilities: PublicModelCapabilities = Field(
        default_factory=PublicModelCapabilities,
        description="Model capability flags",
    )


class PublicModelListResponse(BaseModel):
    object: str = Field("list", description="Object type")
    data: list[PublicModel] = Field(default_factory=list, description="List of available models")


# ─── Tools (OpenAI-compatible function calling) ───────────────────────────────


class PublicToolFunctionDef(BaseModel):
    name: str = Field(..., description="Function name", examples=["get_order"])
    description: Optional[str] = Field(None, description="What the function does")
    parameters: Optional[dict] = Field(None, description="JSON-Schema for the function arguments")


class PublicTool(BaseModel):
    type: Literal["function"] = Field("function", description="Tool type (only 'function' supported)")
    function: PublicToolFunctionDef = Field(..., description="Function definition")


class PublicToolCallFunction(BaseModel):
    name: str = Field(..., description="Name of the function the model wants to call")
    arguments: str = Field(..., description="JSON-encoded string of arguments")


class PublicToolCall(BaseModel):
    id: str = Field(..., description="Unique tool call id", examples=["call_001"])
    type: Literal["function"] = Field("function", description="Tool call type")
    function: PublicToolCallFunction = Field(..., description="Called function and arguments")


class PublicNamedToolChoice(BaseModel):
    type: Literal["function"] = "function"
    function: PublicToolFunctionDef


# tool_choice may be a string ("auto"|"none"|"required") or a named-tool object.
PublicToolChoice = Union[str, PublicNamedToolChoice]


# ─── Chat Completion ─────────────────────────────────────────────────────────


class PublicChatMessage(BaseModel):
    role: str = Field(..., description="Message role", examples=["user", "assistant", "system", "tool"])
    content: Optional[str] = Field(None, description="Message content", examples=["Hello!"])
    # Assistant tool-call request (echoed back by the client on the next turn)
    tool_calls: Optional[list[PublicToolCall]] = Field(
        None, description="Tool calls the assistant requested (assistant messages only)"
    )
    # For role='tool' observation messages
    tool_call_id: Optional[str] = Field(
        None, description="Id of the tool call this observation answers (required for role='tool')"
    )
    name: Optional[str] = Field(None, description="Optional tool/function name for role='tool' messages")


class PublicChatCompletionMetadata(BaseModel):
    external_user_id: Optional[str] = Field(None, description="External user identifier for tracking")
    conversation_id: Optional[str] = Field(None, description="External conversation identifier")


class PublicChatCompletionRequest(BaseModel):
    mode: Optional[Literal["chat", "external_tool_calling"]] = Field(
        None,
        description=(
            "Request mode. 'chat' = plain completion (tools ignored). "
            "'external_tool_calling' = the model may emit tool_calls for the CLIENT to execute. "
            "If omitted, it is inferred from tools/tool_choice/tool-messages."
        ),
    )
    model: str = Field(..., description="Model ID to use for completion", examples=["Qwen/Qwen3.5-2B"])
    messages: list[PublicChatMessage] = Field(
        ...,
        description="List of messages in the conversation",
        min_length=1,
    )
    tools: Optional[list[PublicTool]] = Field(
        None, description="Function tools the model may call (OpenAI format). Max 32."
    )
    tool_choice: Optional[PublicToolChoice] = Field(
        None, description="'auto' | 'none' | 'required' | {type:function, function:{name}}"
    )
    stream: bool = Field(False, description="Whether to stream the response")
    temperature: Optional[float] = Field(None, description="Sampling temperature (0.0-2.0)", ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate", ge=1, le=128000)
    top_p: Optional[float] = Field(None, description="Top-p sampling parameter", ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(None, description="Frequency penalty", ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(None, description="Presence penalty", ge=-2.0, le=2.0)
    stop: Optional[list[str]] = Field(None, description="Stop sequences")
    metadata: Optional[PublicChatCompletionMetadata] = Field(None, description="Optional metadata for tracking")


class PublicUsage(BaseModel):
    prompt_tokens: int = Field(0, description="Number of prompt tokens")
    completion_tokens: int = Field(0, description="Number of completion tokens")
    total_tokens: int = Field(0, description="Total tokens used")


class PublicChatCompletionChoiceMessage(BaseModel):
    role: str = Field("assistant", description="Message role")
    content: Optional[str] = Field(None, description="Message content (null when tool_calls present)")
    tool_calls: Optional[list[PublicToolCall]] = Field(
        None, description="Tool calls the model wants the client to execute"
    )


class PublicChatCompletionChoice(BaseModel):
    index: int = Field(0, description="Choice index")
    message: PublicChatCompletionChoiceMessage = Field(..., description="Generated message")
    finish_reason: Optional[str] = Field(
        "stop", description="Reason for completion", examples=["stop", "length", "tool_calls"]
    )


class PublicChatCompletionResponse(BaseModel):
    id: str = Field(..., description="Unique completion ID", examples=["chatcmpl_xxx"])
    object: str = Field("chat.completion", description="Object type")
    created: int = Field(..., description="Unix timestamp of creation")
    model: str = Field(..., description="Model used for completion")
    choices: list[PublicChatCompletionChoice] = Field(..., description="Generated completions")
    usage: PublicUsage = Field(default_factory=PublicUsage, description="Token usage statistics")


# ─── Streaming (SSE delta format) ────────────────────────────────────────────


class PublicChatCompletionStreamDelta(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None


class PublicChatCompletionStreamChoice(BaseModel):
    index: int = 0
    delta: PublicChatCompletionStreamDelta = Field(default_factory=PublicChatCompletionStreamDelta)
    finish_reason: Optional[str] = None


class PublicChatCompletionStreamChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: list[PublicChatCompletionStreamChoice]


# ─── Files ───────────────────────────────────────────────────────────────────


class PublicFileResponse(BaseModel):
    id: str = Field(..., description="File identifier", examples=["file_xxx"])
    object: str = Field("file", description="Object type")
    filename: str = Field(..., description="Original filename", examples=["document.pdf"])
    bytes: int = Field(0, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type", examples=["application/pdf"])
    created_at: int = Field(..., description="Unix timestamp of upload")


class PublicFileDeleteResponse(BaseModel):
    success: bool = Field(True, description="Whether the deletion was successful")
    id: str = Field(..., description="Deleted file identifier")
    deleted: bool = Field(True, description="Confirmation of deletion")


# ─── Knowledge / RAG ────────────────────────────────────────────────────────


class PublicKnowledgeQueryRequest(BaseModel):
    knowledge_id: str = Field(..., description="Knowledge base identifier")
    query: str = Field(..., description="Search query text")
    top_k: int = Field(5, description="Number of results to return", ge=1, le=50)
    rerank: bool = Field(True, description="Whether to re-rank results")


class PublicKnowledgeQuerySource(BaseModel):
    file_id: Optional[str] = Field(None, description="Source file identifier")
    filename: Optional[str] = Field(None, description="Source filename")
    page: Optional[int] = Field(None, description="Source page number")


class PublicKnowledgeQueryResult(BaseModel):
    content: str = Field(..., description="Matched text content")
    score: float = Field(0.0, description="Relevance score")
    source: Optional[PublicKnowledgeQuerySource] = Field(None, description="Source information")


class PublicKnowledgeQueryResponse(BaseModel):
    object: str = Field("knowledge.query", description="Object type")
    data: list[PublicKnowledgeQueryResult] = Field(default_factory=list, description="Query results")


# ─── Audio ───────────────────────────────────────────────────────────────────


class PublicAudioTranscriptionResponse(BaseModel):
    text: str = Field(..., description="Transcribed text content")
    language: Optional[str] = Field(None, description="Detected language code", examples=["vi", "en"])


class PublicSpeechRequest(BaseModel):
    input: str = Field(
        ...,
        description="Text to synthesize",
        max_length=4096,
        examples=["Xin chào, tôi là OriAgent."],
    )
    voice: str = Field("default", description="Voice identifier")
    format: str = Field("mp3", description="Output audio format", examples=["mp3"])


# ─── Images ──────────────────────────────────────────────────────────────────


class PublicImageGenerationRequest(BaseModel):
    model: Optional[str] = Field(None, description="Image generation model")
    prompt: str = Field(..., description="Image generation prompt", max_length=4000)
    size: str = Field("1024x1024", description="Image dimensions", examples=["1024x1024", "512x512"])
    n: int = Field(1, description="Number of images to generate", ge=1, le=4)


class PublicImageData(BaseModel):
    url: str = Field(..., description="Generated image URL")


class PublicImageGenerationResponse(BaseModel):
    created: int = Field(..., description="Unix timestamp of generation")
    data: list[PublicImageData] = Field(default_factory=list, description="Generated images")


# ─── Internal ReAct Agent (/agents/run) ───────────────────────────────────────


class PublicAgentRunRequest(BaseModel):
    mode: Literal["internal_react"] = Field(
        "internal_react", description="Always 'internal_react' for this endpoint."
    )
    model: str = Field(..., description="Model ID to use", examples=["Qwen/Qwen3.5-2B"])
    messages: list[PublicChatMessage] = Field(
        ..., description="Conversation so far (usually a single user message).", min_length=1
    )
    allowed_tools: list[str] = Field(
        default_factory=list,
        description="Names of INTERNAL tools the agent is allowed to use this run.",
        examples=[["get_time", "echo"]],
    )
    temperature: Optional[float] = Field(None, description="Sampling temperature", ge=0.0, le=2.0)
    max_steps: int = Field(5, description="Max ReAct iterations before forced stop", ge=1, le=8)
    max_tokens: Optional[int] = Field(None, description="Max tokens per model call", ge=1, le=128000)
    enable_intent_router: bool = Field(
        True,
        description=(
            "When true (default), a deterministic pre-pass classifies the request and "
            "may disable tools for general-knowledge questions and inject category guidance."
        ),
    )


class PublicAgentToolTraceItem(BaseModel):
    tool_name: str = Field(..., description="Internal tool that was executed")
    arguments: dict = Field(default_factory=dict, description="Arguments passed to the tool")
    status: str = Field(..., description="Execution status", examples=["success", "error"])


class PublicAgentRunResponse(BaseModel):
    answer: str = Field(..., description="Final answer (no Thought / reasoning exposed)")
    tool_trace: list[PublicAgentToolTraceItem] = Field(
        default_factory=list, description="Safe trace of internal tool executions"
    )
    steps: int = Field(0, description="Number of ReAct iterations performed")
    finish_reason: str = Field("stop", description="'stop' or 'max_steps'", examples=["stop", "max_steps"])
    intent: Optional[str] = Field(
        None,
        description="Detected intent category from the router",
        examples=["general_qa", "data_query", "policy_query", "mixed", "tool_task"],
    )
