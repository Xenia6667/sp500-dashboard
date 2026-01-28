#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 28 16:45:26 2026

@author: aditi
"""

# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

#%%# 1. 設定網頁的基本配置 (標題、寬度)
st.set_page_config(
    page_title="S&P 500 市場儀表板",
    layout="wide",  # 讓內容使用寬螢幕模式
    initial_sidebar_state="expanded" # 預設展開側邊欄
)

# 2. 讀取資料的函數
# @st.cache_data 是一個加速器，讓使用者切換選項時不用重新讀取檔案
@st.cache_data
def load_data():
    # 讀取我們在 Spyder 裡存好的 CSV
    df = pd.read_csv("sp500_analysis_2025.csv")
    return df

# 嘗試讀取資料，如果找不到檔案就報錯
try:
    df = load_data()
except FileNotFoundError:
    st.error("❌ 找不到資料檔 'sp500_analysis_2025.csv'。請確認檔案是否在同一資料夾中！")
    st.stop()

# --- 側邊欄設計 (Sidebar) ---
with st.sidebar:
    st.header("🔍 篩選條件")
    
    # A. 產業選擇器
    # 抓出所有不重複的 Sector 名稱，並在前面加上 'All' 選項
    sector_list = ["All"] + sorted(df['Sector'].unique().tolist())
    selected_sector = st.selectbox("選擇產業 (Sector)", sector_list)
    
    # B. 市值篩選器 (Slider)
    # 讓使用者過濾掉太小的公司
    min_cap, max_cap = int(df['Market_Cap'].min()), int(df['Market_Cap'].max())
    cap_filter = st.slider("市值過濾 (Min Market Cap)", min_cap, max_cap, min_cap)

# --- 資料過濾邏輯 ---
# 1. 先過濾市值
filtered_df = df[df['Market_Cap'] >= cap_filter]

# 2. 再過濾產業
if selected_sector != "All":
    filtered_df = filtered_df[filtered_df['Sector'] == selected_sector]

# --- 主畫面設計 (Main Page) ---
st.title("📈 S&P 500 市場動態儀表板")
st.markdown(f"目前顯示範圍：**{selected_sector}** 產業，共 **{len(filtered_df)}** 檔股票")

# 1. 關鍵指標 (KPI Cards)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("平均漲跌幅 (YTD)", f"{filtered_df['y25td_Return'].mean():.2f}%")
with col2:
    st.metric("平均本益比 (PE)", f"{filtered_df['PE_Ratio'].mean():.2f}")
with col3:
    # 找出漲最多的股票
    top_stock = filtered_df.loc[filtered_df['y25td_Return'].idxmax()]
    st.metric("最強個股", top_stock['Ticker'], f"{top_stock['y25td_Return']:.2f}%")
with col4:
    # 找出總市值 (兆/Billion)
    total_val = filtered_df['Market_Cap'].sum() / 1e9 # 換算成十億
    st.metric("總市值 (Billion)", f"${total_val:,.0f} B")

# 2. 互動式圖表 (Treemap)
st.subheader("🗺️ 板塊熱力圖 (Treemap)")
fig = px.treemap(
    filtered_df,
    path=[px.Constant('Market'), 'Sector', 'Industry', 'Ticker'], # 定義層級
    values='Market_Cap',
    color='y25td_Return',
    color_continuous_scale='RdYlGn',
    color_continuous_midpoint=0,
    hover_data=['PE_Ratio', 'y25td_Return', 'Market_Cap'],
    height=600 # 設定圖表高度
)
st.plotly_chart(fig, use_container_width=True)

# 3. 資料表格 (Data Table)
st.subheader("📋 詳細數據列表")
# 讓表格可以排序、搜尋
st.dataframe(
    filtered_df[['Ticker', 'Sector', 'Industry', 'Market_Cap', 'PE_Ratio', 'y25td_Return']].sort_values('y25td_Return', ascending=False),
    use_container_width=True,
    hide_index=True
)


# --- Part 4: 新增功能 - 個股走勢圖 ---
st.write("---") # 分隔線
st.subheader("📈 個股歷史走勢查詢")

# 1. 建立一個選單，讓使用者從「目前的篩選結果」中挑選一檔股票
# 這樣可以避免選到被過濾掉的公司
ticker_options = filtered_df['Ticker'].tolist()

if len(ticker_options) > 0:
    selected_ticker = st.selectbox("請選擇要查看走勢的股票:", ticker_options)
    
    # 2. 抓取該股票的歷史資料 (快取功能加速)
    @st.cache_data
    def get_stock_history(ticker):
        # 抓過去 1 年的股價
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        return hist

    # 顯示載入中的訊息
    with st.spinner(f"正在下載 {selected_ticker} 的歷史數據..."):
        hist_data = get_stock_history(selected_ticker)

    # 3. 畫出走勢圖 (Line Chart)
    # 這裡我們用 Streamlit 內建的簡單圖表，或者你也可以用 Plotly 畫 K 線
    st.line_chart(hist_data['Close'])
    
    # 顯示最新收盤價
    latest_price = hist_data['Close'].iloc[-1]
    st.metric(f"{selected_ticker} 最新收盤價", f"${latest_price:.2f}")

else:
    st.warning("⚠️ 目前篩選條件下沒有股票，請調整左側選單。")