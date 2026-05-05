#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T+系统数据抓取脚本
湘里情智营·客户决策系统

功能说明：
1. 从T+系统获取每日销售数据
2. 解析并整理销售明细
3. 更新GitHub仓库中的JSON数据文件
4. 支持每日定时执行

使用方式：
1. 手动执行：python3 tplus_fetch.py
2. 定时执行：配合cron配置每日8点执行

依赖安装：
pip install requests schedule python-git
"""

import json
import os
import sys
import datetime
import subprocess
from pathlib import Path

# ==================== 配置区域 ====================
GITHUB_REPO = "xiangliqing888/xiangliqing-data"
GITHUB_BRANCH = "main"
DATA_DIR = Path(__file__).parent

# Git配置
GIT_EMAIL = "bot@xiangliqing.com"
GIT_NAME = "XLQ Bot"

# T+ 系统配置（需要根据实际T+系统配置）
TPLUS_CONFIG = {
    "api_url": "http://your-tplus-server/api",
    "app_key": "your_app_key",
    "app_secret": "your_app_secret",
    "account": "your_account_code"
}

# ==================== 功能函数 ====================

def log(msg):
    """日志输出"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}")

def get_tplus_token():
    """获取T+系统访问令牌"""
    import requests
    
    try:
        url = f"{TPLUS_CONFIG['api_url']}/auth/login"
        data = {
            "app_key": TPLUS_CONFIG['app_key'],
            "app_secret": TPLUS_CONFIG['app_secret'],
            "account": TPLUS_CONFIG['account']
        }
        response = requests.post(url, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get('token')
    except Exception as e:
        log(f"获取Token失败: {e}")
    return None

def fetch_daily_sales(token, date=None):
    """
    从T+系统获取指定日期的销售数据
    
    参数:
        token: T+访问令牌
        date: 查询日期，格式YYYY-MM-DD，默认昨天
    
    返回:
        销售数据列表
    """
    import requests
    
    if date is None:
        date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    try:
        url = f"{TPLUS_CONFIG['api_url']}/report/sales_detail"
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "date_from": date,
            "date_to": date,
            "doc_type": "SA"  # 销货单
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=60)
        if response.status_code == 200:
            return response.json().get('data', [])
    except Exception as e:
        log(f"获取销售数据失败: {e}")
    return []

def parse_sales_records(raw_data):
    """
    解析销售数据
    
    参数:
        raw_data: 原始销售数据
    
    返回:
        整理后的销售数据
    """
    records = []
    
    for item in raw_data:
        record = {
            "date": item.get("voucherDate", "")[:10],
            "doc_no": item.get("docNo", ""),
            "customer_code": item.get("customerCode", ""),
            "customer": item.get("customerName", ""),
            "department": item.get("departmentName", ""),
            "salesman": item.get("salesmanName", ""),
            "product_code": item.get("inventoryCode", ""),
            "product": item.get("inventoryName", ""),
            "spec": item.get("invSC", ""),
            "warehouse": item.get("warehouseName", ""),
            "unit": item.get("unitName", ""),
            "quantity": float(item.get("quantity", 0)),
            "price": float(item.get("price", 0)),
            "amount": float(item.get("amount", 0)),
            "tax_amount": float(item.get("taxAmount", 0))
        }
        records.append(record)
    
    return records

def calculate_summary(records):
    """计算销售汇总数据"""
    if not records:
        return {
            "total_records": 0,
            "total_amount": 0,
            "total_tax": 0,
            "total_quantity": 0,
            "salesmen": []
        }
    
    total_amount = sum(r['amount'] for r in records)
    total_tax = sum(r['tax_amount'] for r in records)
    total_quantity = sum(r['quantity'] for r in records)
    
    # 统计各业务员销售额
    sales_by_salesman = {}
    for r in records:
        name = r['salesman']
        if name not in sales_by_salesman:
            sales_by_salesman[name] = 0
        sales_by_salesman[name] += r['amount']
    
    # 按销售额排序
    top_salesmen = sorted(sales_by_salesman.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "total_records": len(records),
        "total_amount": round(total_amount, 2),
        "total_tax": round(total_tax, 2),
        "total_quantity": round(total_quantity, 2),
        "salesmen": [name for name, _ in top_salesmen[:5]]
    }

