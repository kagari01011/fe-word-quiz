import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
WORDS_FILE = BASE_DIR / "words.json"
APP_FILE = BASE_DIR / "index.html"


def main():
    words = json.loads(WORDS_FILE.read_text(encoding="utf-8"))
    words_json = json.dumps(words, ensure_ascii=False)

    html = APP_FILE.read_text(encoding="utf-8")
    new_html, count = re.subn(
        r"const WORDS = \[.*?\];",
        f"const WORDS = {words_json};",
        html,
        count=1,
        flags=re.S,
    )
    if count == 0:
        raise SystemExit("WORDS の埋め込み箇所が見つかりませんでした")

    APP_FILE.write_text(new_html, encoding="utf-8")
    print(f"index.html を更新しました（単語数: {len(words)}）")


if __name__ == "__main__":
    main()
