import re
import pandas as pd

# ===== 自殺意念強度 =====
SI_RULES = [
    (3, r"(想自殺|要自殺|怎麼死)"),
    (2, r"(想死|不想活)"),
    (1, r"(一閃而過|偶爾想到死)"),
]

def si_score(text):
    for s, p in SI_RULES:
        if re.search(p, text):
            return s
    return 0

# ===== Gemini 策略 =====
STRATEGIES = {
    "情緒驗證": [r"謝謝你願意", r"不容易", r"我理解"],
    "正念距離化": [r"不用跟它打架", r"看著它"],
    "自我慈悲": [r"陪著自己", r"溫柔"],
}

def detect_strategies(text):
    tags = []
    for name, pats in STRATEGIES.items():
        if any(re.search(p, text) for p in pats):
            tags.append(name)
    return tags

# ===== 讀對話 =====
rows = []
with open("conversation.txt", encoding="utf-8") as f:
    for i, line in enumerate(f):
        speaker, text = line.strip().split(":", 1)
        rows.append({
            "turn": i,
            "speaker": speaker,
            "text": text.strip(),
            "si": si_score(text) if speaker == "User" else None,
            "strategies": detect_strategies(text) if speaker == "Gemini" else []
        })

df = pd.DataFrame(rows)

# ===== 找轉折點 =====
user_df = df[df.speaker == "User"].copy()
user_df["delta"] = user_df.si.diff()

print("\n📉 自殺意念下降事件：\n")

for _, row in user_df[user_df.delta < 0].iterrows():
    prev = df.loc[row.turn - 1]
    print(f"- Turn {row.turn}: SI {int(row.si + abs(row.delta))} → {int(row.si)}")
    print(f"  Gemini 策略: {prev.strategies}")
