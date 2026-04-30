#!/usr/bin/env python3
"""
将data_core.json嵌入index.html
用法: python3 embed_data.py
"""
import json
import re
import os

def fix_infinity(obj):
    """修复JSON中的Infinity值"""
    if isinstance(obj, dict):
        return {k: fix_infinity(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [fix_infinity(v) for v in obj]
    elif isinstance(obj, float) and obj == float('inf'):
        return 0
    return obj

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_file = os.path.join(base_dir, 'data_core.json')
    html_file = os.path.join(base_dir, 'index.html')
    
    # 读取数据
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 修复Infinity
    data = fix_infinity(data)
    
    # 读取HTML
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # 嵌入数据
    data_str = json.dumps(data, ensure_ascii=False, indent=2)
    
    # 查找并替换DATA定义
    pattern = r'const DATA\s*=\s*\{.*?\n\};'
    match = re.search(pattern, html, re.DOTALL)
    if match:
        new_html = html[:match.start()] + f'const DATA = {data_str};' + html[match.end():]
    else:
        new_html = html.replace('<script>', f'<script>const DATA = {data_str};', 1)
    
    # 保存
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(new_html)
    
    print(f"数据已嵌入: {html_file}")
    print(f"文件大小: {os.path.getsize(html_file) / 1024:.1f} KB")
    print(f"数据日期: {data.get('dailyReportData', {}).get('date')}")

if __name__ == '__main__':
    main()
