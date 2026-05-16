import akshare as ak
import pandas as pd
import sys

def verify_historical_data():
    print("====== 🚀 开始 A股 历史资金流向数据获取测试 ======\n")
    
    # ---------------- 验证 1：概念板块资金流向 ----------------
    print("[测试 1] 正在尝试从东方财富获取【概念板块】资金流向排行...")
    try:
        df_concept = ak.stock_concept_fund_flow_rank_em()
        if not df_concept.empty:
            print(f"✅ 成功！获取到 {len(df_concept)} 个概念板块的数据。")
            print("📊 历史数据抽样展示 (主力资金流入前 5 名):")
            # 简化打印输出
            sample_c = df_concept[['序号', '概念板块名称', '今日今日主力净流入-净额', '主力净流入最大股']].head(5)
            # 转为亿元展示，方便看
            sample_c['今日今日主力净流入-净额'] = (sample_c['今日今日主力净流入-净额'] / 100000000).round(2)
            sample_c.columns = ['排名', '板块名称', '主力净流入(亿元)', '领涨个股']
            print(sample_c.to_string(index=False))
            print("-" * 50)
        else:
            print("❌ 警告：接口返回了空数据，请检查网络。")
    except Exception as e:
        print(f"❌ 错误：概念板块接口调用失败！错误信息: {e}")
        print("-" * 50)

    # ---------------- 验证 2：个股资金流向 ----------------
    print("\n[测试 2] 正在尝试从东方财富获取【个股】实时资金流向排行...")
    try:
        df_individual = ak.stock_individual_fund_flow_rank_em()
        if not df_individual.empty:
            print(f"✅ 成功！获取到 {len(df_individual)} 只股票的资金流向数据。")
            print("📊 历史数据抽样展示 (个股主力资金流入前 5 名):")
            sample_i = df_individual[['序号', '股票代码', '股票简称', '今日主力净流入-净额', '今日主力净流入-净占比']].head(5)
            sample_i['今日主力净流入-净额'] = (sample_i['今日主力净流入-净额'] / 100000000).round(2)
            sample_i.columns = ['排名', '代码', '简称', '主力净流入(亿元)', '净占比(%)']
            print(sample_i.to_string(index=False))
            print("-" * 50)
        else:
            print("❌ 警告：个股接口返回了空数据。")
    except Exception as e:
        print(f"❌ 错误：个股接口调用失败！错误信息: {e}")
        print("-" * 50)

    print("\n====== 🏁 测试结束 ======")

if __name__ == "__main__":
    verify_historical_data()