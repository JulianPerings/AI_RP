"""
TTS Service — Calls Gemini TTS API to generate audio from a directed script.

Supports multi-speaker (Narrator + Character) with gender-aware voice selection.
Handles the 2-speaker limit by micro-batching segments and streaming each
batch's WAV audio to the frontend for low-latency playback.

TODO: When adding non-Gemini TTS providers, abstract this behind a common
TTS interface and add provider-specific implementations.
"""
import io
import logging
import struct
import wave
from typing import Generator, Optional

from google import genai
from google.genai import types as genai_types

from config import settings
from agents.tts_director import transform_for_tts, resolve_voices

logger = logging.getLogger(__name__)

# PCM constants for Gemini TTS output
SAMPLE_RATE = 24000
SAMPLE_WIDTH = 2  # 16-bit
CHANNELS = 1


def _build_genai_client() -> genai.Client:
    """Build a google-genai Client using the Gemini API key."""
    api_key = (settings.GEMINI_API_KEY or "").strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY is required for TTS")
    return genai.Client(api_key=api_key)


def _pcm_to_wav(pcm_data: bytes) -> bytes:
    """Wrap raw PCM bytes in a WAV header."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_data)
    return buf.getvalue()


def _build_tts_prompt(segments: list[dict]) -> str:
    """Build the text prompt for Gemini TTS from resolved segments.

    Includes mood directions as natural language cues that Gemini TTS
    uses to control style, pace, and tone.
    """
    lines = []
    for seg in segments:
        speaker = seg["speaker"]
        mood = seg.get("mood", "")
        text = seg.get("text", "")

        if mood:
            lines.append(f"Say in a {mood} tone:")
        lines.append(f"{speaker}: {text}")
        lines.append("")

    return "\n".join(lines).strip()


# Max segments per TTS batch.  Smaller batches = lower latency to first audio
# (each batch generates ~5-8s of audio in ~5-7s).
MAX_SEGMENTS_PER_BATCH = 3


def _group_into_batches(
    segments: list[dict],
    max_per_batch: int = MAX_SEGMENTS_PER_BATCH,
) -> list[list[dict]]:
    """Group segments into streaming-friendly micro-batches.

    Respects the Gemini 2-speaker-per-call limit while keeping each
    batch small so the first audio chunk arrives quickly.
    """
    narrator_voice = settings.TTS_NARRATOR_VOICE
    batches: list[list[dict]] = []
    current_batch: list[dict] = []
    current_char_voice: Optional[str] = None

    for seg in segments:
        voice = seg["voice"]
        is_narrator = voice == narrator_voice

        # Flush on character-voice change (2-speaker limit) or batch full
        need_flush = False
        if not is_narrator:
            if current_char_voice is not None and voice != current_char_voice:
                need_flush = True
        if len(current_batch) >= max_per_batch:
            need_flush = True

        if need_flush and current_batch:
            batches.append(current_batch)
            current_batch = []
            current_char_voice = None

        current_batch.append(seg)
        if not is_narrator:
            current_char_voice = voice

    if current_batch:
        batches.append(current_batch)

    return batches


def _generate_audio_for_batch(
    client: genai.Client,
    segments: list[dict],
    model: str,
) -> bytes:
    """Call Gemini TTS for a single batch of segments (max 2 speakers).

    Returns raw PCM bytes.
    """
    # Determine unique voices in this batch
    voices = {}
    for seg in segments:
        speaker = seg["speaker"]
        voice = seg["voice"]
        if speaker not in voices:
            voices[speaker] = voice

    prompt = _build_tts_prompt(segments)

    logger.debug(f"[TTS] Batch voices: {voices}")
    logger.debug(f"[TTS] Prompt ({len(prompt)} chars): {prompt[:300]}")

    # Build speech config
    if len(voices) <= 1:
        # Single speaker
        voice_name = list(voices.values())[0]
        speech_config = genai_types.SpeechConfig(
            voice_config=genai_types.VoiceConfig(
                prebuilt_voice_config=genai_types.PrebuiltVoiceConfig(
                    voice_name=voice_name,
                )
            )
        )
    else:
        # Multi-speaker (max 2)
        speaker_configs = []
        for speaker, voice_name in voices.items():
            speaker_configs.append(
                genai_types.SpeakerVoiceConfig(
                    speaker=speaker,
                    voice_config=genai_types.VoiceConfig(
                        prebuilt_voice_config=genai_types.PrebuiltVoiceConfig(
                            voice_name=voice_name,
                        )
                    ),
                )
            )
        speech_config = genai_types.SpeechConfig(
            multi_speaker_voice_config=genai_types.MultiSpeakerVoiceConfig(
                speaker_voice_configs=speaker_configs,
            )
        )

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=speech_config,
        ),
    )

    # Extract PCM data from response
    data = response.candidates[0].content.parts[0].inline_data.data
    return data


def generate_tts_stream(
    gm_text: str,
    npc_context: Optional[list[dict]] = None,
    player_id: Optional[int] = None,
    db=None,
) -> Generator[bytes, None, None]:
    """Streaming TTS pipeline — yields length-prefixed WAV chunks.

    Each yielded block is: 4-byte big-endian uint32 (length) + WAV bytes.
    The frontend reads these chunks and starts playback as soon as the
    first one arrives, giving much lower time-to-first-audio.

    Args:
        gm_text: Raw GM narrative text.
        npc_context: NPC dicts from the DB ({name, gender, voice, npc_id}).
        player_id: Player ID for voice history lookup.
        db: SQLAlchemy session for writing back auto-assigned NPC voices.

    Pipeline per chunk:
      Director LLM (once) → micro-batch → Gemini TTS → WAV → yield
    """
    logger.info(f"[TTS] Starting streaming pipeline for {len(gm_text)} chars")

    # Step 1: Director transforms GM text → script (with NPC context)
    script = transform_for_tts(gm_text, npc_context=npc_context, player_id=player_id)

    # Step 2: Resolve voice assignments (returns new assignments for DB)
    segments, new_assignments = resolve_voices(
        script, npc_context=npc_context, player_id=player_id,
    )

    if not segments:
        raise ValueError("TTS Director produced no segments")

    # Step 2b: Write back auto-assigned voices to the database
    if new_assignments and db:
        from models import NonPlayerCharacter
        for assignment in new_assignments:
            npc = db.query(NonPlayerCharacter).filter(
                NonPlayerCharacter.id == assignment["npc_id"]
            ).first()
            if npc and not npc.voice:
                npc.voice = assignment["voice"]
                logger.info(
                    f"[TTS] Saved voice '{assignment['voice']}' to NPC "
                    f"'{npc.name}' (id={npc.id})"
                )
        db.commit()

    # Step 3: Micro-batch (small batches for streaming)
    batches = _group_into_batches(segments)
    logger.info(f"[TTS] {len(segments)} segments → {len(batches)} streaming batches")

    # Step 4: Generate and stream each batch
    client = _build_genai_client()
    model = settings.TTS_MODEL

    for i, batch in enumerate(batches):
        logger.debug(f"[TTS] Generating batch {i+1}/{len(batches)} ({len(batch)} segments)")
        pcm = _generate_audio_for_batch(client, batch, model)
        wav = _pcm_to_wav(pcm)
        # Length-prefix so the frontend can parse the chunk boundary
        yield struct.pack('>I', len(wav))
        yield wav
        logger.debug(f"[TTS] Streamed batch {i+1}/{len(batches)} ({len(wav)} bytes)")


def is_tts_available() -> bool:
    """Check whether TTS can be used (Gemini API key is configured)."""
    return bool((settings.GEMINI_API_KEY or "").strip())
