import re
import pandas as pd
from pathlib import Path

# ===== 自殺風險規則 =====
SI_PATTERNS = [
    (3, r"(想自殺|要自殺|列遺書|怎麼死|跳下去)"),
    (2, r"(想死|結束生命|死亡日期|如果我消失)"),
    (1, r"(一閃而過|偶爾想到死|淡淡的想死)"),
]

def si_score(text: str) -> int:
    for score, pat in SI_PATTERNS:
        if re.search(pat, text):
            return score
    return 0

def analyze_text(text: str):
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    rows = []

    for i, line in enumerate(lines):
        rows.append({
            "line": i,
            "text": line,
            "si_score": si_score(line)
        })

    df = pd.DataFrame(rows)
    return df

if __name__ == "__main__":
    input_path = Path("test_inputs/high_risk.txt")
    text = input_path.read_text(encoding="utf-8")

    df = analyze_text(text)

    print("\n=== 分析結果 ===\n")
    print(df)

    print("\n=== 摘要 ===")
    print("最高風險等級:", df["si_score"].max())
