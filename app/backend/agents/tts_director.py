"""
TTS Director — LLM that transforms raw Game Master text into a structured
TTS script with speaker segmentation, mood annotations, and gender detection.

Uses a Gemini model (configurable via TTS_DIRECTOR_MODEL in .env) since
TTS output is also Gemini.  The director outputs JSON consumed by tts_service.

When NPC context is available, the director uses actual NPC names as speaker
labels.  `resolve_voices()` maps those names to persistent voices stored on
the NPC row and returns any new assignments for the caller to write back to
the database.

TODO: When adding non-Gemini TTS providers, generalise the director model
selection to support other providers via build_llm / llm_factory.
"""
import json
import logging
from collections import OrderedDict
from typing import Optional

from google import genai
from google.genai import types as genai_types

from config import settings
from agents.tts_prompts import (
    TTS_DIRECTOR_SYSTEM_PROMPT,
    format_npc_context,
    format_voice_history,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Voice history cache — recent voice assignments per player for cross-message
# consistency.  Keyed by player_id, stores last N assignment lists.
# ---------------------------------------------------------------------------
_VOICE_HISTORY_MAX = 3
_voice_history: dict[int, list[list[dict]]] = {}  # player_id → [[{speaker,voice},...], ...]

# ---------------------------------------------------------------------------
# Voice pools — mapped by gender.  The TTS service picks from these.
# ---------------------------------------------------------------------------

VOICE_POOL = {
    "female": [
        ("Kore", "firm"),
        ("Aoede", "breezy"),
        ("Sulafat", "warm"),
        ("Leda", "youthful"),
        ("Achernar", "soft"),
        ("Zephyr", "bright"),
        ("Callirrhoe", "smooth"),
        ("Gacrux", "mature"),
    ],
    "male": [
        ("Puck", "upbeat"),
        ("Algenib", "gravelly"),
        ("Fenrir", "excitable"),
        ("Orus", "firm"),
        ("Enceladus", "breathy"),
        ("Achird", "friendly"),
        ("Charon", "informative"),
        ("Zubenelgenubi", "deep"),
    ],
}


def _pick_voice(gender: str, mood: str, default_voice: str) -> str:
    """Pick the best voice from the pool based on gender and mood keywords.

    Falls back to the configured default voice for that gender.
    """
    pool = VOICE_POOL.get(gender, VOICE_POOL["male"])

    # Simple keyword matching: find a voice whose trait appears in the mood
    mood_lower = (mood or "").lower()
    for voice_name, trait in pool:
        if trait in mood_lower:
            return voice_name

    # No mood match — return the configured default
    return default_voice


def _build_genai_client() -> genai.Client:
    """Build a google-genai Client using the Gemini API key."""
    api_key = (settings.GEMINI_API_KEY or "").strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY is required for TTS")
    return genai.Client(api_key=api_key)


def get_voice_history(player_id: Optional[int]) -> list[dict]:
    """Return flattened recent voice assignments for a player."""
    if player_id is None:
        return []
    history = _voice_history.get(player_id, [])
    # Flatten + deduplicate keeping latest
    seen: OrderedDict[str, str] = OrderedDict()
    for batch in history:
        for entry in batch:
            seen[entry["speaker"]] = entry["voice"]
    return [{"speaker": s, "voice": v} for s, v in seen.items()]


def _save_voice_history(player_id: Optional[int], assignments: list[dict]) -> None:
    """Append a voice assignment batch to the player's history."""
    if player_id is None or not assignments:
        return
    if player_id not in _voice_history:
        _voice_history[player_id] = []
    _voice_history[player_id].append(assignments)
    # Keep only the most recent N batches
    _voice_history[player_id] = _voice_history[player_id][-_VOICE_HISTORY_MAX:]


def transform_for_tts(
    gm_text: str,
    npc_context: Optional[list[dict]] = None,
    player_id: Optional[int] = None,
) -> dict:
    """Call the TTS Director LLM to transform GM text into a TTS script.

    Args:
        gm_text: Raw Game Master narrative text.
        npc_context: List of NPC dicts from the DB ({name, gender, voice, npc_id}).
        player_id: Player ID for voice history lookup.

    Returns a dict with structure:
        {
            "segments": [
                {"speaker": "Narrator", "mood": "...", "text": "..."},
                {"speaker": "Merchant Gareth", "gender": "male", "mood": "...", "text": "..."},
                ...
            ]
        }
    """
    client = _build_genai_client()
    model = settings.TTS_DIRECTOR_MODEL

    logger.info(f"[TTS-DIR] Transforming {len(gm_text)} chars with {model}")
    logger.debug(f"[TTS-DIR] Input: {gm_text[:300]}")

    # Build prompt with optional NPC context and voice history
    prompt_parts = [TTS_DIRECTOR_SYSTEM_PROMPT]
    if npc_context:
        prompt_parts.append(format_npc_context(npc_context))
        logger.debug(f"[TTS-DIR] NPC context: {[n['name'] for n in npc_context]}")

    voice_hist = get_voice_history(player_id)
    if voice_hist:
        prompt_parts.append(format_voice_history(voice_hist))
        logger.debug(f"[TTS-DIR] Voice history: {voice_hist}")

    prompt_parts.append(f"\n\n---\n\nTransform this Game Master text:\n\n{gm_text}")
    full_prompt = "\n".join(prompt_parts)

    response = client.models.generate_content(
        model=model,
        contents=full_prompt,
        config=genai_types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=4096,
        ),
    )

    raw = response.text.strip()
    # Strip markdown code fences if the model wraps them
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3].strip()

    logger.debug(f"[TTS-DIR] Raw output: {raw[:500]}")

    try:
        script = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning(f"[TTS-DIR] JSON parse failed: {e}. Falling back to single narrator segment.")
        script = {
            "segments": [
                {"speaker": "Narrator", "mood": "atmospheric", "text": gm_text}
            ]
        }

    # Validate and normalise segments
    segments = script.get("segments", [])
    if not segments:
        segments = [{"speaker": "Narrator", "mood": "atmospheric", "text": gm_text}]

    for seg in segments:
        seg.setdefault("speaker", "Narrator")
        seg.setdefault("mood", "neutral")
        seg.setdefault("text", "")
        if seg["speaker"] != "Narrator":
            seg.setdefault("gender", "male")

    script["segments"] = segments

    logger.info(f"[TTS-DIR] Produced {len(segments)} segments")
    return script


