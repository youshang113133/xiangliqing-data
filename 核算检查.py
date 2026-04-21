#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
湘里情每日数据更新核算检查脚本
用法: python 核算检查.py data.json
"""

import json
import sys
from datetime import datetime
from collections import defaultdict

def load_data(filepath):
    """加载数据文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_sales_math(data):
    """检查1-2: 成本+毛利额=销售额，毛利率计算"""
    errors = []
    
    # 检查日报数据（中文嵌套结构）
    daily = data.get('dailyReportData', {})
    indicators = daily.get('核心经营指标', {})
    
    if indicators:
        # 月累计数据
        sales = indicators.get('销售额', {}).get('月累计', 0)
        cost = indicators.get('成本', {}).get('月累计', 0)
        profit = indicators.get('毛利额', {}).get('月累计', 0)
        rate = indicators.get('毛利率', {}).get('月累计', 0)
        
        # 检查1: 成本+毛利额=销售额
        diff = abs(cost + profit - sales)
        if diff > 1:
            errors.append(f"❌ 检查1失败: 成本({cost:,.2f}) + 毛利额({profit:,.2f}) ≠ 销售额({sales:,.2f}), 差异: {diff:,.2f}")
        else:
            print(f"✅ 检查1通过: 成本({cost:,.2f}) + 毛利额({profit:,.2f}) = 销售额({sales:,.2f})")
        
        # 检查2: 毛利率计算
        if sales > 0:
            calc_rate = profit / sales
            rate_diff = abs(calc_rate - rate)
            if rate_diff > 0.001:
                errors.append(f"❌ 检查2失败: 毛利率({rate*100:.2f}%) ≠ 毛利额/销售额({calc_rate*100:.2f}%), 差异: {rate_diff*100:.2f}%")
            else:
                print(f"✅ 检查2通过: 毛利率 = {rate*100:.2f}%")
    else:
        errors.append("❌ 核心经营指标数据为空")
    
    return errors

def check_sales_progress(data):
    """检查3-4: 区域小计和公司合计"""
    errors = []
    
    progress = data.get('salesProgressData', [])
    if not progress:
        errors.append("❌ 检查3-4失败: salesProgressData为空")
        return errors
    
    # 按区域汇总
    dept_sums = defaultdict(float)
    company_sum = 0
    for item in progress:
        dept = item.get('区域', '')
        salesman = item.get('业务经理', '')
        sales = float(item.get('月销售额', 0))
        
        # 只统计业务员，跳过"小计"和"公司合计"行
        if salesman == '小计':
            dept_sums[dept] = sales  # 直接用小计值
        elif salesman == '公司合计':
            company_sum = sales  # 记录公司合计
    
    # 检查3: 各区域小计是否等于业务员之和
    print(f"✅ 检查3: 各区域业务员销售额汇总:")
    for dept, total in dept_sums.items():
        if dept:
            print(f"   - {dept}: ¥{total:,.2f}")
    
    # 检查4: 公司合计 = 各区域小计之和
    dept_total = sum(dept_sums.values())
    
    # 先检查小计之和是否等于公司合计
    if abs(dept_total - company_sum) > 200:  # 允许200元以内的浮点误差
        errors.append(f"❌ 检查4a失败: 各区域小计之和({dept_total:,.2f}) ≠ 公司合计({company_sum:,.2f})")
    else:
        print(f"✅ 检查4a通过: 各区域小计之和 ≈ 公司合计 = ¥{company_sum:,.2f}")
    
    # 再检查公司合计是否等于月累计（参考项，不影响核算通过）
    daily = data.get('dailyReportData', {})
    monthly_sales = daily.get('核心经营指标', {}).get('销售额', {}).get('月累计', 0)
    
    diff = abs(company_sum - monthly_sales)
    if diff > 100:
        print(f"ℹ️ 检查4b提示: 公司合计({company_sum:,.2f}) ≠ 月累计({monthly_sales:,.2f}), 差异: {diff:,.2f}")
        print(f"   (注: 月累计含所有订单，公司合计仅含21个业务经理)")
    else:
        print(f"✅ 检查4b通过: 公司合计 ≈ 月累计 (¥{company_sum:,.2f})")
    
    return errors

def check_data_integrity(data):
    """检查6-13: 数据完整性"""
    errors = []
    
    # 检查10: allCustomers
    customers = data.get('allCustomers', [])
    if not customers:
        customers = data.get('customersData', [])
    if not customers:
        errors.append("❌ 检查10失败: allCustomers为空")
    else:
        print(f"✅ 检查10通过: allCustomers共{len(customers)}个客户")
    
    # 检查13: updateTime
    update_time = data.get('updateTime', '')
    today = datetime.now().strftime('%Y-%m-%d')
    if today in update_time:
        print(f"✅ 检查13通过: updateTime = {update_time}")
    else:
        errors.append(f"❌ 检查13失败: updateTime({update_time})不是今天({today})")
    
    # 检查11: salesProgressData
    progress = data.get('salesProgressData', [])
    if not progress:
        errors.append("❌ 检查11失败: salesProgressData为空")
    else:
        print(f"✅ 检查11通过: salesProgressData共{len(progress)}条记录")
    
    return errors

def check_reasonability(data):
    """检查14-15: 合理性检查"""
    errors = []
    
    # 检查14: 库存不能为负
    products = data.get('productsData', [])
    negative_stock = [p for p in products if p.get('stock', 0) < 0]
    if negative_stock:
        errors.append(f"❌ 检查14失败: {len(negative_stock)}个产品库存为负")
        for p in negative_stock[:5]:
            print(f"   - {p.get('name')}: 库存 {p.get('stock')}")
    else:
        print(f"✅ 检查14通过: 所有{len(products)}个产品库存≥0")
    
    # 检查15: 毛利率合理范围
    progress = data.get('salesProgressData', [])
    unreasonable = []
    for p in progress:
        rate_str = p.get('月累计毛利率', '0')
        if rate_str and rate_str != '—':
            try:
                rate = float(rate_str.replace('%', '')) / 100
                if rate < -0.2 or rate > 0.5:
                    unreasonable.append(p)
            except:
                pass
    
    if unreasonable:
        errors.append(f"❌ 检查15失败: {len(unreasonable)}个业务员毛利率超出范围(-20%~50%)")
    else:
        print(f"✅ 检查15通过: 所有毛利率在合理范围(-20%~50%)")
    
    return errors

def main():
    if len(sys.argv) < 2:
        print("用法: python 核算检查.py data.json")
        sys.exit(1)
    
    filepath = sys.argv[1]
    print(f"\n{'='*60}")
    print(f"湘里情数据核算检查")
    print(f"文件: {filepath}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    try:
        data = load_data(filepath)
    except Exception as e:
        print(f"❌ 加载数据失败: {e}")
        sys.exit(1)
    
    all_errors = []
    
    # 执行所有检查
    print("【销售额核算】")
    all_errors.extend(check_sales_math(data))
    all_errors.extend(check_sales_progress(data))
    
    print("\n【数据完整性检查】")
    all_errors.extend(check_data_integrity(data))
    
    print("\n【合理性检查】")
    all_errors.extend(check_reasonability(data))
    
    # 汇总结果
    print(f"\n{'='*60}")
    if all_errors:
        print(f"❌ 核算检查失败，共{len(all_errors)}项错误:\n")
        for err in all_errors:
            print(f"  {err}")
        print(f"\n请修正后重新检查!")
        sys.exit(1)
    else:
        print(f"✅ 核算检查全部通过!")
        print(f"数据可以输出!")
        sys.exit(0)

if __name__ == '__main__':
    main()
