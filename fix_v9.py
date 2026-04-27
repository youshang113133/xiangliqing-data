#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import json

# 读取V6文件
with open('湘里情智营·客户决策_v4_4月任务_V6.html', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

print(f'原始文件大小: {len(content.encode())/1024/1024:.2f} MB')

# ===== 修复1: 月累计销售额 662万 -> 728万 =====
# 查找 dailyReportData 中的月累计销售额
old_sales = '"月累计": 6624409.14'
new_sales = '"月累计": 7288600'
if old_sales in content:
    content = content.replace(old_sales, new_sales)
    print('✅ 修复1: 月累计销售额 662万 -> 728万')
else:
    # 尝试其他格式
    old_sales2 = '6624409.14'
    if old_sales2 in content:
        content = content.replace(old_sales2, '7288600')
        print('✅ 修复1: 月累计销售额 (数字格式)')

# ===== 修复2: 找到并修改TOP10客户表格 =====
# 先查找TOP10相关的函数
print('\n搜索TOP10函数...')

# 搜索 renderTaskTop10 相关函数
func_match = re.search(r'function renderTaskTop10Customers\(managerName\)\s*\{([^}]+)\}', content, re.DOTALL)
if func_match:
    old_func = func_match.group(0)
    print('找到 renderTaskTop10Customers 函数')
    
    # 检查函数里是否有 monthly_amount 或表格形式
    if 'monthly_amount' in old_func or '<table' in old_func:
        print('  这是表格形式的TOP10，需要添加件数列')
        
        # 替换表头
        old_headers = "['排名', '客户名称', '月销售额', '日销售额']"
        new_headers = "['排名', '客户名称', '月销售额', '件数目标', '件数完成', '日销售额']"
        if old_headers in old_func:
            new_func = old_func.replace(old_headers, new_headers)
            print('  ✅ 更新了表头')
            
            # 替换表格行渲染
            old_row = '''<td class="amount">¥${data.monthly_amount.toLocaleString()}</td>
            <td class="amount">¥${data.daily_amount.toLocaleString()}</td>'''
            new_row = '''<td class="amount">¥${data.monthly_amount.toLocaleString()}</td>
            <td class="amount">${data.monthly_qty_target || 0}</td>
            <td class="amount">${data.monthly_qty_complete || 0}</td>
            <td class="amount">¥${data.daily_amount.toLocaleString()}</td>'''
            if old_row in new_func:
                new_func = new_func.replace(old_row, new_row)
                print('  ✅ 更新了表格行')
            
            content = content.replace(old_func, new_func)
    else:
        print('  这是列表形式的TOP10，跳过')

# ===== 修复3: 确保 taskRecommendCard 容器存在 =====
print('\n检查推荐容器...')
if 'id="taskRecommendCard"' not in content:
    # 查找 taskRecommendList 容器
    old_rec = '<div class="card-body" id="taskRecommendList">'
    new_rec = '<div class="card-body" id="taskRecommendCard"><div id="taskRecommendList">'
    if old_rec in content:
        content = content.replace(old_rec, new_rec)
        print('✅ 修复3: 添加了 taskRecommendCard 容器')
        
        # 同时需要关闭这个容器，找到按钮后面的位置
        old_close = '''<button class="btn btn-primary" style="width: 100%; margin-top: 10px;">查看全部推荐</button>
            </div>
        </div>
    </div>
</div>'''
        new_close = '''<button class="btn btn-primary" style="width: 100%; margin-top: 10px;">查看全部推荐</button>
                </div>
            </div>
        </div>
    </div>
</div>'''
        if old_close in content:
            content = content.replace(old_close, new_close)
            print('✅ 修复3: 关闭了容器标签')
else:
    print('  taskRecommendCard 已存在')

# ===== 修复4: 移除重复的函数定义 =====
print('\n检查重复函数...')
func_count = len(re.findall(r'function renderTaskTop10Customers', content))
if func_count > 1:
    print(f'  发现 {func_count} 个 renderTaskTop10Customers 函数定义')
    # 找到第一个函数的结束位置
    funcs = list(re.finditer(r'function renderTaskTop10Customers\s*\([^)]*\)\s*\{[^}]*\}', content))
    if len(funcs) > 1:
        # 移除后面的重复定义
        for m in funcs[1:]:
            content = content[:m.start()] + content[m.end():]
        print('  ✅ 移除了重复的函数定义')

# ===== 保存文件 =====
output_file = '湘里情智营·客户决策_v4_4月任务_V9_20260422.html'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(content)

final_size = len(content.encode())
print(f'\n✅ V9修复完成！')
print(f'输出文件: {output_file}')
print(f'文件大小: {final_size/1024/1024:.2f} MB')

# 验证修复
print('\n验证修复:')
print('  月销售额728万:', '7288600' in content)
print('  件数目标列:', '件数目标' in content)
print('  件数完成列:', '件数完成' in content)
print('  monthly_qty_target:', 'monthly_qty_target' in content)
print('  taskRecommendCard:', 'id="taskRecommendCard"' in content)
