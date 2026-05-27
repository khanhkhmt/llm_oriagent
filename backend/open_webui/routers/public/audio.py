"""
Public Audio API — POST /audio/transcriptions, POST /audio/speech
Reuses existing STT/TTS engine logic from open_webui.routers.audio.
"""
import logging, os, time, uuid, tempfile
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from open_webui.routers.public.deps import PublicAPIContext, get_public_api_context
from open_webui.routers.public.rate_limit import check_rate_limit
from open_webui.routers.public.schemas import PublicAudioTranscriptionResponse, PublicSpeechRequest

log = logging.getLogger(__name__)
router = APIRouter()

MAX_AUDIO_SIZE = 25 * 1024 * 1024  # 25MB

@router.post("/audio/transcriptions", response_model=PublicAudioTranscriptionResponse,
    summary="Transcribe audio", description="Convert audio file to text using configured STT engine.")
async def public_transcribe(request: Request, file: UploadFile = File(...),
    language: Optional[str] = Form(None), ctx: PublicAPIContext = Depends(get_public_api_context)):
    await check_rate_limit(request, ctx.user_id, "audio_transcriptions", ctx.request_id)
    if not file.filename:
        raise HTTPException(status_code=400, detail="Audio file required.")
    contents = await file.read()
    if len(contents) > MAX_AUDIO_SIZE:
        raise HTTPException(status_code=413, detail="Audio file too large. Max 25MB.")
    # Write to temp file for transcription engine
    ext = os.path.splitext(file.filename)[1] or ".wav"
    tmp_dir = os.path.join(tempfile.gettempdir(), "oriagent_public_audio")
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, f"{uuid.uuid4().hex}{ext}")
    try:
        with open(tmp_path, "wb") as f:
            f.write(contents)
        # Reuse existing transcription handler
        from open_webui.routers.audio import transcription_handler
        metadata = {"language": language} if language else {}
        from open_webui.models.users import Users
        user = await Users.get_user_by_id(ctx.user_id)
        result = transcription_handler(request, tmp_path, metadata, user=user)
        text = result.get("text", "") if isinstance(result, dict) else str(result)
        log.info("Public STT: req=%s user=%s chars=%d", ctx.request_id, ctx.user_id, len(text))
        return PublicAudioTranscriptionResponse(text=text, language=language)
    except HTTPException:
        raise
    except Exception as e:
        log.error("Public STT error: req=%s error=%s", ctx.request_id, str(e))
        raise HTTPException(status_code=500, detail="Transcription failed.")
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

@router.post("/audio/speech", summary="Text to speech",
    description="Convert text to audio using configured TTS engine.")
async def public_speech(request: Request, form_data: PublicSpeechRequest,
    ctx: PublicAPIContext = Depends(get_public_api_context)):
    await check_rate_limit(request, ctx.user_id, "audio_speech", ctx.request_id)
    if not form_data.input or not form_data.input.strip():
        raise HTTPException(status_code=400, detail="Input text is required.")
    if len(form_data.input) > 4096:
        raise HTTPException(status_code=400, detail="Input text too long. Max 4096 characters.")
    # Build a mock request body matching internal speech endpoint format
    import json, hashlib
    from open_webui.models.users import Users
    user = await Users.get_user_by_id(ctx.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")
    if request.app.state.config.TTS_ENGINE == "":
        raise HTTPException(status_code=404, detail="TTS engine is not configured.")
    # Delegate to internal speech handler by constructing payload
    payload = {"input": form_data.input}
    if form_data.voice and form_data.voice != "default":
        payload["voice"] = form_data.voice
    try:
        # Import and call internal speech logic
        body_bytes = json.dumps(payload).encode("utf-8")
        name = hashlib.sha256(
            body_bytes + str(request.app.state.config.TTS_ENGINE).encode("utf-8")
            + str(request.app.state.config.TTS_MODEL).encode("utf-8")
        ).hexdigest()
        from pathlib import Path
        from open_webui.config import CACHE_DIR
        cache_dir = CACHE_DIR / "audio" / "speech"
        cache_dir.mkdir(parents=True, exist_ok=True)
        file_path = cache_dir / f"{name}.mp3"
        if file_path.is_file():
            log.info("Public TTS cache hit: req=%s", ctx.request_id)
            return FileResponse(file_path)
        # We need to call the speech endpoint's internal logic
        # Build a scope dict so we can create an internal Request
        from starlette.datastructures import Headers
        internal_request = Request(
            scope={
                "type": "http", "method": "POST", "path": "/api/v1/audio/speech",
                "query_string": b"", "headers": Headers({}).raw,
                "app": request.app, "state": request.state.__dict__,
            },
            receive=lambda: {"type": "http.request", "body": body_bytes},
        )
        internal_request._body = body_bytes
        # Import speech function
        from open_webui.routers.audio import speech as internal_speech
        # Note: speech() reads request.body() and uses request.app.state
        # We need to monkey-patch the body method
        async def mock_body():
            return body_bytes
        internal_request.body = mock_body
        internal_request.app = request.app
        response = await internal_speech(internal_request, user=user)
        log.info("Public TTS: req=%s user=%s", ctx.request_id, ctx.user_id)
        return response
    except HTTPException:
        raise
    except Exception as e:
        log.error("Public TTS error: req=%s error=%s", ctx.request_id, str(e))
        raise HTTPException(status_code=500, detail="Speech synthesis failed.")
