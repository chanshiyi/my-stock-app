import streamlit as st
import pandas as pd
import akshare as ak
import plotly.express as px
import time
from datetime import datetime

st.set_page_config(page_title="2026 资金监控云端版", layout="wide")

# 初始化历史记忆
if 'history_data' not in st.session_state:
    st.session_state.history_data = pd.DataFrame(columns=['时间', '板块', '资金流(亿)'])

def get_data_safe():
    try:
        # 获取数据
        df = ak.stock_sector_fund_flow_rank(indicator="今日")
        
        if df is not None and not df.empty:
            now_time = datetime.now().strftime('%H:%M:%S')
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
        # 捕获类似 'Expecting value' 的错误，并友好提示
        return None, f"同步受阻（通常因为未开盘或IP限制）: {str(e)}"

st.title("🏹 A股分时资金流动态轨迹 (云端版)")
st.caption(f"☁️ 服务器时间：{datetime.now().strftime('%H:%M:%S')} | 建议 09:35 - 15:00 观察")

# 侧边栏
with st.sidebar:
    st.header("调试选项")
    # 增加一个演示模式，让你在没开盘时也能看到图表样子
    demo_mode = st.toggle("开启演示模式 (使用模拟数据)")
    if st.button("清空所有数据"):
        st.session_state.history_data = pd.DataFrame(columns=['时间', '板块', '资金流(亿)'])
        st.rerun()

# 数据获取逻辑
if demo_mode:
    # 模拟数据生成（仅供测试界面）
    now = datetime.now().strftime('%H:%M:%S')
    test_df = pd.DataFrame({
        '时间': [now] * 3,
        '板块': ['半导体', '电力设备', '计算机'],
        '资金流(亿)': [1.5, -2.1, 0.8]
    })
    result, error = test_df, None
else:
    result, error = get_data_safe()

# 渲染逻辑
if result is not None:
    st.session_state.history_data = pd.concat([st.session_state.history_data, result]).ignore_index=True
    if len(st.session_state.history_data) > 1500:
        st.session_state.history_data = st.session_state.history_data.tail(1500)

    # 绘图：复刻图2效果
    fig = px.line(
        st.session_state.history_data, 
        x="时间", y="资金流(亿)", color="板块",
        title="主力资金实时动态走势",
        template="plotly_dark"
    )
    fig.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(result, use_container_width=True)
else:
    st.warning(f"📡 {error}")
    st.info("💡 如果你想现在看看图表效果，请点击左侧的‘开启演示模式’。")

time.sleep(30)
st.rerun()