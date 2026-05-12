import streamlit as st
import pandas as pd
import akshare as ak
import plotly.express as px
import time
from datetime import datetime, timedelta

# ==========================================
# 1. 核心配置与工具函数
# ==========================================
def get_beijing_time():
    return datetime.utcnow() + timedelta(hours=8)

st.set_page_config(page_title="2026 资金雷达 (大单预警版)", layout="wide")

# 初始化历史记忆
if 'history_data' not in st.session_state:
    st.session_state.history_data = pd.DataFrame(columns=['时间', '板块', '资金流(亿)'])
# 初始化上一次的数据快照，用于对比异动
if 'last_snapshot' not in st.session_state:
    st.session_state.last_snapshot = None

def get_data_safe():
    try:
        df = ak.stock_sector_fund_flow_rank(indicator="今日")
        if df is not None and not df.empty:
            now_time = get_beijing_time().strftime('%H:%M:%S')
            subset = pd.concat([df.head(10), df.tail(5)])
            new_rows = []
            for _, row in subset.iterrows():
                new_rows.append({
                    '时间': now_time,
                    '板块': row['名称'],
                    '资金流(亿)': row['今日主力净流入-净额'] / 10000 
                })
            return pd.DataFrame(new_rows), None
        else:
            return None, "数据源暂无更新"
    except Exception as e:
        return None, str(e)

# ==========================================
# 2. 界面渲染
# ==========================================
st.title("🏹 A股实时资金流向 & 异动雷达")

# 侧边栏：设置预警阈值
with st.sidebar:
    st.header("🛡️ 预警设置")
    alert_threshold = st.number_input("大单异动阈值 (亿元)", min_value=0.1, max_value=50.0, value=2.0, step=0.5)
    st.caption(f"提示：若 30 秒内某板块资金变动超过 {alert_threshold} 亿，将触发预警。")
    st.write("---")
    demo_mode = st.toggle("开启演示模式 (模拟测试)")
    if st.button("清空所有数据"):
        st.session_state.history_data = pd.DataFrame(columns=['时间', '板块', '资金流(亿)'])
        st.session_state.last_snapshot = None
        st.rerun()

# 数据获取
if demo_mode:
    now = get_beijing_time().strftime('%H:%M:%S')
    # 模拟一个异动：半导体突然暴增 5 亿
    test_df = pd.DataFrame({
        '时间': [now] * 3,
        '板块': ['半导体', '人工智能', '中特估'],
        '资金流(亿)': [10.5, -1.8, 0.5] 
    })
    result, error = test_df, None
else:
    result, error = get_data_safe()

# ==========================================
# 3. 异动监测逻辑
# ==========================================
if result is not None:
    # 如果有上一次的记录，开始对比
    if st.session_state.last_snapshot is not None:
        # 合并新旧数据对比
        comparison = pd.merge(result, st.session_state.last_snapshot, on='板块', suffixes=('_新', '_旧'))
        comparison['变动'] = comparison['资金流(亿)_新'] - comparison['资金流(亿)_旧']
        
        # 筛选超过阈值的异动
        alerts = comparison[abs(comparison['变动']) >= alert_threshold]
        
        if not alerts.empty:
            for _, alert in alerts.iterrows():
                direction = "🔥 涌入" if alert['变动'] > 0 else "❄️ 撤离"
                st.toast(f"{alert['板块']} 板块 {direction} {abs(alert['变动']):.2f} 亿！", icon="🚨")
                if alert['变动'] > 0:
                    st.success(f"**大单预警**：{alert['板块']} 正在被主力猛攻，瞬间流向：+{alert['变动']:.2f} 亿元")
                else:
                    st.error(f"**提防砸盘**：{alert['板块']} 出现主力抛售，瞬间流向：{alert['变动']:.2f} 亿元")

    # 更新快照
    st.session_state.last_snapshot = result
    
    # 更新历史折线图数据
    st.session_state.history_data = pd.concat([st.session_state.history_data, result], ignore_index=True)
    if len(st.session_state.history_data) > 1500:
        st.session_state.history_data = st.session_state.history_data.tail(1500)

    # 绘图
    fig = px.line(
        st.session_state.history_data, 
        x="时间", y="资金流(亿)", color="板块",
        title="主力资金实时动态走势 (30秒/频)",
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.info(f"⏰ 北京时间：{get_beijing_time().strftime('%H:%M:%S')} | 数据运行中...")
else:
    st.warning(f"📡 等待数据同步: {error}")

time.sleep(30)
st.rerun()