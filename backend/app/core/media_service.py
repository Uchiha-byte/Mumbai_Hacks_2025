import base64
import io
from PIL import Image
from app.core.huggingface import hf_client, MODELS


async def detect_deepfake_image(image_data: str) -> str:
    """
    Detects if an image is AI-generated or manipulated using GPT-4o vision.
    Input: Base64 data URL or raw base64 string.
    Returns: formatted analysis string.
    """
    import json
    import logging
    import base64 as b64lib
    logger = logging.getLogger(__name__)

    try:
        from openai import AsyncOpenAI
        from app.core.config import settings

        if not settings.OPENAI_API_KEY:
            return _format_gpt_image_result("SUSPECT", 0, "OpenAI API key not configured.", [])

        # Extract mime type and raw base64
        if image_data.startswith("data:"):
            header, raw_b64 = image_data.split(",", 1)
            mime = header.split(":")[1].split(";")[0]  # e.g. image/jpeg
        else:
            raw_b64 = image_data
            # Detect mime from magic bytes
            img_bytes = b64lib.b64decode(raw_b64 + "==")
            if img_bytes[:4] == b'\x89PNG':
                mime = "image/png"
            elif img_bytes[:2] == b'\xff\xd8':
                mime = "image/jpeg"
            elif img_bytes[:4] == b'RIFF':
                mime = "image/webp"
            else:
                mime = "image/jpeg"

        # GPT-4o vision: pass as base64 inline
        data_url = f"data:{mime};base64,{raw_b64}"

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url, "detail": "high"},
                        },
                        {
                            "type": "text",
                            "text": (
                                "Analyze this image for signs of AI generation, deepfake manipulation, or digital editing. "
                                "Respond ONLY with a raw JSON object (no markdown, no code blocks) with these exact fields: "
                                "verdict (FAKE, REAL, or SUSPECT), confidence (integer 0-100), "
                                "reason (one sentence string), signals (array of strings describing what you detected)."
                            ),
                        },
                    ],
                }
            ],
            max_tokens=300,
        )

        content = response.choices[0].message.content.strip()
        content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(content)

        return _format_gpt_image_result(
            data.get("verdict", "SUSPECT"),
            int(data.get("confidence", 50)),
            data.get("reason", ""),
            data.get("signals", []),
        )

    except Exception as e:
        logger.error(f"GPT-4o image detection error: {e}", exc_info=True)
        return _format_gpt_image_result("SUSPECT", 0, f"Analysis failed: {e}", [])


def _format_gpt_image_result(verdict: str, confidence: int, reason: str, signals: list) -> str:
    if verdict == "FAKE":
        result_label = "AI-Generated / Manipulated"
        risk = "High" if confidence >= 80 else "Medium"
    elif verdict == "REAL":
        result_label = "Authentic"
        risk = "Low"
    else:
        result_label = "Suspicious — Needs Review"
        risk = "Medium"

    signals_text = "\n".join(f"• {s}" for s in signals) if signals else "• No specific signals identified"

    return (
        f"**🖼️ Image Authenticity Analysis**\n\n"
        f"**Result:** {result_label}\n"
        f"**Confidence:** {confidence}%\n"
        f"**Risk Level:** {risk}\n\n"
        f"**Assessment:**\n"
        f"• {reason}\n\n"
        f"**Detected Signals:**\n"
        f"{signals_text}\n\n"
        f"**⚠️ Note:** AI-based analysis may not catch all manipulations. "
        f"For critical verification, use professional forensic tools."
    )


def _format_image_result(raw: str) -> str:
    """Format the raw HuggingFace label|score into a human-readable analysis string."""
    parts = raw.split("|")
    label = parts[0] if parts else "Unknown"
    try:
        score = float(parts[1]) if len(parts) > 1 else 0.5
    except ValueError:
        score = 0.5

    confidence_pct = int(score * 100)
    if score > 0.8:
        risk = "Low"
    elif score >= 0.5:
        risk = "Medium"
    else:
        risk = "High"

    if label.lower() in ("fake", "ai-generated", "manipulated"):
        result_label = "AI-Generated / Manipulated"
        observation = "Artifacts or inconsistencies detected by the deepfake classifier."
    elif label.lower() in ("real", "authentic"):
        result_label = "Authentic"
        observation = "No significant manipulation artifacts detected."
    else:
        result_label = label
        observation = "Classification result is inconclusive."

    return (
        f"**🖼️ Image Authenticity Analysis**\n\n"
        f"**Result:** {result_label}\n"
        f"**Confidence:** {confidence_pct}%\n"
        f"**Risk Level:** {risk}\n\n"
        f"**Visual Analysis:**\n"
        f"• {observation}\n\n"
        f"**⚠️ Note:** Free detection models have limited accuracy. "
        f"For critical verification, use professional forensic tools."
    )


