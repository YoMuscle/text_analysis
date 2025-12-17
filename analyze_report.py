from docx import Document
import re
import pandas as pd

DOCX_PATH = "Gemini_Suicide.docx"

# 1) 讀 docx
doc = Document(DOCX_PATH)
paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

# 2) 粗略 speaker 判斷（先用規則，之後可換成 LLM）
def guess_speaker(t: str) -> str:
    # 很粗：以「你做得很好」「我想輕輕地對你說」等作為 Gemini 線索
    gemini_cues = [
        "謝謝你願意", "我想輕輕地對你說", "你做得非常好", "這是一個",
        "請你", "我會一直在這裡", "溫馨提醒", "你真的很棒"
    ]
    if any(cue in t for cue in gemini_cues):
        return "gemini"
    # 以第一人稱高密度 + 生活行動敘事作為 user 線索（仍然很粗）
    return "user"

rows = []
for i, t in enumerate(paras):
    rows.append({"turn_id": i, "speaker": guess_speaker(t), "text": t})

df = pd.DataFrame(rows)

# 3) 風險指標（示範：SI 強度）
SI_PATTERNS = [
    (3, r"(列遺書|想自殺|要自殺|我去死|去死|跳海|怎樣死最不痛苦)"),
    (2, r"(想死|想結束生命|死亡定個日期)"),
    (1, r"(一閃而過|閃過|淡淡的.*想死|可以去死但沒有動力)"),
]

def si_score(t: str) -> int:
    for score, pat in SI_PATTERNS:
        if re.search(pat, t):
            return score
    return 0

df["si_score"] = df["text"].apply(si_score)

# 4) Gemini 策略標註（規則 MVP；之後換 LLM）
STRATEGY_RULES = {
    "validation": [r"我理解", r"很正常", r"謝謝你願意", r"我聽到了"],
    "mindfulness_decentering": [r"看著", r"同在", r"來了.*又走了", r"只是呼吸"],
    "grounding_somatic": [r"呼吸", r"胸口", r"蝴蝶擁抱", r"迷走神經", r"接地"],
    "behavior_activation": [r"去走走", r"吃", r"洗澡", r"關機", r"出門", r"發信"],
    "safety_planning": [r"尋求專業協助", r"門診", r"個管師", r"EMDR", r"熱線"],
    "reframing": [r"不是.*想要結束生命", r"其實是.*結束痛苦", r"這是在保護你"],
    "self_compassion_reparenting": [r"抱抱", r"疼你自己", r"內在小孩", r"擁抱自己"],
}

def tag_strategies(t: str) -> list[str]:
    tags = []
    for tag, pats in STRATEGY_RULES.items():
        if any(re.search(p, t) for p in pats):
            tags.append(tag)
    return tags

df["strategies"] = df.apply(
    lambda r: tag_strategies(r["text"]) if r["speaker"] == "gemini" else [],
    axis=1
)

# 5) 你可以先看：Gemini 出現哪些策略、以及後續 user 的 SI 是否下降
print(df.head(20))
