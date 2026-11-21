"""Türkçe VLM istemleri ve hazır sorular (plan 4.6)."""

from __future__ import annotations

from collections.abc import Iterable

from services.labels import DIRECTION_TR

SYSTEM_PROMPT = (
    "Görme engelli bir kişiye Türkçe, tek cümle, en fazla 15 kelimeyle cevap ver. "
    "Emin değilsen 'Emin değilim' de."
)

# Güvenlik kararı modele bırakılmaz: "Karşıya geçmek güvenli mi?" yok.
PRESET_QUESTIONS: dict[str, str] = {
    "whats_ahead": "Önümde ne var?",
    "crosswalk": "Yaya geçidi var mı?",
    "nearest_obstacle": "En yakın engel nerede?",
    "stairs": "Merdiven var mı?",
    "people": "Etrafımda insan var mı?",
    "read_text": "Bu yazı ne diyor?",
}

FALLBACK_ANSWER = "Emin değilim."


def summarize_objects(objects: Iterable[tuple[str, str, float | None]]) -> str:
    """(Türkçe ad, bölge, mesafe) üçlülerini tek satırlık özete çevirir."""
    parts = []
    for name_tr, region, distance_m in objects:
        text = f"{name_tr} {DIRECTION_TR.get(region, 'önde')}"
        if distance_m is not None:
            text += f" yaklaşık {round(distance_m)} metre"
        parts.append(text)
    return ", ".join(parts) if parts else "algılanan nesne yok"


def user_text(question: str, summary: str) -> str:
    return f"Soru: {question.strip()}\nKarede algılanan nesneler: {summary}."
