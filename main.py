import streamlit as st
import pandas as pd
import akshare as ak
import plotly.express as px
import time
from datetime import datetime, timedelta

# ==========================================
# 1. 基础配置
# ==========================================
def get_beijing_time():
    return datetime.utcnow() + timedelta(hours=8)

st.set_page_config(page_title="2026 资金雷达 (全自定义版)", layout="wide")

# 初始化历史记忆
if 'history_data' not in st.session_state:
    st.session_state.history_data = pd.DataFrame(columns=['时间', '板块', '资金流(亿)'])
if 'last_snapshot' not in st.session_state:
    st.session_state.last_snapshot = None

# ==========================================
# 2. 侧边栏：自定义控制中心
# ==========================================
with st.sidebar:
    st.header("⚙️ 显示设置")
    # 让用户自己设置数量
    n_inflow = st.slider("监控流入板块数量", 1, 30, 10)
    n_outflow = st.slider("监控流出板块数量", 1, 20, 5)
    
    st.write("---")
    st.header("🛡️ 预警设置")
    alert_threshold = st.number_input("大单异动阈值 (亿元)", 0.1, 50.0, 2.0, 0.5)
    
    st.write("---")
    demo_mode = st.toggle("开启演示模式 (模拟数据)")
    if st.button("清空所有数据"):
        st.session_state.history_data = pd.DataFrame(columns=['时间', '板块', '资金流(亿)'])
        st.session_state.last_snapshot = None
        st.rerun()

# ==========================================
# 3. 数据获取逻辑
# ==========================================
def get_data_custom(in_count, out_count):
    try:
        df = ak.stock_sector_fund_flow_rank(indicator="今日")
        if df is not None and not df.empty:
            now_time = get_beijing_time().strftime('%H:%M:%S')
            
            # 核心：根据用户在侧边栏的设置来切片
            # head(in_count) 拿排名靠前的流入，tail(out_count) 拿排名靠后的流出
            subset = pd.concat([df.head(in_count), df.tail(out_count)])
            
            new_rows = []
            for _, row in subset.iterrows():
                new_rows.append({
                    '时间': now_time,
                    '板块': row['名称'],
                    '资金流(亿)': row['今日主力净流入-净额'] / 10000 
                })
            return pd.DataFrame(new_rows), None
    except Exception as e:
        return None, str(e)
    return None, "未获取到数据"

# 数据处理
if demo_mode:
    now = get_beijing_time().strftime('%H:%M:%S')
    test_df = pd.DataFrame({
        '时间': [now] * 3,
        '板块': ['测试流入1', '测试流入2', '测试流出1'],
        '资金流(亿)': [5.0, 3.2, -4.5]
    })
    result, error = test_df, None
else:
    # 传入用户设置的数量
    result, error = get_data_custom(n_inflow, n_outflow)

# ==========================================
# 4. 异动雷达与绘图
# ==========================================
st.title("🏹 A股实时资金流向 & 异动雷达")

if result is not None:
    # 异动预警 (Toast & Alert)
    if st.session_state.last_snapshot is not None:
        comparison = pd.merge(result, st.session_state.last_snapshot, on='板块', suffixes=('_新', '_旧'))
        comparison['变动'] = comparison['资金流(亿)_新'] - comparison['资金流(亿)_旧']
        alerts = comparison[abs(comparison['变动']) >= alert_threshold]
        for _, alert in alerts.iterrows():
            if alert['变动'] > 0:
                st.success(f"🚨 **大单涌入**：{alert['板块']} 瞬时爆发 +{alert['变动']:.2f} 亿！")
            else:
                st.error(f"🚨 **主力砸盘**：{alert['板块']} 瞬时撤离 {alert['变动']:.2f} 亿！")

    st.session_state.last_snapshot = result
    
    # 更新折线图历史
    st.session_state.history_data = pd.concat([st.session_state.history_data, result], ignore_index=True)
    # 限制数据长度，显示板块越多，历史数据保留越短以防卡顿
    max_points = 2000
    if len(st.session_state.history_data) > max_points:
        st.session_state.history_data = st.session_state.history_data.tail(max_points)

    # 绘图
    fig = px.line(
        st.session_state.history_data, 
        x="时间", y="资金流(亿)", color="板块",
        title=f"实时监控：流入前{n_inflow} & 流出前{n_outflow} 板块轨迹",
        template="plotly_dark"
    )
    fig.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)
    
    st.info(f"⏰ 北京时间：{get_beijing_time().strftime('%H:%M:%S')} | 已加载全市场实时数据")
else:
    st.warning(f"📡 接口状态：{error}")

time.sleep(30)
st.rerun()