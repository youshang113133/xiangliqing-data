import json, re

# 读取原文件
with open('湘里情智营·客户决策_v2.html', 'r', encoding='utf-8') as f:
    content = f.read()

print(f'原始文件大小: {len(content)/1024/1024:.2f} MB')

# 解析客户数据 - 使用栈匹配
data_start = content.find('var customersData = [')
if data_start < 0:
    print('未找到客户数据')
    exit()

bracket_count = 0
found_start = False
end_idx = -1
for i in range(data_start + len('var customersData = '), len(content)):
    if content[i] == '[':
        bracket_count += 1
        found_start = True
    elif content[i] == ']':
        bracket_count -= 1
        if found_start and bracket_count == 0:
            end_idx = i + 1
            break

if end_idx <= 0:
    print('未找到客户数据结束位置')
    exit()

customers_json = content[data_start + len('var customersData = '):end_idx]
customers = json.loads(customers_json)
print(f'原始客户数: {len(customers)}')

# 统计
overdue = [c for c in customers if c.get('isOverdue')]
important = [c for c in customers if c.get('level', '').startswith('A类')]
print(f'超期客户数: {len(overdue)}, A类客户数: {len(important)}')

# 合并去重
keep_ids = set(c['id'] for c in overdue)
keep_ids.update(c['id'] for c in important)
simplified = [c for c in customers if c['id'] in keep_ids]
print(f'精简后客户数: {len(simplified)}')

# 精简字段
slimmed = [{
    'id': c.get('id', ''),
    'name': c.get('name', ''),
    'level': c.get('level', ''),
    'nextDate': c.get('nextDate', ''),
    'advice': c.get('advice', ''),
    'isOverdue': c.get('isOverdue', False),
    'warning': c.get('warning', ''),
} for c in simplified]

new_data = json.dumps(slimmed, ensure_ascii=False)
print(f'精简后数据大小: {len(new_data)/1024:.0f} KB')

# 替换
old_str = content[data_start:end_idx]
content = content.replace(old_str, 'var customersData = ' + new_data)
print(f'已替换客户数据')

# 删除产品数据
prod_start = content.find('var productsData = [')
if prod_start >= 0:
    bracket_count = 0
    found_start = False
    end_idx = -1
    for i in range(prod_start + len('var productsData = '), len(content)):
        if content[i] == '[':
            bracket_count += 1
            found_start = True
        elif content[i] == ']':
            bracket_count -= 1
            if found_start and bracket_count == 0:
                end_idx = i + 1
                break
    
    if end_idx > 0:
        old_prod = content[prod_start:end_idx]
        content = content.replace(old_prod, 'var productsData = [];')
        print(f'已删除产品数据，原大小: {len(old_prod)/1024:.0f} KB')

# 写入
with open('湘里情智营·客户决策_v2_simple.html', 'w', encoding='utf-8') as f:
    f.write(content)

import os
size = os.path.getsize('湘里情智营·客户决策_v2_simple.html')
print(f'最终文件大小: {size/1024/1024:.2f} MB')
