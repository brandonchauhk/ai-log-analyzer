import streamlit as st
import pandas as pd

from config import OPENAI_API_KEY
from services.parser import parse_log_file
from services.analyzer import analyze_logs

st.set_page_config(page_title="AI Log Analyzer", page_icon="🧪", layout="wide")

st.title("🧪 AI Log Analyzer — 系統日誌智能分析工具")
st.caption("上傳系統 / 應用程式 Log，解析為結構化資料，並由 AI 協助做摘要、找出問題與建議處理方向。")

uploaded_file = st.file_uploader("上傳 Log 檔案（.log / .txt）", type=["log", "txt"])

log_type = st.selectbox(
    "選擇 Log 類型（會影響解析方式）",
    ["Windows Event Log", "Linux syslog", "Application Log"],
)

if uploaded_file is not None:
    # 讀取檔案內容
    log_text = uploaded_file.read().decode("utf-8", errors="ignore")

    st.subheader("📄 原始 Log 內容")
    st.text_area("Raw Log", log_text, height=260)

    # 解析 Log（依照選擇的類型）
    parsed_df = parse_log_file(log_text, log_type=log_type)

    st.subheader("📑 已解析 Log（結構化資料）")

    if parsed_df is None or parsed_df.empty:
        st.warning("⚠ 無法解析任何紀錄，請確認是否選對 Log 類型或檔案格式。")
    else:
        # ---- 基本統計區塊 ----
        st.markdown("### 📊 基本統計總覽")

        col1, col2 = st.columns(2)

        with col1:
            if "level" in parsed_df.columns:
                st.markdown("**依 Level 統計（Error / Warning / Info 等）**")
                level_counts = parsed_df["level"].value_counts().reset_index()
                level_counts.columns = ["level", "count"]
                st.dataframe(level_counts, use_container_width=True)
            else:
                st.markdown("**此 Log 類型沒有 level 欄位可統計。**")

        with col2:
            # 嘗試找一個「來源／模組／process」類型欄位做統計
            source_col = None
            for cand in ["source", "process", "module"]:
                if cand in parsed_df.columns:
                    source_col = cand
                    break

            if source_col:
                st.markdown(f"**依 {source_col} 統計（Top 10）**")
                src_counts = (
                    parsed_df[source_col]
                    .value_counts()
                    .head(10)
                    .reset_index()
                )
                src_counts.columns = [source_col, "count"]
                st.dataframe(src_counts, use_container_width=True)
            else:
                st.markdown("**此 Log 類型沒有適合做來源統計的欄位。**")

        st.markdown("---")
        st.markdown("### 🔍 篩選條件")

        # ---- 篩選條件：Level 與 Message 關鍵字 ----
        filtered_df = parsed_df.copy()

        # 1) 依 level 多選篩選（如有 level 欄位）
        if "level" in parsed_df.columns:
            all_levels = parsed_df["level"].dropna().unique().tolist()
            selected_levels = st.multiselect(
                "依 Level 篩選（不選代表顯示全部）：",
                options=all_levels,
                default=all_levels,
            )
            if selected_levels:
                filtered_df = filtered_df[filtered_df["level"].isin(selected_levels)]

        # 2) 依 message 關鍵字篩選
        if "message" in parsed_df.columns:
            keyword = st.text_input("依 Message 關鍵字篩選（可留空）：")
            if keyword:
                filtered_df = filtered_df[
                    filtered_df["message"].str.contains(keyword, case=False, na=False)
                ]

        st.markdown(f"目前符合條件的紀錄數量：**{len(filtered_df)}**")
        st.markdown("### 📋 篩選後的 Log 紀錄")
        st.dataframe(filtered_df, use_container_width=True)

        # ---- AI 分析按鈕：使用「篩選後」的結果 ----
        st.markdown("---")
        st.subheader("🤖 AI 智能分析")

        st.caption("AI 會根據目前篩選後的紀錄，總結系統狀態、找出問題類型，並給出建議排查步驟。")

        if st.button("🚀 使用 AI 進行智能分析"):
            if filtered_df is None or filtered_df.empty:
                st.warning("目前沒有任何符合條件的紀錄，無法進行 AI 分析。")
            else:
                with st.spinner("AI 正在分析 Log，請稍候..."):
                    analysis_md = analyze_logs(filtered_df)

                st.markdown("### 📌 AI 分析結果（Markdown）")
                st.markdown(analysis_md)

else:
    st.info("請先上傳一個 .log 或 .txt 檔案。你亦可以使用 sample_logs 內的示例檔作測試。")