def save_daily_data(date, records, summary):
    """保存每日销售数据到JSON文件"""
    filename = DATA_DIR / f"daily_sales_{date.replace('-', '')}.json"
    
    data = {
        "date": date,
        "summary": summary,
        "records": records
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    log(f"已保存数据到: {filename}")
    return filename

def update_main_data():
    """更新主数据文件"""
    # 读取所有daily_sales文件，合并到data.json
    daily_files = sorted(DATA_DIR.glob("daily_sales_*.json"))
    
    all_records = []
    for f in daily_files[-30:]:  # 最近30天数据
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                all_records.extend(data.get('records', []))
        except:
            continue
    
    # 读取现有data.json
    data_file = DATA_DIR / "data.json"
    if data_file.exists():
        with open(data_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    else:
        existing_data = {"records": []}
    
    # 合并数据（去重）
    existing_doc_nos = {r['doc_no'] for r in existing_data.get('records', [])}
    new_records = [r for r in all_records if r['doc_no'] not in existing_doc_nos]
    
    if new_records:
        existing_data['records'].extend(new_records)
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False)
        log(f"更新data.json，新增{len(new_records)}条记录")
    else:
        log("data.json已是最新，无需更新")

def update_daily_update_file(date, summary):
    """更新daily_update.json"""
    update_file = DATA_DIR / "daily_update.json"
    
    data = {
        "date": date,
        "update_time": datetime.datetime.now().strftime("%H:%M"),
        "当日销售额": summary['total_amount'],
        "税额": summary['total_tax'],
        "记录数": summary['total_records'],
        "总数量": summary['total_quantity'],
        "主要业务员": summary['salesmen'],
        "状态": "数据已更新",
        "月累计销售额": calculate_month_total(date)
    }
    
    with open(update_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    log(f"更新daily_update.json")

def calculate_month_total(date):
    """计算当月累计销售额"""
    month_str = date[:7].replace('-', '')
    month_files = sorted(DATA_DIR.glob(f"daily_sales_{month_str}*.json"))
    
    total = 0
    for f in month_files:
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                total += data['summary']['total_amount']
        except:
            continue
    
    return round(total, 2)

def git_commit_and_push(date):
    """提交更改到GitHub"""
    try:
        # 配置Git
        subprocess.run(["git", "config", "user.email", GIT_EMAIL], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", GIT_NAME], check=True, capture_output=True)
        
        # 添加文件
        subprocess.run(["git", "add", "daily_sales_*.json", "daily_update.json", "data.json"], check=True, capture_output=True)
        
        # 检查是否有更改
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not result.stdout.strip():
            log("没有新的数据更新，跳过提交")
            return False
        
        # 提交
        commit_msg = f"📊 数据更新 {date}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)
        
        # 推送
        subprocess.run(["git", "push", "origin", GITHUB_BRANCH], check=True, capture_output=True)
        log("已推送更新到GitHub")
        return True
        
    except subprocess.CalledProcessError as e:
        log(f"Git操作失败: {e}")
        return False

def run_fetch(date=None):
    """执行数据抓取主流程"""
    log("=" * 50)
    log("开始T+数据抓取")
    log("=" * 50)
    
    if date is None:
        date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Step 1: 获取Token
    log("Step 1: 获取T+访问令牌...")
    token = get_tplus_token()
    if not token:
        log("❌ 无法获取访问令牌，请检查T+系统配置")
        return False
    
    # Step 2: 获取销售数据
    log(f"Step 2: 获取 {date} 销售数据...")
    raw_data = fetch_daily_sales(token, date)
    if not raw_data:
        log("⚠️ 今日无销售数据或获取失败")
        return False
    
    # Step 3: 解析数据
    log("Step 3: 解析销售数据...")
    records = parse_sales_records(raw_data)
    summary = calculate_summary(records)
    log(f"获取到 {len(records)} 条销售记录")
    
    # Step 4: 保存数据
    log("Step 4: 保存数据文件...")
    save_daily_data(date, records, summary)
    update_daily_update_file(date, summary)
    update_main_data()
    
    # Step 5: 提交到GitHub
    log("Step 5: 提交到GitHub...")
    git_commit_and_push(date)
    
    log("=" * 50)
    log("数据抓取完成!")
    log("=" * 50)
    return True

# ==================== 手动执行入口 ====================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="T+数据抓取脚本")
    parser.add_argument("--date", "-d", help="指定日期 (YYYY-MM-DD)", default=None)
    parser.add_argument("--test", "-t", action="store_true", help="测试模式，不提交到GitHub")
    args = parser.parse_args()
    
    result = run_fetch(args.date)
    sys.exit(0 if result else 1)
