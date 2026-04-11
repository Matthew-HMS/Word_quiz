from __future__ import annotations

import io

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse


router = APIRouter(prefix="/api/tts", tags=["tts"])


@router.get("")
def tts(text: str):
    # Optional: keep this simple. For production, add caching + rate limiting.
    if not text or len(text) > 64:
        raise HTTPException(status_code=400, detail="Invalid text")

    try:
        from gtts import gTTS

        buf = io.BytesIO()
        tts_obj = gTTS(text=text, lang="en")
        tts_obj.write_to_fp(buf)
        buf.seek(0)
        return StreamingResponse(buf, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {e}")
