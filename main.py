import streamlit as st
import akshare as ak
import pandas as pd
import time

# 设置网页标题和布局
st.set_page_config(page_title="A股资金流向实时监控面板", layout="wide")

st.title("🔍 A股资金流向实时监控面板 (云端版)")
st.caption("数据来源：东方财富网 | 页面支持手动或自动刷新")

# --- 侧边栏控制区域 ---
st.sidebar.header("⚙️ 控制面板")
refresh_rate = st.sidebar.slider("数据自动刷新频率 (秒)", min_value=10, max_value=120, value=30)
auto_refresh = st.sidebar.checkbox("开启自动刷新", value=False)

# 缓存数据获取函数，避免多用户同时高频请求导致 IP 被封
@st.cache_data(ttl=15)
def get_market_flow():
    try:
        df = ak.stock_concept_fund_flow_rank_em()
        df = df.rename(columns={
            "序号": "排名", "概念板块名称": "板块名称",
            "今日今日主力净流入-净额": "主力净流入(元)", "今日今日主力净流入-净率": "主力净流入率(%)",
            "今日超大单净流入-净额": "超大单净流入(元)", "今日大单净流入-净额": "大单净流入(元)",
            "主力净流入最大股": "领涨个股"
        })
        money_cols = ["主力净流入(元)", "超大单净流入(元)", "大单净流入(元)"]
        for col in money_cols:
            df[col] = (df[col] / 100000000).round(2)
            df = df.rename(columns={col: col.replace("(元)", "(亿元)")})
        return df[["排名", "板块名称", "主力净流入(亿元)", "主力净流入率(%)", "超大单净流入(亿元)", "大单净流入(亿元)", "领涨个股"]]
    except Exception as e:
        return pd.DataFrame()

# --- 主面板数据渲染 ---
data_df = get_market_flow()

if not data_df.empty:
    total_inflow = data_df["主力净流入(亿元)"].sum().round(2)
    
    # 顶部指标看板
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="今日监控概念板块总净流入", value=f"{total_inflow} 亿元")
    with col2:
        top_1 = data_df.iloc[0]
        st.metric(label="🥇 资金最青睐板块", value=top_1["板块名称"], delta=f"+{top_1['主力净流入(亿元)']} 亿")
    with col3:
        last_1 = data_df.iloc[-1]
        st.metric(label="💔 资金砸盘最狠板块", value=last_1["板块名称"], delta=f"{last_1['主力净流入(亿元)']} 亿")
    
    st.markdown("---")
    
    # 数据表格展示
    left_col, right_col = st.columns(2)
    with left_col:
        st.subheader("🔥 今日主力资金【流入】前 15 名")
        st.dataframe(data_df.sort_values(by="主力净流入(亿元)", ascending=False).head(15), use_container_width=True, hide_index=True)
    with right_col:
        st.subheader("❄️ 今日主力资金【流出】前 15 名")
        st.dataframe(data_df.sort_values(by="主力净流入(亿元)", ascending=True).head(15), use_container_width=True, hide_index=True)
        
    st.caption(f"⏱️ 界面最后刷新时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
else:
    st.warning("暂无数据，可能是非交易时间、接口维护或网络延迟。点击页面右上角可以手动刷新。")

# 云端自动刷新逻辑
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()