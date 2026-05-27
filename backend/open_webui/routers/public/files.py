"""
Public Files API — POST /files, GET /files/{file_id}, DELETE /files/{file_id}
"""
import logging, os, time, uuid, asyncio
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from open_webui.routers.public.deps import PublicAPIContext, get_public_api_context
from open_webui.routers.public.rate_limit import check_rate_limit
from open_webui.routers.public.schemas import PublicFileResponse, PublicFileDeleteResponse
from open_webui.models.files import Files, FileForm
from open_webui.storage.provider import Storage

log = logging.getLogger(__name__)
router = APIRouter()

BLOCKED_EXT = {"exe","bat","cmd","sh","ps1","vbs","com","scr","msi","dll","php","jsp","asp","cgi","py","rb"}
MAX_FILE_SIZE = 50 * 1024 * 1024

@router.post("/files", response_model=PublicFileResponse, summary="Upload a file")
async def upload_file(request: Request, file: UploadFile = File(...),
    purpose: Optional[str] = Form(None), ctx: PublicAPIContext = Depends(get_public_api_context)):
    await check_rate_limit(request, ctx.user_id, "files", ctx.request_id)
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")
    filename = os.path.basename(file.filename)
    if ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    if ext in BLOCKED_EXT:
        raise HTTPException(status_code=400, detail=f"File type '.{ext}' is not allowed.")
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum 50MB.")
    await file.seek(0)
    file_id = str(uuid.uuid4())
    content_type = file.content_type or "application/octet-stream"
    try:
        _, file_path = await asyncio.to_thread(Storage.upload_file, file.file, f"{file_id}_{filename}",
            {"OpenWebUI-User-Id": ctx.user_id, "OpenWebUI-File-Id": file_id})
    except Exception as e:
        log.error("File upload error: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to store file.")
    await Files.insert_new_file(ctx.user_id, FileForm(id=file_id, filename=filename, path=file_path,
        data={}, meta={"name": filename, "content_type": content_type, "size": len(contents),
        "purpose": purpose or "general", "source": "public_api"}))
    log.info("Public file uploaded: req=%s user=%s file=%s", ctx.request_id, ctx.user_id, file_id)
    return PublicFileResponse(id=file_id, object="file", filename=filename,
        bytes=len(contents), mime_type=content_type, created_at=int(time.time()))

@router.get("/files/{file_id}", response_model=PublicFileResponse, summary="Get file metadata")
async def get_file_metadata(file_id: str, request: Request, ctx: PublicAPIContext = Depends(get_public_api_context)):
    f = await Files.get_file_by_id(file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found.")
    if f.user_id != ctx.user_id and ctx.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied.")
    meta = f.meta or {}
    return PublicFileResponse(id=f.id, object="file", filename=f.filename,
        bytes=meta.get("size", 0), mime_type=meta.get("content_type"), created_at=f.created_at)

@router.delete("/files/{file_id}", response_model=PublicFileDeleteResponse, summary="Delete a file")
async def delete_file(file_id: str, request: Request, ctx: PublicAPIContext = Depends(get_public_api_context)):
    f = await Files.get_file_by_id(file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found.")
    if f.user_id != ctx.user_id and ctx.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied.")
    result = await Files.delete_file_by_id(file_id)
    if not result:
        raise HTTPException(status_code=500, detail="Delete failed.")
    log.info("Public file deleted: req=%s file=%s", ctx.request_id, file_id)
    return PublicFileDeleteResponse(success=True, id=file_id, deleted=True)
