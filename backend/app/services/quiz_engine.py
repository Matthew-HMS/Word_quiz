from __future__ import annotations

import random
import re
from dataclasses import dataclass


def clean_text(text: str) -> str:
    text = re.sub(r"[\r\n]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = text.split(";")[0].strip()
    return text


@dataclass
class EngineResult:
    correct: int
    wrong: int
    wrong_words_first_attempt: list[dict]

    @property
    def accuracy(self) -> float:
        total = self.correct + self.wrong
        if total == 0:
            return 0.0
        return round(self.correct / total, 2) * 100


# Session state schema stored in DB (JSON):
# {
#   "keys": [...],
#   "idx": 0,
#   "correct": 0,
#   "wrong": 0,
#   "wrong_first": {"word": "translation"},
#   "wrong_counts": {"word": 1},
#   "pending": null | {"kind": "spell_retry", "word": "..."},
#   "current": {"kind": "multiple_choice"|"spelling", ...}
# }


def init_state(mode: str, study_set: dict[str, str], keys: list[str]) -> dict:
    random.shuffle(keys)
    return {
        "mode": mode,
        "keys": keys,
        "idx": 0,
        "correct": 0,
        "wrong": 0,
        "wrong_first": {},
        "wrong_counts": {},
        "pending": None,
        "current": None,
        "set_size": len(keys),
    }


def _progress(state: dict) -> str:
    # idx is 0-based; display like (n/total)
    n = min(state["idx"] + 1, len(state["keys"]))
    total = max(len(state["keys"]), 1)
    return f"({n}/{total})"


def build_question(state: dict, study_set: dict[str, str]) -> dict:
    if state.get("pending"):
        # Frontend should call get_question only when not pending, but be safe.
        return state["pending"]

    keys: list[str] = state["keys"]
    idx: int = state["idx"]
    if idx >= len(keys):
        return {"kind": "finished"}

    word = keys[idx]
    translation = study_set[word]
    mode = state["mode"]

    if mode == "en-spelling":
        q = {
            "kind": "spelling",
            "prompt": clean_text(translation),
            "answer": word,
        }
        state["current"] = q
        return q

    if mode == "en-to-ch":
        values = list(study_set.values())
        if translation in values:
            values.remove(translation)
        if len(values) < 3:
            # not enough distractors
            q = {"kind": "skip", "reason": "not_enough_choices"}
            state["current"] = q
            return q
        distractors = random.sample(values, 3)
        choices = [translation] + distractors
        random.shuffle(choices)
        correct_index = choices.index(translation) + 1
        q = {
            "kind": "multiple_choice",
            "prompt": word,
            "choices": [clean_text(c) for c in choices],
            "correct": correct_index,
            "word": word,
            "translation": translation,
        }
        state["current"] = q
        return q

    # ch-to-en
    values = list(study_set.keys())
    if word in values:
        values.remove(word)
    if len(values) < 3:
        q = {"kind": "skip", "reason": "not_enough_choices"}
        state["current"] = q
        return q

    distractors = random.sample(values, 3)
    choices = [word] + distractors
    random.shuffle(choices)
    correct_index = choices.index(word) + 1
    q = {
        "kind": "multiple_choice",
        "prompt": clean_text(translation),
        "choices": [clean_text(c) for c in choices],
        "correct": correct_index,
        "word": word,
        "translation": translation,
    }
    state["current"] = q
    return q


def submit_answer(state: dict, study_set: dict[str, str], *, choice: int | None, text: str | None) -> dict:
    # Handle pending spell-retry first
    pending = state.get("pending")
    if pending and pending.get("kind") == "spell_retry":
        expected = pending.get("word")
        if not isinstance(expected, str):
            state["pending"] = None
            return {"correct": False, "feedback": "Session error; cleared pending.", "next": "question"}

        if (text or "") == expected:
            # append to end (repeat word later) and move on
            state["pending"] = None
            state["keys"].append(expected)
            state["idx"] += 1
            state["current"] = None
            return {"correct": True, "feedback": "Correct spelling. Continuing…", "next": "question"}

        return {"correct": False, "feedback": "Wrong spelling. Try again.", "next": "spell_retry"}

    current = state.get("current")
    if not isinstance(current, dict) or not current:
        # Build a question if missing
        current = build_question(state, study_set)

    if current.get("kind") == "skip":
        state["idx"] += 1
        state["current"] = None
        return {"correct": True, "feedback": "Skipped (not enough choices).", "next": "question"}

    if current.get("kind") == "finished":
        return {"correct": True, "feedback": "Finished.", "next": "finished"}

    mode = state["mode"]

    if current.get("kind") == "spelling":
        expected = current.get("answer")
        if (text or "") == expected:
            state["correct"] += 1
            state["idx"] += 1
            state["current"] = None
            return {"correct": True, "feedback": "Correct!", "next": "question" if state["idx"] < len(state["keys"]) else "finished"}

        # wrong
        word = str(expected)
        translation = str(study_set.get(word, ""))
        state["wrong"] += 1
        state["wrong_counts"][word] = int(state["wrong_counts"].get(word, 0)) + 1
        state["wrong_first"].setdefault(word, translation)
        state["pending"] = {"kind": "spell_retry", "word": word}
        return {"correct": False, "feedback": f"Wrong. Correct answer: '{word}'.", "next": "spell_retry"}

    # multiple_choice
    correct_idx = int(current["correct"])
    word = str(current["word"])
    translation = str(current["translation"])

    if choice == correct_idx:
        state["correct"] += 1
        state["idx"] += 1
        state["current"] = None
        return {"correct": True, "feedback": "Correct!", "next": "question" if state["idx"] < len(state["keys"]) else "finished"}

    state["wrong"] += 1
    state["wrong_counts"][word] = int(state["wrong_counts"].get(word, 0)) + 1
    state["wrong_first"].setdefault(word, translation)

    # Mirror CLI: force spelling of the word before proceeding
    state["pending"] = {"kind": "spell_retry", "word": word}
    cleaned = clean_text(translation) if mode == "en-to-ch" else word
    if mode == "en-to-ch":
        msg = f"Wrong. Correct answer: '{cleaned}'."
    else:
        msg = f"Wrong. Correct answer: '{word}'."

    return {"correct": False, "feedback": msg, "next": "spell_retry"}


def finalize_result(state: dict) -> EngineResult:
    wrong_first: dict = state.get("wrong_first") or {}
    wrong_counts: dict = state.get("wrong_counts") or {}
    wrong_words = [
        {"en": en, "ch": ch, "count": int(wrong_counts.get(en, 1))}
        for en, ch in wrong_first.items()
    ]
    return EngineResult(
        correct=int(state.get("correct", 0)),
        wrong=int(state.get("wrong", 0)),
        wrong_words_first_attempt=wrong_words,
    )
