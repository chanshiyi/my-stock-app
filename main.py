import streamlit as st
import akshare as ak
import pandas as pd
import time
import socket

# 设置网页标题和布局
st.set_page_config(page_title="A股资金流向实时监控面板", layout="wide")

st.title("🔍 A股资金流向实时监控面板 (100%稳定版)")
st.caption("数据来源：东方财富网 | 实时监控主力资金动向")

# 设置全局网络超时时间
socket.setdefaulttimeout(15)

# --- 侧边栏控制区域 ---
st.sidebar.header("⚙️ 控制面板")
monitor_type = st.sidebar.selectbox("选择监控维度", ["行业板块资金流", "个股资金流"])
refresh_rate = st.sidebar.slider("数据自动刷新频率 (秒)", min_value=10, max_value=120, value=30)
auto_refresh = st.sidebar.checkbox("开启自动刷新", value=False)

def get_stock_data_v3(data_type):
    with st.spinner("🔄 正在努力请求东方财富数据接口..."):
        try:
            if data_type == "行业板块资金流":
                # 使用东方财富最核心、最稳定的行业资金流接口
                df = ak.stock_sector_fund_flow_rank_by_1_day_wp()
                if df is None or df.empty:
                    return pd.DataFrame()
                
                # 重新规范列名
                df = df.rename(columns={
                    "序号": "排名", "名称": "板块名称",
                    "今日主力净流入-净额": "主力净流入(元)", "今日主力净流入-净率": "主力净流入率(%)",
                    "今日超大单净流入-净额": "超大单净流入(元)", "今日大单净流入-净额": "大单净流入(元)",
                    "最大净流入股票": "领涨个股"
                })
                # 将元转换为亿元
                money_cols = ["主力净流入(元)", "超大单净流入(元)", "大单净流入(元)"]
                for col in money_cols:
                    if col in df.columns:
                        df[col] = (pd.to_numeric(df[col], errors='coerce') / 100000000).round(2)
                        df = df.rename(columns={col: col.replace("(元)", "(亿元)")})
                return df[["排名", "板块名称", "主力净流入(亿元)", "主力净流入率(%)", "超大单净流入(亿元)", "大单净流入(亿元)", "领涨个股"]]
                
            else:
                # 使用东方财富个股排行通用接口
                df = ak.stock_individual_fund_flow_rank()
                if df is None or df.empty:
                    return pd.DataFrame()
                
                df = df.rename(columns={
                    "序号": "排名", "股票代码": "代码", "股票简称": "简称",
                    "今日主力净流入-净额": "主力净流入(元)", "今日主力净流入-净率": "主力净流入率(%)",
                    "今日超大单净流入-净额": "超大单净流入(元)", "今日大单净流入-净额": "大单净流入(元)"
                })
                money_cols = ["主力净流入(元)", "超大单净流入(元)", "大单净流入(元)"]
                for col in money_cols:
                    if col in df.columns:
                        df[col] = (pd.to_numeric(df[col], errors='coerce') / 100000000).round(2)
                        df = df.rename(columns={col: col.replace("(元)", "(亿元)")})
                return df[["排名", "代码", "简称", "主力净流入(亿元)", "主力净流入率(%)", "超大单净流入(亿元)", "大单净流入(亿元)"]]
                
        except Exception as e:
            st.error(f"⚠️ 报错提示：{str(e)}\n\n请不要慌，这通常是云端库版本问题。")
            return pd.DataFrame()

# --- 主面板数据渲染 ---
data_df = get_stock_data_v3(monitor_type)

if not data_df.empty:
    # 过滤掉无法转换的空值，确保求和不报错
    valid_inflow = pd.to_numeric(data_df["主力净流入(亿元)"], errors='coerce').dropna()
    total_inflow = valid_inflow.sum().round(2)
    name_col = "板块名称" if monitor_type == "行业板块资金流" else "简称"
    
    # 顶部指标看板
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label=f"今日监控{monitor_type}总净流入", value=f"{total_inflow} 亿元")
    with col2:
        top_1 = data_df.sort_values(by="主力净流入(亿元)", ascending=False).iloc[0]
        st.metric(label="🥇 资金最青睐", value=top_1[name_col], delta=f"+{top_1['主力净流入(亿元)']} 亿")
    with col3:
        last_1 = data_df.sort_values(by="主力净流入(亿元)", ascending=True).iloc[0]
        st.metric(label="💔 资金砸盘最狠", value=last_1[name_col], delta=f"{last_1['主力净流入(亿元)']} 亿")
    
    st.markdown("---")
    
    # 数据表格展示
    left_col, right_col = st.columns(2)
    with left_col:
        st.subheader("🔥 主力资金【流入】前 15 名")
        st.dataframe(data_df.sort_values(by="主力净流入(亿元)", ascending=False).head(15), use_container_width=True, hide_index=True)
    with right_col:
        st.subheader("❄️ 主力资金【流出】前 15 名")
        st.dataframe(data_df.sort_values(by="主力净流入(亿元)", ascending=True).head(15), use_container_width=True, hide_index=True)
        
    st.caption(f"⏱️ 界面最后刷新时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
else:
    if st.button("🔄 重新尝试获取数据"):
        st.rerun()

# 云端自动刷新逻辑
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()