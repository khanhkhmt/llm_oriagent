"""
Pydantic schemas for OriAgent Public API v1.
These schemas define the public-facing request/response contracts.
They intentionally do NOT expose internal fields (e.g., local file paths, provider keys).
"""

from typing import Optional, Any
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
    id: str = Field(..., description="Model identifier", examples=["qwen2.5:0.5b"])
    name: str = Field(..., description="Human-readable model name", examples=["Qwen 2.5 0.5B"])
    provider: str = Field("", description="Model provider (ollama, openai, etc.)", examples=["ollama"])
    capabilities: PublicModelCapabilities = Field(
        default_factory=PublicModelCapabilities,
        description="Model capability flags",
    )


class PublicModelListResponse(BaseModel):
    object: str = Field("list", description="Object type")
    data: list[PublicModel] = Field(default_factory=list, description="List of available models")


# ─── Chat Completion ─────────────────────────────────────────────────────────


class PublicChatMessage(BaseModel):
    role: str = Field(..., description="Message role", examples=["user", "assistant", "system"])
    content: str = Field(..., description="Message content", examples=["Hello!"])


class PublicChatCompletionMetadata(BaseModel):
    external_user_id: Optional[str] = Field(None, description="External user identifier for tracking")
    conversation_id: Optional[str] = Field(None, description="External conversation identifier")


class PublicChatCompletionRequest(BaseModel):
    model: str = Field(..., description="Model ID to use for completion", examples=["qwen2.5:0.5b"])
    messages: list[PublicChatMessage] = Field(
        ...,
        description="List of messages in the conversation",
        min_length=1,
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
    content: str = Field("", description="Message content")


class PublicChatCompletionChoice(BaseModel):
    index: int = Field(0, description="Choice index")
    message: PublicChatCompletionChoiceMessage = Field(..., description="Generated message")
    finish_reason: Optional[str] = Field("stop", description="Reason for completion", examples=["stop", "length"])


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
