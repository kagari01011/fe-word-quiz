import json
import random
import sys
import unicodedata
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
WORDS_FILE = BASE_DIR / "words.json"
PROGRESS_FILE = BASE_DIR / "progress.json"

WRONG_WEIGHT = 3  # 間違えるほど出題されやすくなる係数


class QuitSession(Exception):
    pass


def setup_io():
    for stream in (sys.stdout, sys.stdin):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def load_words():
    with open(WORDS_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_progress(progress):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def word_key(word):
    return f"{word['category']}::{word['term']}"


def get_entry(progress, word):
    return progress.setdefault(word_key(word), {"asked": 0, "correct": 0, "wrong": 0})


def normalize(text):
    text = unicodedata.normalize("NFKC", text)
    return text.strip().lower().replace(" ", "").replace("　", "")


def accepted_answers(word):
    return {normalize(word["term"])} | {normalize(a) for a in word.get("aliases", [])}


def categories_of(words):
    seen = []
    for w in words:
        if w["category"] not in seen:
            seen.append(w["category"])
    return seen


def choose_category(words):
    cats = categories_of(words)
    print("\n分野を選んでください")
    print(" 0: すべての分野")
    for i, c in enumerate(cats, 1):
        print(f" {i}: {c}")
    while True:
        ans = input("番号 > ").strip()
        if ans == "0":
            return None
        if ans.isdigit() and 1 <= int(ans) <= len(cats):
            return cats[int(ans) - 1]
        print("入力が正しくありません。")


def pick_question(pool, progress, last_key):
    candidates = pool
    if len(pool) > 1 and last_key is not None:
        candidates = [w for w in pool if word_key(w) != last_key]
    weights = [1 + get_entry(progress, w)["wrong"] * WRONG_WEIGHT for w in candidates]
    return random.choices(candidates, weights=weights, k=1)[0]


def ask_question(word, progress, index, total):
    print(f"\n--- 第{index}問 / {total} [{word['category']}] ---")
    print(f"意味: {word['meaning']}")
    answer = input("用語は？ (qで中断) > ").strip()
    if normalize(answer) in ("q", "quit"):
        raise QuitSession()

    entry = get_entry(progress, word)
    entry["asked"] += 1
    if normalize(answer) in accepted_answers(word):
        entry["correct"] += 1
        print("○ 正解！")
    else:
        entry["wrong"] += 1
        aliases = word.get("aliases", [])
        suffix = f"（別解: {'、'.join(aliases)}）" if aliases else ""
        print(f"× 不正解。正解は「{word['term']}」{suffix}")


def run_quiz(words, progress, category):
    pool = words if category is None else [w for w in words if w["category"] == category]
    if not pool:
        print("この分野には問題がありません。")
        return

    raw = input("出題数を入力してください（空欄で10問） > ").strip()
    total = int(raw) if raw.isdigit() and int(raw) > 0 else 10

    last_key = None
    asked_count = 0
    try:
        for i in range(1, total + 1):
            word = pick_question(pool, progress, last_key)
            ask_question(word, progress, i, total)
            last_key = word_key(word)
            asked_count += 1
    except QuitSession:
        print("\n中断しました。")
    finally:
        save_progress(progress)
        print(f"\n{asked_count}問に解答しました。結果を保存しました。")


def show_stats(words, progress):
    cats = categories_of(words)
    print("\n=== 分野別の成績 ===")
    for c in cats:
        cat_words = [w for w in words if w["category"] == c]
        asked = sum(get_entry(progress, w)["asked"] for w in cat_words)
        correct = sum(get_entry(progress, w)["correct"] for w in cat_words)
        if asked == 0:
            print(f" {c}: 未挑戦")
        else:
            rate = correct / asked * 100
            print(f" {c}: {correct}/{asked} 正解 ({rate:.0f}%)")

    weak = sorted(
        words,
        key=lambda w: get_entry(progress, w)["wrong"],
        reverse=True,
    )
    weak = [w for w in weak if get_entry(progress, w)["wrong"] > 0][:10]
    if weak:
        print("\n=== 苦手な用語 TOP10 ===")
        for w in weak:
            e = get_entry(progress, w)
            print(f" {w['term']} ({w['category']}) - 間違い{e['wrong']}回 / 出題{e['asked']}回")
    else:
        print("\nまだ間違えた問題はありません。")


def main():
    setup_io()
    words = load_words()
    progress = load_progress()

    print("基本情報技術者試験 単語クイズ")
    while True:
        print("\n1: 問題を始める")
        print("2: 成績を見る")
        print("3: 終了")
        choice = input("番号 > ").strip()
        if choice == "1":
            category = choose_category(words)
            run_quiz(words, progress, category)
        elif choice == "2":
            show_stats(words, progress)
        elif choice == "3":
            print("お疲れさまでした。")
            break
        else:
            print("入力が正しくありません。")


if __name__ == "__main__":
    main()
