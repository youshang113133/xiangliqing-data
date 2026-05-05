#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T+系统数据抓取脚本 (浏览器自动化版)
湘里情智营·客户决策系统

功能说明：
1. 使用Playwright浏览器自动化登录T+系统
2. 抓取每日销售明细数据
3. 解析并整理销售明细
4. 更新GitHub仓库中的JSON数据文件
5. 支持每日定时执行

使用方式：
1. 手动执行：python3 tplus_fetch.py
2. 指定日期：python3 tplus_fetch.py --date 2026-05-01
3. 测试模式：python3 tplus_fetch.py --test

环境变量配置：
- TPLUS_URL: T+系统地址 (默认: http://124.232.133.77/tplus)
- TPLUS_USERNAME: 用户名
- TPLUS_PASSWORD: 密码
- TPLUS_ACCOUNT: 账套名称 (默认: 湖南湘里情农业科技有限公司)
"""

import json
import os
import sys
import datetime
import subprocess
import argparse
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

# ==================== 日志配置 ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ==================== 配置区域 ====================
GITHUB_REPO = "xiangliqing888/xiangliqing-data"
GITHUB_BRANCH = "main"
DATA_DIR = Path(__file__).parent

# Git配置
GIT_EMAIL = "bot@xiangliqing.com"
GIT_NAME = "XLQ Bot"

# T+系统配置（从环境变量读取）
TPLUS_CONFIG = {
    "url": os.environ.get("TPLUS_URL", "http://124.232.133.77/tplus"),
    "username": os.environ.get("TPLUS_USERNAME", ""),
    "password": os.environ.get("TPLUS_PASSWORD", ""),
    "account": os.environ.get("TPLUS_ACCOUNT", "湖南湘里情农业科技有限公司")
}


def log(msg: str):
    """日志输出"""
    logger.info(msg)


def log_error(msg: str):
    """错误日志输出"""
    logger.error(msg)


def log_warn(msg: str):
    """警告日志输出"""
    logger.warning(msg)


def check_config():
    """检查配置是否完整"""
    missing = []
    if not TPLUS_CONFIG["username"]:
        missing.append("TPLUS_USERNAME")
    if not TPLUS_CONFIG["password"]:
        missing.append("TPLUS_PASSWORD")
    
    if missing:
        log_error(f"缺少必需的环境变量: {', '.join(missing)}")
        log("请设置环境变量或在config.json中配置")
        return False
    return True


def load_config_from_file():
    """从config.json加载配置（如果存在）"""
    config_file = DATA_DIR / "config.json"
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                for key in TPLUS_CONFIG:
                    if key in config and TPLUS_CONFIG[key] == "":
                        TPLUS_CONFIG[key] = config[key]
                    elif key in config:
                        # 命令行环境变量优先
                        pass
        except Exception as e:
            log_warn(f"加载配置文件失败: {e}")


def get_playwright():
    """获取Playwright实例"""
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright().start()
    except ImportError:
        log_error("Playwright未安装，请运行: pip install playwright && playwright install chromium")
        return None
    except Exception as e:
        log_error(f"启动Playwright失败: {e}")
        return None


def login_tplus(playwright, page):
    """
    登录T+系统
    
    参数:
        playwright: Playwright实例
        page: 页面对象
    
    返回:
        登录是否成功
    """
    try:
        login_url = f"{TPLUS_CONFIG['url']}/view/login.html"
        log(f"打开登录页面: {login_url}")
        page.goto(login_url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000)
        
        # 截图保存登录页面状态
        page.screenshot(path=str(DATA_DIR / "debug_login.png"))
        log("已保存登录页面截图")
        
        # 获取页面元素
        page.wait_for_timeout(2000)
        
        # 尝试多种登录方式
        login_success = False
        
        # 方式1: 标准登录表单
        try:
            # 查找用户名输入框
            username_selectors = [
                'input[name="username"]',
                'input[id="username"]',
                'input[placeholder*="用户"]',
                'input[type="text"]',
                '#username',
                '.username input'
            ]
            
            username_input = None
            for selector in username_selectors:
                try:
                    username_input = page.wait_for_selector(selector, timeout=3000)
                    if username_input:
                        log(f"找到用户名输入框: {selector}")
                        break
                except:
                    continue
            
            if username_input:
                username_input.fill(TPLUS_CONFIG["username"])
                page.wait_for_timeout(500)
                
                # 查找密码输入框
                password_selectors = [
                    'input[name="password"]',
                    'input[id="password"]',
                    'input[type="password"]',
                    '#password',
                    '.password input'
                ]
                
                password_input = None
                for selector in password_selectors:
                    try:
                        password_input = page.wait_for_selector(selector, timeout=3000)
                        if password_input:
                            log(f"找到密码输入框: {selector}")
                            break
                    except:
                        continue
                
                if password_input:
                    password_input.fill(TPLUS_CONFIG["password"])
                    page.wait_for_timeout(500)
                    
                    # 查找登录按钮
                    login_btn_selectors = [
                        'button[type="submit"]',
                        'input[type="submit"]',
                        'button:has-text("登录")',
                        'a:has-text("登录")',
                        '.login-btn',
                        '#loginBtn'
                    ]
                    
                    login_btn = None
                    for selector in login_btn_selectors:
                        try:
                            login_btn = page.wait_for_selector(selector, timeout=3000)
                            if login_btn:
                                log(f"找到登录按钮: {selector}")
                                break
                        except:
                            continue
                    
                    if login_btn:
                        login_btn.click()
                        page.wait_for_timeout(5000)
                        
                        # 处理"当前用户已登录"弹窗 - 使用更可靠的方式
                        try:
                            # 等待弹窗出现
                            page.wait_for_timeout(2000)
                            
                            # 查找确定按钮
                            confirm_btns = [
                                'button:has-text("确定")',
                                '.t-dialog-btn-primary',
                                '.dialog-btn-primary',
                                '[class*="confirm"]',
                                '[class*="primary"]'
                            ]
                            
                            for btn_selector in confirm_btns:
                                try:
                                    confirm_btn = page.query_selector(btn_selector)
                                    if confirm_btn and confirm_btn.is_visible():
                                        log("检测到弹窗，点击确定")
                                        confirm_btn.click()
                                        page.wait_for_timeout(3000)
                                        break
                                except:
                                    continue
                        except Exception as e:
                            log_warn(f"处理弹窗时出错: {e}")
                        
                        login_success = True
        except Exception as e:
            log_warn(f"方式1登录失败: {e}")
        
        # 方式2: 直接通过URL参数
        if not login_success:
            try:
                # 尝试直接访问带认证的URL
                direct_url = f"{TPLUS_CONFIG['url']}/view/main.html"
                page.goto(direct_url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(2000)
                
                # 检查是否已登录
                if "login" not in page.url.lower():
                    login_success = True
            except Exception as e:
                log_warn(f"方式2登录失败: {e}")
        
        if login_success:
            log("✓ 登录成功")
            page.screenshot(path=str(DATA_DIR / "debug_after_login.png"))
            return True
        else:
            log_error("✗ 登录失败，无法找到登录表单")
            # 保存页面HTML用于调试
            with open(DATA_DIR / "debug_page.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            return False
            
    except Exception as e:
        log_error(f"登录过程出错: {e}")
        page.screenshot(path=str(DATA_DIR / "debug_error.png"))
        return False


def select_account(page, account_name: str):
    """
    选择账套
    
    参数:
        page: 页面对象
        account_name: 账套名称
    
    返回:
        选择是否成功
    """
    try:
        page.wait_for_timeout(2000)
        
        # 查找账套选择器
        account_selectors = [
            f'text="{account_name}"',
            f'a:has-text("{account_name}")',
            f'div:has-text("{account_name}")',
            f'span:has-text("{account_name}")'
        ]
        
        for selector in account_selectors:
            try:
                elements = page.query_selector_all(selector)
                for element in elements:
                    text = element.inner_text()
                    if account_name in text:
                        log(f"找到账套选项: {text[:50]}...")
                        element.click()
                        page.wait_for_timeout(2000)
                        log("✓ 账套选择成功")
                        return True
            except:
                continue
        
        log_warn(f"未找到账套 '{account_name}'，可能已自动选择")
        return True
        
    except Exception as e:
        log_warn(f"选择账套时出错: {e}")
        return True  # 继续执行


def navigate_to_sales_page(page):
    """
    导航到销售明细页面
    
    参数:
        page: 页面对象
    
    返回:
        导航是否成功
    """
    try:
        log("等待页面加载...")
        page.wait_for_timeout(3000)
        
        nav_success = False
        
        # 方式1: 通过JavaScript点击销售管理菜单并选择销货单
        log("尝试方式1: JavaScript点击销售管理菜单...")
        
        try:
            # 查找并点击"销售管理"一级菜单
            clicked = page.evaluate("""
                () => {
                    // 查找包含"销售管理"文本的元素
                    const menus = document.querySelectorAll('.menu-text, .menu-first-content, [class*="menu"] span');
                    for (const menu of menus) {
                        if (menu.innerText && menu.innerText.includes('销售管理')) {
                            menu.click();
                            return '点击了: ' + menu.innerText;
                        }
                    }
                    return null;
                }
            """)
            if clicked:
                log(clicked)
                page.wait_for_timeout(2000)
                
                # 展开后，查找并点击"明细表"或"销货单"
                clicked = page.evaluate("""
                    () => {
                        // 查找包含"明细表"或"销货单"的元素
                        const elements = document.querySelectorAll('a, [class*="menu"], [class*="submenu"] span');
                        for (const el of elements) {
                            const text = el.innerText || '';
                            if (text.includes('明细表') || text.includes('销货单')) {
                                // 检查父元素是否可见
                                const parent = el.closest('[class*="show"], [class*="active"], .submenu');
                                if (parent || el.offsetParent !== null) {
                                    el.click();
                                    return '点击了: ' + text.substring(0, 30);
                                }
                            }
                        }
                        return null;
                    }
                """)
                if clicked:
                    log(f"子菜单: {clicked}")
                    page.wait_for_timeout(3000)
                    nav_success = True
        except Exception as e:
            log_warn(f"方式1失败: {e}")
        
        # 方式2: 直接点击链接
        if not nav_success:
            log("尝试方式2: 查找销售相关链接...")
            try:
                # 查找所有销售相关的a标签
                sales_links = page.query_selector_all('a[href*="sale"], a[href*="SA"], a[alltitle*="销售"]')
                for link in sales_links[:10]:
                    text = link.inner_text()
                    href = link.get_attribute('href') or ''
                    log(f"  找到: {text[:30]} -> {href[:50]}")
            except Exception as e:
                log_warn(f"查找链接失败: {e}")
        
        # 方式3: 使用code属性导航 (T+系统的菜单code)
        log("尝试方式3: 使用code属性导航...")
        try:
            # 尝试常见的销售报表code
            sale_codes = ['SA01', 'SA', 'Sell', '#SA', '#SA01']
            for code in sale_codes:
                result = page.evaluate(f"""
                    () => {{
                        const el = document.querySelector('[code*="SA"], [code*="sell"], [code*="Sale"]');
                        if (el) {{
                            const text = el.innerText || el.getAttribute('alltitle') || '';
                            return {{code: el.getAttribute('code'), text: text.substring(0, 30)}};
                        }}
                        return null;
                    }}
                """)
                if result:
                    log(f"找到菜单项: code={result['code']}, text={result['text']}")
        except Exception as e:
            log_warn(f"方式3失败: {e}")
        
        # 方式4: 尝试直接访问URL
        log("尝试方式4: 直接访问销售页面URL...")
        sales_urls = [
            f"{TPLUS_CONFIG['url']}/view/sa/salist.html",
            f"{TPLUS_CONFIG['url']}/view/sale/salist.html",
            f"{TPLUS_CONFIG['url']}/view/sale/deliverlist.html",
            f"{TPLUS_CONFIG['url']}/view/sa/deliverlist.html",
            f"{TPLUS_CONFIG['url']}/view/sa/salereport.html"
        ]
        
        for url in sales_urls:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=10000)
                page.wait_for_timeout(2000)
                
                # 检查是否加载成功
                url = page.url
                content = page.content()
                if "login" not in url.lower() and len(content) > 5000:
                    log(f"✓ 访问成功: {url}")
                    nav_success = True
                    break
            except Exception as e:
                continue
        
        if nav_success:
            log("✓ 进入销售页面成功")
            page.screenshot(path=str(DATA_DIR / "debug_sales_page.png"))
        else:
            log_warn("未能导航到销售页面，尝试从当前页面提取数据")
            
        return True
            
    except Exception as e:
        log_warn(f"导航到销售页面时出错: {e}")
        return True


def fetch_sales_data(page, date: str) -> List[Dict[str, Any]]:
    """
    从T+系统获取指定日期的销售数据
    
    参数:
        page: 页面对象
        date: 查询日期，格式YYYY-MM-DD
    
    返回:
        销售数据列表
    """
    records = []
    
    try:
        log(f"尝试获取 {date} 的销售数据...")
        
        # 设置日期筛选条件
        date_inputs = [
            'input[placeholder*="日期"]',
            'input[id*="date"]',
            'input[name*="date"]',
            '.date-picker input',
            '.datepicker input'
        ]
        
        for selector in date_inputs:
            try:
                date_input = page.wait_for_selector(selector, timeout=2000)
                if date_input:
                    # 清除并输入日期
                    date_input.click()
                    page.wait_for_timeout(500)
                    date_input.fill(date)
                    page.wait_for_timeout(1000)
                    log(f"已设置查询日期: {date}")
                    break
            except:
                continue
        
        # 点击查询按钮
        query_buttons = [
            'button:has-text("查询")',
            'button:has-text("搜索")',
            'a:has-text("查询")',
            '#queryBtn',
            '.query-btn'
        ]
        
        for selector in query_buttons:
            try:
                query_btn = page.wait_for_selector(selector, timeout=2000)
                if query_btn:
                    query_btn.click()
                    page.wait_for_timeout(3000)
                    log("已点击查询按钮")
                    break
            except:
                continue
        
        # 等待数据加载
        page.wait_for_timeout(3000)
        
        # 提取表格数据
        page.screenshot(path=str(DATA_DIR / "debug_data_table.png"))
        
        # 尝试多种表格选择器
        table_selectors = [
            'table',
            '.data-table',
            '.grid-table',
            '#dataTable',
            '[role="grid"]'
        ]
        
        for selector in table_selectors:
            try:
                table = page.wait_for_selector(selector, timeout=3000)
                if table:
                    rows = table.query_selector_all('tr')
                    log(f"找到表格，共 {len(rows)} 行")
                    
                    # 解析表头
                    headers = []
                    header_row = rows[0] if rows else None
                    if header_row:
                        header_cells = header_row.query_selector_all('th, td')
                        for cell in header_cells:
                            headers.append(cell.inner_text().strip())
                    
                    log(f"表头: {headers[:10]}...")
                    
                    # 解析数据行
                    for i, row in enumerate(rows[1:], start=1):
                        cells = row.query_selector_all('td')
                        if len(cells) >= 3:
                            record = {}
                            for j, cell in enumerate(cells):
                                if j < len(headers):
                                    record[headers[j]] = cell.inner_text().strip()
                            if record:
                                records.append(record)
                    
                    if records:
                        log(f"成功提取 {len(records)} 条数据")
                        break
            except:
                continue
        
        # 如果没有找到表格，尝试JavaScript提取
        if not records:
            log("尝试通过JavaScript提取数据...")
            try:
                js_result = page.evaluate("""
                    () => {
                        // 尝试多种方式获取数据
                        let data = [];
                        
                        // 方式1: 从DataGrid
                        const grids = document.querySelectorAll('[class*="datagrid"], [class*="grid"]');
                        grids.forEach(grid => {
                            const rows = grid.querySelectorAll('tr');
                            rows.forEach(row => {
                                const cells = row.querySelectorAll('td');
                                if (cells.length > 0) {
                                    const rowData = Array.from(cells).map(c => c.innerText);
                                    data.push(rowData);
                                }
                            });
                        });
                        
                        // 方式2: 从表格
                        const tables = document.querySelectorAll('table tbody tr');
                        tables.forEach(row => {
                            const cells = row.querySelectorAll('td');
                            if (cells.length > 0) {
                                const rowData = Array.from(cells).map(c => c.innerText);
                                data.push(rowData);
                            }
                        });
                        
                        return data;
                    }
                """)
                if js_result and len(js_result) > 0:
                    log(f"通过JavaScript提取到 {len(js_result)} 行数据")
            except Exception as e:
                log_warn(f"JavaScript提取失败: {e}")
        
    except Exception as e:
        log_error(f"获取销售数据时出错: {e}")
    
    return records


def parse_sales_records(raw_data: List[Dict], date: str) -> List[Dict[str, Any]]:
    """
    解析销售数据
    
    参数:
        raw_data: 原始销售数据
        date: 数据日期
    
    返回:
        整理后的销售数据
    """
    records = []
    
    # 字段映射
    field_mapping = {
        '单据编号': 'doc_no',
        '单号': 'doc_no',
        '日期': 'date',
        '单据日期': 'date',
        '客户编码': 'customer_code',
        '客户': 'customer',
        '客户名称': 'customer',
        '部门': 'department',
        '部门名称': 'department',
        '业务员': 'salesman',
        '业务员名称': 'salesman',
        '商品编码': 'product_code',
        '存货编码': 'product_code',
        '商品': 'product',
        '商品名称': 'product',
        '存货名称': 'product',
        '规格': 'spec',
        '规格型号': 'spec',
        '单位': 'unit',
        '数量': 'quantity',
        '单价': 'price',
        '金额': 'amount',
        '不含税金额': 'amount',
        '税额': 'tax_amount'
    }
    
    for idx, item in enumerate(raw_data, start=1):
        record = {
            "id": idx,
            "date": date
        }
        
        for key, value in item.items():
            mapped_key = field_mapping.get(key, key)
            if mapped_key in ['quantity', 'price', 'amount', 'tax_amount']:
                try:
                    # 处理数字格式
                    value_str = str(value).replace(',', '').replace('¥', '')
                    record[mapped_key] = float(value_str) if value_str else 0
                except:
                    record[mapped_key] = value
            else:
                record[mapped_key] = str(value)
        
        # 如果没有单据编号，生成一个
        if 'doc_no' not in record or not record['doc_no']:
            record['doc_no'] = f"SA-{date.replace('-', '')}-{str(idx).zfill(4)}"
        
        records.append(record)
    
    return records


def parse_sales_records_from_text(raw_data: List[Dict], date: str) -> List[Dict[str, Any]]:
    """
    从文本格式的原始数据解析销售记录
    
    参数:
        raw_data: 原始销售数据（列表格式）
        date: 数据日期
    
    返回:
        整理后的销售数据
    """
    records = []
    
    # 字段索引（需要根据实际表格结构调整）
    field_indices = {
        0: 'doc_no',      # 单据编号
        1: 'customer',    # 客户
        2: 'department',  # 部门
        3: 'salesman',    # 业务员
        4: 'product',     # 商品
        5: 'spec',        # 规格
        6: 'warehouse',   # 仓库
        7: 'unit',        # 单位
        8: 'quantity',    # 数量
        9: 'price',       # 单价
        10: 'amount',     # 金额
    }
    
    for idx, row_data in enumerate(raw_data):
        if isinstance(row_data, list) and len(row_data) > 5:
            record = {
                "id": idx + 1,
                "date": date
            }
            
            for col_idx, field_name in field_indices.items():
                if col_idx < len(row_data):
                    value = str(row_data[col_idx]).strip()
                    if field_name in ['quantity', 'price', 'amount']:
                        try:
                            value = float(value.replace(',', '').replace('¥', ''))
                        except:
                            value = 0
                    record[field_name] = value
            
            # 生成单据编号
            if 'doc_no' not in record or not record['doc_no']:
                record['doc_no'] = f"SA-{date.replace('-', '')}-{str(idx + 1).zfill(4)}"
            
            records.append(record)
    
    return records


def calculate_summary(records: List[Dict]) -> Dict[str, Any]:
    """计算销售汇总数据"""
    if not records:
        return {
            "total_records": 0,
            "total_amount": 0,
            "total_tax": 0,
            "total_quantity": 0,
            "salesmen": []
        }
    
    total_amount = sum(r.get('amount', 0) for r in records)
    total_tax = sum(r.get('tax_amount', 0) for r in records)
    total_quantity = sum(r.get('quantity', 0) for r in records)
    
    # 统计各业务员销售额
    sales_by_salesman = {}
    for r in records:
        name = r.get('salesman', '未知')
        if name not in sales_by_salesman:
            sales_by_salesman[name] = 0
        sales_by_salesman[name] += r.get('amount', 0)
    
    # 按销售额排序
    top_salesmen = sorted(sales_by_salesman.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "total_records": len(records),
        "total_amount": round(total_amount, 2),
        "total_tax": round(total_tax, 2),
        "total_quantity": round(total_quantity, 2),
        "salesmen": [name for name, _ in top_salesmen[:5]]
    }


def save_daily_data(date: str, records: List[Dict], summary: Dict) -> Path:
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


def update_main_data() -> int:
    """更新主数据文件"""
    daily_files = sorted(DATA_DIR.glob("daily_sales_*.json"))
    
    all_records = []
    for f in daily_files[-30:]:
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                all_records.extend(data.get('records', []))
        except:
            continue
    
    data_file = DATA_DIR / "data.json"
    if data_file.exists():
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                if 'records' not in existing_data:
                    existing_data = {"records": existing_data.get('data', [])}
        except:
            existing_data = {"records": []}
    else:
        existing_data = {"records": []}
    
    existing_doc_nos = {r.get('doc_no', '') for r in existing_data.get('records', [])}
    new_records = [r for r in all_records if r.get('doc_no', '') not in existing_doc_nos]
    
    if new_records:
        existing_data['records'].extend(new_records)
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False)
        log(f"更新data.json，新增{len(new_records)}条记录")
    else:
        log("data.json已是最新，无需更新")
    
    return len(new_records)


def update_daily_update_file(date: str, summary: Dict):
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


def calculate_month_total(date: str) -> float:
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


def git_commit_and_push(date: str, test_mode: bool = False) -> bool:
    """提交更改到GitHub"""
    try:
        # 配置Git
        subprocess.run(["git", "config", "user.email", GIT_EMAIL], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", GIT_NAME], check=True, capture_output=True)
        
        # 添加文件
        subprocess.run(["git", "add", "daily_sales_*.json", "daily_update.json", "data.json"], 
                       check=True, capture_output=True)
        
        # 检查是否有更改
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not result.stdout.strip():
            log("没有新的数据更新，跳过提交")
            return False
        
        if test_mode:
            log(f"[测试模式] 跳过Git提交。变更文件:\n{result.stdout}")
            return False
        
        # 提交
        commit_msg = f"📊 数据更新 {date}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)
        
        # 推送
        subprocess.run(["git", "push", "origin", GITHUB_BRANCH], check=True, capture_output=True)
        log("已推送更新到GitHub")
        return True
        
    except subprocess.CalledProcessError as e:
        log_error(f"Git操作失败: {e}")
        return False


def cleanup_debug_files():
    """清理调试文件"""
    debug_files = ['debug_login.png', 'debug_after_login.png', 'debug_sales_page.png',
                   'debug_data_table.png', 'debug_error.png', 'debug_page.html']
    for f in debug_files:
        filepath = DATA_DIR / f
        if filepath.exists():
            try:
                filepath.unlink()
            except:
                pass


def run_fetch(date: Optional[str] = None, test_mode: bool = False):
    """执行数据抓取主流程"""
    log("=" * 60)
    log("开始T+数据抓取 (浏览器自动化版)")
    log("=" * 60)
    
    # 检查配置
    load_config_from_file()
    if not check_config():
        return False
    
    # 默认日期为昨天
    if date is None:
        date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    log(f"查询日期: {date}")
    
    playwright = None
    browser = None
    context = None
    page = None
    
    try:
        # Step 1: 启动浏览器
        log("Step 1: 启动浏览器...")
        playwright = get_playwright()
        if not playwright:
            log_error("无法启动Playwright")
            return False
        
        browser = playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()
        page.set_default_timeout(60000)
        
        # Step 2: 登录T+系统
        log("Step 2: 登录T+系统...")
        if not login_tplus(playwright, page):
            return False
        
        # Step 3: 选择账套
        log("Step 3: 选择账套...")
        select_account(page, TPLUS_CONFIG["account"])
        
        # Step 4: 导航到销售页面
        log("Step 4: 导航到销售页面...")
        navigate_to_sales_page(page)
        
        # Step 5: 获取销售数据
        log("Step 5: 获取销售数据...")
        raw_data = fetch_sales_data(page, date)
        
        if not raw_data:
            log_warn("未获取到销售数据")
            # 生成模拟数据用于测试
            if test_mode:
                log("[测试模式] 生成模拟数据...")
                raw_data = generate_mock_data(date)
        
        if not raw_data:
            log_warn("今日无销售数据")
            # 即使没有数据也创建空文件
            records = []
        else:
            # Step 6: 解析数据
            log("Step 6: 解析销售数据...")
            if isinstance(raw_data[0], list):
                records = parse_sales_records_from_text(raw_data, date)
            else:
                records = parse_sales_records(raw_data, date)
        
        summary = calculate_summary(records)
        log(f"获取到 {len(records)} 条销售记录")
        log(f"当日销售额: {summary['total_amount']}")
        
        # Step 7: 保存数据
        log("Step 7: 保存数据文件...")
        save_daily_data(date, records, summary)
        update_daily_update_file(date, summary)
        new_count = update_main_data()
        
        # Step 8: 提交到GitHub
        if test_mode:
            log("Step 8: [测试模式] 跳过Git提交")
        else:
            log("Step 8: 提交到GitHub...")
            git_commit_and_push(date)
        
        # 清理调试文件
        cleanup_debug_files()
        
        log("=" * 60)
        log("数据抓取完成!")
        log("=" * 60)
        return True
        
    except Exception as e:
        log_error(f"执行过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理资源
        try:
            if page:
                page.screenshot(path=str(DATA_DIR / "debug_final.png"))
            if browser:
                browser.close()
            if playwright:
                playwright.stop()
        except:
            pass


def generate_mock_data(date: str) -> List[Dict]:
    """生成模拟数据用于测试"""
    log("生成测试用模拟数据...")
    
    mock_data = []
    
    # 生成3条测试记录
    for i in range(1, 4):
        record = {
            "单据编号": f"SA-{date.replace('-', '')}-{str(i).zfill(4)}",
            "客户": f"测试客户{i}",
            "部门": "长株潭业务部",
            "业务员": "王纯",
            "商品": f"测试商品{i}",
            "规格": "1*10包",
            "仓库": "红星仓",
            "单位": "件",
            "数量": 10 * i,
            "单价": 100,
            "金额": 1000 * i,
            "税额": 100 * i
        }
        mock_data.append(record)
    
    return mock_data


# ==================== 手动执行入口 ====================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="T+数据抓取脚本 (浏览器自动化版)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 tplus_fetch.py                    # 抓取昨日数据
  python3 tplus_fetch.py --date 2026-05-01  # 抓取指定日期
  python3 tplus_fetch.py --test             # 测试模式，不提交
  
环境变量:
  TPLUS_URL        T+系统地址
  TPLUS_USERNAME   用户名
  TPLUS_PASSWORD   密码
  TPLUS_ACCOUNT    账套名称
        """
    )
    parser.add_argument("--date", "-d", help="指定日期 (YYYY-MM-DD)", default=None)
    parser.add_argument("--test", "-t", action="store_true", help="测试模式，不提交到GitHub")
    parser.add_argument("--headless", action="store_true", default=True, help="无头模式运行浏览器")
    
    args = parser.parse_args()
    
    result = run_fetch(args.date, args.test)
    sys.exit(0 if result else 1)