async def detect_deepfake_audio(audio_data: str) -> str:
    """
    Detects if audio is a deepfake using HuggingFace model.
    Input: Base64 string of the audio.
    Returns: formatted analysis string.
    """
    try:
        if "," in audio_data:
            audio_data = audio_data.split(",")[1]

        audio_bytes = base64.b64decode(audio_data)

        async with __import__('httpx').AsyncClient() as client:
            from app.core.huggingface import MODELS
            from app.core.config import settings
            response = await client.post(
                f"https://api-inference.huggingface.co/models/{MODELS['audio_detection']}",
                headers={
                    "Authorization": f"Bearer {settings.HUGGINGFACE_API_TOKEN}",
                    "Content-Type": "application/octet-stream",
                },
                content=audio_bytes,
                timeout=30.0,
            )

        if response.status_code != 200:
            raw = "Error|0.0"
        else:
            result = response.json()
            if isinstance(result, list) and result:
                top = sorted(result, key=lambda x: x['score'], reverse=True)[0]
                raw = f"{top['label']}|{top['score']:.2f}"
            else:
                raw = "Unknown|0.5"

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Audio detection error: {e}")
        raw = "Error|0.0"

    return _format_audio_result(raw)


def _format_audio_result(raw: str) -> str:
    parts = raw.split("|")
    label = parts[0] if parts else "Unknown"
    try:
        score = float(parts[1]) if len(parts) > 1 else 0.5
    except ValueError:
        score = 0.5

    confidence_pct = int(score * 100)
    if score > 0.8:
        risk = "Low"
    elif score >= 0.5:
        risk = "Medium"
    else:
        risk = "High"

    if label.lower() in ("fake", "ai-generated", "voice-cloned", "spoof"):
        result_label = "AI-Generated / Voice-Cloned"
        observation = "Synthetic voice patterns detected by the audio classifier."
    elif label.lower() in ("real", "authentic", "genuine", "bonafide"):
        result_label = "Authentic"
        observation = "Natural voice patterns detected; no cloning artifacts found."
    else:
        result_label = label
        observation = "Classification result is inconclusive."

    return (
        f"**🎵 Audio Authenticity Analysis**\n\n"
        f"**Result:** {result_label}\n"
        f"**Confidence:** {confidence_pct}%\n"
        f"**Risk Level:** {risk}\n\n"
        f"**Audio Analysis:**\n"
        f"• {observation}\n\n"
        f"**⚠️ Note:** Free detection models have limited accuracy. "
        f"For critical voice verification, use professional audio forensics."
    )


async def detect_deepfake_video(video_data: str) -> str:
    """
    Detects if a video contains deepfakes by analyzing frames via HuggingFace.
    Input: Base64 string of the video.
    Returns: formatted analysis string.
    """
    try:
        if "," in video_data:
            video_data = video_data.split(",")[1]

        video_bytes = base64.b64decode(video_data)

        async with __import__('httpx').AsyncClient() as client:
            from app.core.huggingface import MODELS
            from app.core.config import settings
            response = await client.post(
                f"https://api-inference.huggingface.co/models/{MODELS['video_detection']}",
                headers={
                    "Authorization": f"Bearer {settings.HUGGINGFACE_API_TOKEN}",
                    "Content-Type": "application/octet-stream",
                },
                content=video_bytes,
                timeout=30.0,
            )

        if response.status_code != 200:
            raw = "Error|0.0"
        else:
            result = response.json()
            if isinstance(result, list) and result:
                top = sorted(result, key=lambda x: x['score'], reverse=True)[0]
                raw = f"{top['label']}|{top['score']:.2f}"
            else:
                raw = "Unknown|0.5"

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Video detection error: {e}")
        raw = "Error|0.0"

    return _format_video_result(raw)


def _format_video_result(raw: str) -> str:
    parts = raw.split("|")
    label = parts[0] if parts else "Unknown"
    try:
        score = float(parts[1]) if len(parts) > 1 else 0.5
    except ValueError:
        score = 0.5

    confidence_pct = int(score * 100)
    if score > 0.8:
        risk = "Low"
    elif score >= 0.5:
        risk = "Medium"
    else:
        risk = "High"

    if label.lower() in ("fake", "deepfake", "ai-generated"):
        result_label = "Deepfake / AI-Generated"
        observation = "Deepfake artifacts detected in video frames."
    elif label.lower() in ("real", "authentic"):
        result_label = "Authentic"
        observation = "No significant deepfake artifacts detected."
    else:
        result_label = label
        observation = "Classification result is inconclusive."

    return (
        f"**🎬 Video Authenticity Analysis**\n\n"
        f"**Result:** {result_label}\n"
        f"**Confidence:** {confidence_pct}%\n"
        f"**Risk Level:** {risk}\n\n"
        f"**Visual Analysis:**\n"
        f"• {observation}\n\n"
        f"**⚠️ Note:** Free detection models have limited accuracy. "
        f"For critical deepfake verification, use professional forensic analysis."
    )
