import csv
import json
import os
import random
import re
import subprocess
import sys
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import click
from gtts import gTTS


V2_SETS_DIR = Path("./v2/sets")
HISTORY_FILE = Path("./v2/history.log")

# One-time warning flag for missing ffplay
_FFPLAY_WARNED = False


def clean_text(text: str) -> str:
    """V2 compatibility: remove newlines, extra spaces; take first definition before ';'."""
    text = re.sub(r"[\r\n]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = text.split(";")[0].strip()
    return text


def speak(text: str) -> None:
    tts = gTTS(text=text, lang="en")
    filename = "word.mp3"
    tts.save(filename)


def play_audio(filename: str) -> None:
    """Play audio via ffplay.

    If ffplay (FFmpeg) is not installed, skip playback gracefully.
    """
    global _FFPLAY_WARNED
    try:
        with open(os.devnull, "w") as devnull:
            subprocess.run(["ffplay", "-nodisp", "-autoexit", filename], stdout=devnull, stderr=devnull)
    except FileNotFoundError:
        if not _FFPLAY_WARNED:
            print(
                "Warning: ffplay not found (FFmpeg not installed). Proceeding without audio playback.",
                file=sys.stderr,
            )
            _FFPLAY_WARNED = True
    except Exception:
        # Avoid crashing the quiz due to audio issues
        if not _FFPLAY_WARNED:
            print("Warning: Audio playback failed. Proceeding without audio playback.", file=sys.stderr)
            _FFPLAY_WARNED = True


def list_files(directory: Path) -> list[str]:
    if not directory.exists():
        return []
    files = [p.name for p in directory.iterdir() if p.is_file() and p.suffix.lower() == ".csv"]
    return sorted(
        files,
        key=lambda x: [int(t) if t.isdigit() else t.lower() for t in re.split(r"([0-9]+)", x)],
    )


def load_study_set(vocabulary_file: str | None) -> tuple[dict[str, str] | None, str | None]:
    """Returns (study_set, filename). study_set None means user quit interactive selection."""
    study_set: dict[str, str] = {}

    if not V2_SETS_DIR.exists():
        try:
            V2_SETS_DIR.mkdir(parents=True, exist_ok=True)
            print("Created sets/ directory. Add CSV files and try again.", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: Could not create sets/ directory: {e}", file=sys.stderr)
            sys.exit(1)

    if vocabulary_file:
        file_path = V2_SETS_DIR / vocabulary_file
        if not file_path.exists():
            print(f"Error: File '{vocabulary_file}' not found in sets/ directory", file=sys.stderr)
            sys.exit(1)
        try:
            with file_path.open(encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) < 2:
                        print(
                            f"Error: Corrupted CSV in {vocabulary_file}. Verify comma/semicolon separators",
                            file=sys.stderr,
                        )
                        sys.exit(3)
                    study_set[row[0]] = row[1]
            if not study_set:
                print(f"Error: No vocabulary entries found in {vocabulary_file}", file=sys.stderr)
                sys.exit(1)
            return study_set, vocabulary_file
        except Exception as e:
            print(f"Error: Failed to parse CSV file: {e}", file=sys.stderr)
            sys.exit(3)

    # Interactive selection (same UX as V2)
    per_page = 5
    while True:
        files = list_files(V2_SETS_DIR)
        if not files:
            print("Error: No vocabulary sets available in sets/ directory", file=sys.stderr)
            sys.exit(1)

        total_pages = (len(files) + per_page - 1) // per_page
        page = 1

        def display_page():
            start = (page - 1) * per_page
            end = start + per_page
            print(f"\nPage {page}/{total_pages}\n")
            for i, file in enumerate(files[start:end], start=1):
                print(f"{start + i}. {file}")

        while True:
            display_page()
            command = input("\nEnter file number to select, 'n' for next page, 'p' for previous page, 'q' to quit: ")

            if command.lower() == "q":
                return None, None
            if command.isdigit():
                file_index = int(command) - 1
                if 0 <= file_index < len(files):
                    vocabulary_file = files[file_index]
                    break
                print("Invalid file number. Please try again.\n")
                continue
            if command.lower() == "n":
                if page < total_pages:
                    page += 1
                else:
                    print("You are on the last page.\n")
                continue
            if command.lower() == "p":
                if page > 1:
                    page -= 1
                else:
                    print("You are on the first page.\n")
                continue
            print("Invalid command. Please try again.\n")

        # load selected
        file_path = V2_SETS_DIR / str(vocabulary_file)
        try:
            with file_path.open(encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) < 2:
                        print(
                            f"Error: Corrupted CSV in {file_path.name}. Verify comma/semicolon separators",
                            file=sys.stderr,
                        )
                        sys.exit(3)
                    study_set[row[0]] = row[1]
            print(f"Set: {file_path.name} loaded successfully!\n")
            return study_set, file_path.name
        except Exception as e:
            print(f"Error: Failed to parse CSV: {e}", file=sys.stderr)
            sys.exit(3)


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def append_history(record: dict) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_history() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    rows: list[dict] = []
    with HISTORY_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                # ignore corrupted lines
                continue
    return rows


def weak_words_for_set(vocab_file: str) -> set[str]:
    rows = [r for r in read_history() if r.get("set") == vocab_file]
    weak: set[str] = set()
    for r in rows:
        for ww in r.get("wrong_words", []) or []:
            en = ww.get("en") if isinstance(ww, dict) else None
            if isinstance(en, str) and en:
                weak.add(en)
    return weak


def print_wrong_words_block(wrong_words: list[tuple[str, str]]) -> None:
    if not wrong_words:
        return
    print("--- Wrong Words (first-attempt only) ---")
    for i, (en, ch) in enumerate(wrong_words, 1):
        print(f"{i}) {en}  -> {clean_text(ch)}")
    print("")


@dataclass
class QuizResult:
    correct: int
    wrong: int
    # Unique first-attempt wrong words for printing (en -> ch)
    wrong_words_first_attempt: list[tuple[str, str]]
    # Per-word wrong count within this session (en -> count)
    wrong_word_counts: dict[str, int]

    @property
    def accuracy(self) -> float:
        total = self.correct + self.wrong
        if total == 0:
            return 0.0
        return round(self.correct / total, 2) * 100


def quiz_en_to_ch(study_set: dict[str, str], keys: list[str]) -> QuizResult:
    correct = 0
    wrong = 0
    wrong_first: dict[str, str] = {}
    wrong_counts: dict[str, int] = {}

    for key in keys:
        word = key
        meaning = study_set[key]
        values = list(study_set.values())
        if meaning in values:
            values.remove(meaning)

        if len(values) < 3:
            print("\nWarning: Not enough unique values in dataset to create multiple choice options.")
            print(f"Skipping '{word}'...\n")
            continue

        random_values = random.sample(values, 3)
        possible_ans = [meaning] + random_values
        random.shuffle(possible_ans)
        question = {1: clean_text(possible_ans[0]), 2: clean_text(possible_ans[1]), 3: clean_text(possible_ans[2]), 4: clean_text(possible_ans[3])}

        while True:
            try:
                speak(word)
                counter = f"({correct + wrong + 1}/{len(keys)})"
                print(f"What is the meaning of '{word}'? {counter}")
                print(f"1. {question[1]}")
                print(f"2. {question[2]}")
                print(f"3. {question[3]}")
                print(f"4. {question[4]}")
                print("\n\n\n\n\n")
                threading.Thread(target=play_audio, args=("word.mp3",)).start()
                response = input("Your answer: ")

                if response not in ["1", "2", "3", "4"]:
                    raise ValueError("Invalid! Enter a number between 1 and 4.\n")

                if question[int(response)] == clean_text(meaning):
                    correct += 1
                    print("Correct!\n")
                    print("\033[1;37;42m ======================================================= \033[0m\n")
                else:
                    wrong += 1
                    wrong_counts[word] = wrong_counts.get(word, 0) + 1
                    wrong_first.setdefault(word, meaning)
                    cleaned_meaning = clean_text(meaning)
                    print(f"Wrong! The correct answer is '{cleaned_meaning}'.\n")
                    while True:
                        threading.Thread(target=play_audio, args=("word.mp3",)).start()
                        retry = input(f"Please spell the word '{word}' ! ans: ")
                        if retry == word:
                            break
                        print("Wrong! Please try again.\n")
                    keys.append(word)
                    print("\033[1;37;41m ======================================================= \033[0m\n")
                break
            except ValueError as e:
                print(e)

    return QuizResult(
        correct=correct,
        wrong=wrong,
        wrong_words_first_attempt=list(wrong_first.items()),
        wrong_word_counts=wrong_counts,
    )


def quiz_en_spelling(study_set: dict[str, str], keys: list[str]) -> QuizResult:
    correct = 0
    wrong = 0
    wrong_first: dict[str, str] = {}
    wrong_counts: dict[str, int] = {}

    for key in keys:
        word = key
        meaning = study_set[key]

        speak(word)
        counter = f"({correct + wrong + 1}/{len(keys)})"
        print(f"How do you spell this word? Meaning: {clean_text(meaning)} {counter}\n\n\n\n\n\n\n")
        response = input("Your answer: ")

        if response == word:
            correct += 1
            play_audio("word.mp3")
            print("Correct!\n")
            print("\033[1;37;42m ======================================================= \033[0m\n")
        else:
            wrong += 1
            wrong_counts[word] = wrong_counts.get(word, 0) + 1
            wrong_first.setdefault(word, meaning)
            print(f"Wrong! The correct answer is '{word}'.\n")
            while True:
                threading.Thread(target=play_audio, args=("word.mp3",)).start()
                retry = input("Please spell the word again ! ans: ")
                if retry == word:
                    break
                print(f"Wrong! The correct answer is '{word}'. Try again.\n")
            keys.append(word)
            print("\033[1;37;41m ======================================================= \033[0m\n")

    return QuizResult(
        correct=correct,
        wrong=wrong,
        wrong_words_first_attempt=list(wrong_first.items()),
        wrong_word_counts=wrong_counts,
    )


def quiz_ch_to_en(study_set: dict[str, str], keys: list[str]) -> QuizResult:
    correct = 0
    wrong = 0
    wrong_first: dict[str, str] = {}
    wrong_counts: dict[str, int] = {}

    for key in keys:
        word = key
        meaning = study_set[key]

        values = list(study_set.keys())
        if word in values:
            values.remove(word)

        cleaned_meaning = clean_text(meaning)

        if len(values) < 3:
            print("\nWarning: Not enough unique values in dataset to create multiple choice options.")
            print(f"Skipping '{word}'...\n")
            continue

        random_values = random.sample(values, 3)
        possible_ans = [word] + random_values
        random.shuffle(possible_ans)
        question = {1: clean_text(possible_ans[0]), 2: clean_text(possible_ans[1]), 3: clean_text(possible_ans[2]), 4: clean_text(possible_ans[3])}

        while True:
            try:
                speak(word)
                counter = f"({correct + wrong + 1}/{len(keys)})"
                print(f"What is the meaning of '{cleaned_meaning}'? {counter}")
                print(f"1. {question[1]}")
                print(f"2. {question[2]}")
                print(f"3. {question[3]}")
                print(f"4. {question[4]}")
                print("\n\n\n\n\n")
                response = input("Your answer: ")

                if response not in ["1", "2", "3", "4"]:
                    raise ValueError("Invalid! Enter a number between 1 and 4.\n")

                if question[int(response)] == word:
                    correct += 1
                    play_audio("word.mp3")
                    print("Correct!\n")
                    print("\033[1;37;42m ======================================================= \033[0m\n")
                else:
                    wrong += 1
                    wrong_counts[word] = wrong_counts.get(word, 0) + 1
                    wrong_first.setdefault(word, meaning)
                    print(f"Wrong! The correct answer is '{word}'.\n")
                    while True:
                        threading.Thread(target=play_audio, args=("word.mp3",)).start()
                        retry = input("Please spell the word again ! ans: ")
                        if retry == word:
                            break
                        print(f"Wrong! The correct answer is '{word}'. Try again.\n")
                    keys.append(word)
                    print("\033[1;37;41m ======================================================= \033[0m\n")
                break
            except ValueError as e:
                print(e)

    return QuizResult(
        correct=correct,
        wrong=wrong,
        wrong_words_first_attempt=list(wrong_first.items()),
        wrong_word_counts=wrong_counts,
    )


@click.group()
@click.version_option(version="2.0", prog_name="Vocabulary Learning System")
def main() -> None:
    """Vocabulary Learning System v2.0"""
    pass


@main.command("list")
def list_cmd() -> None:
    """List all available vocabulary sets in v2/sets."""
    if not V2_SETS_DIR.exists():
        print("Error: No vocabulary sets available in sets/ directory", file=sys.stderr)
        sys.exit(1)

    files = list_files(V2_SETS_DIR)
    if not files:
        print("Error: No vocabulary sets available in sets/ directory", file=sys.stderr)
        sys.exit(1)

    print(f"Available vocabulary sets ({len(files)} total):\n")
    for i, filename in enumerate(files, 1):
        file_path = V2_SETS_DIR / filename
        size = file_path.stat().st_size
        print(f"{i}. {filename} ({size} bytes)")


@main.command("quiz")
@click.option(
    "--type",
    "quiz_type",
    required=True,
    type=click.Choice(["en-to-ch", "en-spelling", "ch-to-en"]),
    help="Quiz mode",
)
@click.option("--set", "vocab_file", default=None, help="CSV filename in v2/sets/")
@click.option("--weak-only", is_flag=True, help="Only quiz on previously-wrong words for this set")
def quiz_cmd(quiz_type: str, vocab_file: str | None, weak_only: bool) -> None:
    """Run a quiz session (supports --weak-only and writes history)."""
    if weak_only and not vocab_file:
        raise click.UsageError("--weak-only requires --set")

    study_set, selected_file = load_study_set(vocab_file)
    if study_set is None:
        return

    assert selected_file is not None

    # apply weak-only filtering
    keys = list(study_set.keys())
    if weak_only:
        weak = weak_words_for_set(selected_file)
        keys = [k for k in keys if k in weak]
        if not keys:
            print("No weak words found for this set yet. Take a normal quiz first.")
            sys.exit(0)

    if quiz_type in ("en-to-ch", "ch-to-en") and len(study_set) < 4:
        print(
            "Error: Dataset has fewer than 4 words. Multiple-choice modes require ≥4 vocabulary entries",
            file=sys.stderr,
        )
        sys.exit(1)

    random.shuffle(keys)

    if quiz_type == "en-to-ch":
        result = quiz_en_to_ch(study_set, keys)
    elif quiz_type == "en-spelling":
        result = quiz_en_spelling(study_set, keys)
    else:
        result = quiz_ch_to_en(study_set, keys)

    print(f"Correct: {result.correct}\nWrong: {result.wrong}\nAccuracy: {result.accuracy}%\n")
    print_wrong_words_block(result.wrong_words_first_attempt)

    append_history(
        {
            "ts": now_iso(),
            "set": selected_file,
            "mode": quiz_type,
            "correct": result.correct,
            "wrong": result.wrong,
            "accuracy": result.accuracy,
            "wrong_words": [
                {"en": en, "ch": ch, "count": int(result.wrong_word_counts.get(en, 1))}
                for en, ch in result.wrong_words_first_attempt
            ],
        }
    )


@main.command("stats")
@click.option("--set", "vocab_file", default=None, help="Filter by CSV filename in v2/sets/")
def stats_cmd(vocab_file: str | None) -> None:
    """Show historical quiz statistics from v2/history.log."""
    rows = read_history()
    if vocab_file:
        rows = [r for r in rows if r.get("set") == vocab_file]

    if not rows:
        if vocab_file:
            print(f"No history records for set: {vocab_file}")
        else:
            print("No history records yet. Take a quiz first.")
        sys.exit(0)

    total = len(rows)
    avg_acc = sum(float(r.get("accuracy", 0.0)) for r in rows) / total
    last = rows[-1]

    # breakdown by set + mode
    buckets: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        k = (str(r.get("set")), str(r.get("mode")))
        buckets.setdefault(k, []).append(r)

    title = "Stats (filtered)" if vocab_file else "Stats (all)"
    print(title)
    print("=" * len(title))
    print(f"Total sessions: {total}")
    print(f"Average accuracy: {round(avg_acc, 2)}%")
    print(
        f"Last session: {last.get('ts')} | set={last.get('set')} | mode={last.get('mode')} | acc={last.get('accuracy')}%"
    )
    print("")

    print("By set & mode")
    print("------------")
    for (s, m), items in sorted(buckets.items(), key=lambda x: (x[0][0], x[0][1])):
        a = sum(float(i.get("accuracy", 0.0)) for i in items) / len(items)
        print(f"- {s} | {m}: sessions={len(items)}, avg_acc={round(a, 2)}%")

    # top wrong words (aggregate)
    wrong_counts: dict[str, int] = {}
    wrong_ch: dict[str, str] = {}
    for r in rows:
        for ww in r.get("wrong_words", []) or []:
            if not isinstance(ww, dict):
                continue
            en = ww.get("en")
            if not isinstance(en, str) or not en:
                continue

            c = ww.get("count")
            try:
                count_int = int(c) if c is not None else 1
            except (TypeError, ValueError):
                count_int = 1
            if count_int < 1:
                count_int = 1

            wrong_counts[en] = wrong_counts.get(en, 0) + count_int
            ch = ww.get("ch")
            if isinstance(ch, str) and ch and en not in wrong_ch:
                wrong_ch[en] = ch

    top10 = sorted(wrong_counts.items(), key=lambda kv: (-kv[1], kv[0].lower()))[:10]
    print("")
    print("Top 10 wrong words")
    print("------------------")
    if not top10:
        print("(no wrong words recorded)")
        return

    for i, (en, cnt) in enumerate(top10, 1):
        ch = wrong_ch.get(en, "")
        suffix = f" -> {clean_text(ch)}" if ch else ""
        print(f"{i}. {en} (wrong={cnt}){suffix}")


@main.group("vocab")
@click.option("--set", "vocab_file", required=True, help="Target CSV filename in v2/sets/")
@click.pass_context
def vocab_cmd(ctx: click.Context, vocab_file: str) -> None:
    """Manage vocabulary entries in a CSV set (add/delete)."""
    # Validate target file is under V2/sets and exists.
    target = (V2_SETS_DIR / vocab_file).resolve()
    base = V2_SETS_DIR.resolve()
    if base not in target.parents:
        raise click.UsageError("--set must point to an existing CSV in ./V2/sets/")
    if not target.exists() or target.suffix.lower() != ".csv":
        print(f"Error: File '{vocab_file}' not found in sets/ directory", file=sys.stderr)
        sys.exit(1)

    ctx.obj = {"target": target}


@vocab_cmd.command("add")
@click.argument("word")
@click.argument("translation")
@click.pass_context
def vocab_add(ctx: click.Context, word: str, translation: str) -> None:
    target: Path = ctx.obj["target"]

    # Load existing
    rows: list[list[str]] = []
    existing: set[str] = set()
    with target.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            rows.append(row)
            if row[0]:
                existing.add(row[0])

    if word in existing:
        print(f"'{word}' already exists in {target.name}. No change.")
        return

    # Ensure the file ends with a newline so the appended row starts on a new line.
    try:
        with target.open("rb+") as fb:
            fb.seek(0, os.SEEK_END)
            if fb.tell() > 0:
                fb.seek(-1, os.SEEK_END)
                if fb.read(1) != b"\n":
                    fb.write(b"\n")
    except OSError:
        # If we can't patch the newline, just proceed; csv.writer will still write a row.
        pass

    with target.open("a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([word, translation])

    print(f"Added: {word} -> {translation} (set={target.name})")


@vocab_cmd.command("delete")
@click.argument("word")
@click.pass_context
def vocab_delete(ctx: click.Context, word: str) -> None:
    target: Path = ctx.obj["target"]

    kept: list[list[str]] = []
    removed = False

    with target.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            if row[0] == word:
                removed = True
                continue
            kept.append(row)

    if not removed:
        print(f"'{word}' not found in {target.name}. No change.")
        return

    with target.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(kept)

    print(f"Deleted: {word} (set={target.name})")


if __name__ == "__main__":
    main()
