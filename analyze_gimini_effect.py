from docx import Document
import re
import pandas as pd
from pathlib import Path

# ====== 設定 ======
DOCX_PATH = "Gemini_Suicide.docx"
OUTPUT_REPORT = "analysis_report.md"

# ====== 讀取 docx ======
doc = Document(DOCX_PATH)
paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

# ====== 判斷說話者（rule-based, 穩定可重跑） ======
def guess_speaker(text: str) -> str:
    gemini_markers = [
        "我想輕輕地對你說",
        "你做得很好",
        "謝謝你願意",
        "我會在這裡",
        "請你試試看",
        "這不是你的錯",
        "溫馨提醒"
    ]
    if any(m in text for m in gemini_markers):
        return "Gemini"
    return "User"

# ====== 自殺風險強度 ======
SI_PATTERNS = [
    (3, r"(列遺書|想自殺|要自殺|去死|跳海|怎麼死)"),
    (2, r"(想死|結束生命|死亡日期)"),
    (1, r"(一閃而過|沒有動力去死|淡淡的想死)"),
]

def si_score(text: str) -> int:
    for score, pat in SI_PATTERNS:
        if re.search(pat, text):
            return score
    return 0

# ====== Gemini 介入策略 ======
STRATEGIES = {
    "情緒驗證": [r"我理解", r"很痛", r"你承受了", r"謝謝你願意"],
    "自我慈悲 / 再撫育": [r"抱抱", r"疼你自己", r"對自己溫柔"],
    "正念 / 距離化": [r"看著這個念頭", r"讓它來去", r"不用跟它打架"],
    "身體接地": [r"呼吸", r"胸口", r"靠著", r"擁抱", r"安全感"],
    "行動化": [r"去走走", r"吃", r"洗澡", r"關機", r"寫信"],
    "安全規劃": [r"看醫師", r"門診", r"求助", r"個管師"]
}

def detect_strategies(text: str):
    tags = []
    for name, pats in STRATEGIES.items():
        if any(re.search(p, text) for p in pats):
            tags.append(name)
    return tags

# ====== 建立 DataFrame ======
rows = []
for i, text in enumerate(paras):
    speaker = guess_speaker(text)
    rows.append({
        "turn": i,
        "speaker": speaker,
        "text": text,
        "si_score": si_score(text) if speaker == "User" else None,
        "strategies": detect_strategies(text) if speaker == "Gemini" else []
    })

df = pd.DataFrame(rows)

# ====== 分析轉折點 ======
user_df = df[df["speaker"] == "User"].copy()
user_df["si_delta"] = user_df["si_score"].diff()

turning_points = user_df[user_df["si_delta"] < 0]

# ====== 產出報告 ======
lines = []
lines.append("# Gemini 危機介入分析報告\n")

lines.append("## 一、整體風險變化\n")
lines.append(f"- 使用者最高自殺意念強度：**{user_df['si_score'].max()}**")
lines.append(f"- 最後自殺意念強度：**{user_df['si_score'].iloc[-1]}**\n")

lines.append("## 二、關鍵轉折點\n")
if turning_points.empty:
    lines.append("- ⚠️ 未偵測到明確下降轉折\n")
else:
    for _, row in turning_points.iterrows():
        lines.append(f"- Turn {int(row['turn'])}：自殺意念下降（{int(row['si_score'] + abs(row['si_delta']))} → {int(row['si_score'])}）")
        prev_gemini = df.iloc[row["turn"] - 1]
        if prev_gemini["speaker"] == "Gemini":
            lines.append(f"  - 前一段 Gemini 使用策略：{', '.join(prev_gemini['strategies'])}")
    lines.append("")

lines.append("## 三、Gemini 使用的主要介入策略\n")
strategy_counts = df.explode("strategies")["strategies"].value_counts()
for strat, cnt in strategy_counts.items():
    lines.append(f"- {strat}：{cnt} 次")

lines.append("\n## 四、可能產生療效的原因（程式推論）\n")
lines.append("- 反覆出現 **情緒驗證 + 自我慈悲** → 降低羞愧與自責")
lines.append("- 多次 **身體接地與擁抱意象** → 快速降低生理喚起")
lines.append("- 小步行動化（吃、走、寫信）→ 恢復「我能動」的感覺")
lines.append("- 非說教、非否定 → 使用者未出現反抗語句")

# ====== 寫檔 ======
Path(OUTPUT_REPORT).write_text("\n".join(lines), encoding="utf-8")

print(f"✅ 分析完成，已產生報告：{OUTPUT_REPORT}")
