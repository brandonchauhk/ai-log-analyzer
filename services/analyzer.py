# services/analyzer.py

import pandas as pd
from services.openai_client import call_llm

SYSTEM_PROMPT = """你是一位資深系統工程師兼 SRE，擅長閱讀各種系統與應用程式 Log，
幫忙找出問題、風險以及可能的根因，並提供實際可行的改善建議。

請注意：
- 你看到的是「已經解析好的結構化 log」，每一列是一個事件。
- 欄位例如：timestamp, level, source, message, host, process, module 等。
- level 若有 Error / Warning / Critical 類型，要特別留意。
"""


def _build_user_prompt(df: pd.DataFrame) -> str:
    """
    將 DataFrame 簡化成適合丟給 LLM 的文字。
    若行數太多，只取前 200 行，並說明已截斷。
    """
    total_rows = len(df)

    if total_rows > 200:
        sample_df = df.head(200)
        truncated_note = f"(注意：原本共有 {total_rows} 筆紀錄，此處僅顯示前 200 筆供分析)\n\n"
    else:
        sample_df = df
        truncated_note = ""

    csv_preview = sample_df.to_csv(index=False)

    # 用括號串接多行字串，避免三重反引號造成語法問題
    prompt = (
        "以下是已解析的 log 資料表，每一行代表一個事件：\n\n"
        f"{truncated_note}"
        "（以下為部分 log 的 CSV 內容預覽）\n"
        f"{csv_preview}\n"
        "（CSV 預覽結束）\n\n"
        "請根據這些 log，幫我做以下幾件事，回答請用繁體中文：\n\n"
        "1. **整體摘要**：用 3–6 行說明大致發生了什麼事（系統狀態如何？是否有明顯錯誤或異常？）。\n"
        "2. **問題與異常整理**：列出最重要的 3–8 個問題／異常類型，每個問題請包含：\n"
        "   - 問題類型 / 現象\n"
        "   - 關聯的 log 行為特徵（例如：哪些 level / source / process）\n"
        "   - 可能影響（例如：登入失敗、服務無法啟動、磁碟 I/O 問題等）\n"
        "3. **可能根因推測**：對較嚴重的問題，給出 1–3 個可能原因（基於 log 合理推論即可）。\n"
        "4. **建議排查與處理步驟**：用條列方式列出具體建議，例如：\n"
        "   - 先檢查什麼\n"
        "   - 再看哪個系統 / 服務\n"
        "   - 需要找哪個團隊（例如：網絡組、系統組、應用程式開發組）\n"
        "5. 若 log 看起來風險不高，請說明目前「沒有明顯重大問題」，但可持續監控哪些訊號。\n\n"
        "請用 Markdown 格式輸出分析結果，方便直接貼到報告或簡報中。"
    )

    return prompt


def analyze_logs(df: pd.DataFrame) -> str:
    """
    接受解析後的 DataFrame，呼叫 LLM，
    回傳一段 Markdown 分析報告。
    """
    if df is None or df.empty:
        return "解析後沒有任何 log 記錄可供分析。"

    user_prompt = _build_user_prompt(df)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.strip()},
        {"role": "user",   "content": user_prompt.strip()},
    ]

    result = call_llm(messages)
    return result
