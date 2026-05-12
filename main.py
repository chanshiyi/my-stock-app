import streamlit as st
import pandas as pd
import akshare as ak
import plotly.express as px
import time
from datetime import datetime, timedelta

# ==========================================
# 1. 自动时区修正函数
# ==========================================
def get_beijing_time():
    # 获取服务器当前时间，并强行加上 8 小时
    return datetime.utcnow() + timedelta(hours=8)

st.set_page_config(page_title="2026 资金监控 (北京时间版)", layout="wide")

# 初始化历史记忆
if 'history_data' not in st.session_state:
    st.session_state.history_data = pd.DataFrame(columns=['时间', '板块', '资金流(亿)'])

def get_data_safe():
    try:
        df = ak.stock_sector_fund_flow_rank(indicator="今日")
        if df is not None and not df.empty:
            # 使用修正后的北京时间
            now_time = get_beijing_time().strftime('%H:%M:%S')
            subset = pd.concat([df.head(8), df.tail(4)])
            new_rows = []
            for _, row in subset.iterrows():
                new_rows.append({
                    '时间': now_time,
                    '板块': row['名称'],
                    '资金流(亿)': row['今日主力净流入-净额'] / 10000 
                })
            return pd.DataFrame(new_rows), None
        else:
            return None, "目前非交易时段，或服务器暂未更新数据。"
    except Exception as e:
        return None, f"同步受阻: {str(e)}"

# ==========================================
# 2. 界面渲染
# ==========================================
st.title("🏹 A股实时分时资金流 (北京时间版)")

# 显示修正后的北京时间，让你心里有数
st.info(f"⏰ 当前北京时间：{get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}")

with st.sidebar:
    st.header("调试选项")
    demo_mode = st.toggle("开启演示模式 (测试图表)")
    if st.button("清空所有数据"):
        st.session_state.history_data = pd.DataFrame(columns=['时间', '板块', '资金流(亿)'])
        st.rerun()

if demo_mode:
    now = get_beijing_time().strftime('%H:%M:%S')
    test_df = pd.DataFrame({
        '时间': [now] * 3,
        '板块': ['半导体', '人工智能', '中特估'],
        '资金流(亿)': [2.5, -1.8, 0.5]
    })
    result, error = test_df, None
else:
    result, error = get_data_safe()

if result is not None:
    st.session_state.history_data = pd.concat([st.session_state.history_data, result]).ignore_index=True
    if len(st.session_state.history_data) > 1500:
        st.session_state.history_data = st.session_state.history_data.tail(1500)

    # 绘图逻辑
    fig = px.line(
        st.session_state.history_data, 
        x="时间", y="资金流(亿)", color="板块",
        title="主力资金实时动态走势 (复刻图2效果)",
        template="plotly_dark"
    )
    fig.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(result, use_container_width=True)
else:
    st.warning(f"📡 {error}")

# 30秒刷新一次
time.sleep(30)
st.rerun()