def resolve_voices(
    script: dict,
    npc_context: Optional[list[dict]] = None,
    player_id: Optional[int] = None,
) -> tuple[list[dict], list[dict]]:
    """Resolve voice names for each segment.

    Voice resolution priority (highest first):
      1. NPC has a stored voice in the DB  →  use it
      2. Speaker name matches a recent voice history entry  →  reuse it
      3. Same speaker already resolved earlier in this message  →  reuse (lock)
      4. Pick from mood-based voice pool  →  new assignment

    Returns:
        (resolved_segments, new_voice_assignments)
        where new_voice_assignments is a list of {npc_id, voice} dicts for
        NPCs that had no stored voice and were auto-assigned one.  The caller
        should write these back to the database.
    """
    narrator_voice = settings.TTS_NARRATOR_VOICE
    default_female = settings.TTS_CHARACTER_VOICE_FEMALE
    default_male = settings.TTS_CHARACTER_VOICE_MALE

    # Build lookup: NPC name (lowered) → {npc_id, gender, voice}
    npc_lookup: dict[str, dict] = {}
    if npc_context:
        for npc in npc_context:
            npc_lookup[npc["name"].lower()] = npc

    # Recent voice history lookup: speaker name → voice
    hist_lookup: dict[str, str] = {}
    for h in get_voice_history(player_id):
        hist_lookup[h["speaker"].lower()] = h["voice"]

    # Per-message speaker lock: speaker name → voice
    speaker_lock: dict[str, str] = {}
    new_assignments: list[dict] = []  # [{npc_id, voice}, ...] for DB writeback

    resolved = []
    for seg in script.get("segments", []):
        seg = dict(seg)  # shallow copy
        speaker = seg["speaker"]

        if speaker == "Narrator":
            seg["voice"] = narrator_voice
        elif speaker.lower() in speaker_lock:
            # Already resolved this speaker in this message
            seg["voice"] = speaker_lock[speaker.lower()]
        else:
            gender = seg.get("gender", "male")
            default = default_female if gender == "female" else default_male
            voice = None

            # Priority 1: NPC has stored voice in DB
            npc_info = npc_lookup.get(speaker.lower())
            if npc_info and npc_info.get("voice"):
                voice = npc_info["voice"]
                logger.debug(f"[TTS-DIR] {speaker}: using stored voice '{voice}'")

            # Priority 2: Voice history from recent messages
            if not voice and speaker.lower() in hist_lookup:
                voice = hist_lookup[speaker.lower()]
                logger.debug(f"[TTS-DIR] {speaker}: using history voice '{voice}'")

            # Priority 3: Pick from mood pool
            if not voice:
                voice = _pick_voice(gender, seg.get("mood", ""), default)
                logger.debug(f"[TTS-DIR] {speaker}: picked new voice '{voice}'")

                # Auto-assign to DB if this is a known NPC without a voice
                if npc_info and not npc_info.get("voice"):
                    new_assignments.append({
                        "npc_id": npc_info["npc_id"],
                        "voice": voice,
                    })
                    logger.info(f"[TTS-DIR] Auto-assigning voice '{voice}' to NPC {speaker} (id={npc_info['npc_id']})")

            seg["voice"] = voice
            speaker_lock[speaker.lower()] = voice

        resolved.append(seg)

    # Save this message's voice assignments to history
    assignments = [
        {"speaker": s["speaker"], "voice": s["voice"]}
        for s in resolved if s["speaker"] != "Narrator"
    ]
    # Deduplicate
    seen = set()
    deduped = []
    for a in assignments:
        key = a["speaker"].lower()
        if key not in seen:
            seen.add(key)
            deduped.append(a)
    _save_voice_history(player_id, deduped)

    logger.debug(
        f"[TTS-DIR] Voice assignments (lock={speaker_lock}): "
        f"{[(s['speaker'], s['voice']) for s in resolved]}"
    )
    return resolved, new_assignments
