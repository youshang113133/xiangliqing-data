import json, re

# 读取原文件
with open('湘里情智营·客户决策_v2.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 解析客户数据
m = re.search(r'var customersData = (\[.*?\]);', content, re.DOTALL)
if m:
    customers = json.loads(m.group(1))
    print(f'原始客户数: {len(customers)}')
    
    # 精简客户数据 - 只保留核心字段
    simplified = []
    for c in customers:
        simplified.append({
            'id': c.get('id', ''),
            'name': c.get('name', ''),
            'level': c.get('level', ''),
            'nextDate': c.get('nextDate', ''),
            'advice': c.get('advice', ''),
            'isOverdue': c.get('isOverdue', False),
            'warning': c.get('warning', ''),
            'salesman': c.get('salesman', ''),
            'profitRate': c.get('profitRate', 0),
        })
    
    new_customers_data = json.dumps(simplified, ensure_ascii=False)
    print(f'精简后客户数据大小: {len(new_customers_data)} 字符')
    
    # 替换原客户数据
    content = re.sub(
        r'var customersData = \[.*?\];',
        f'var customersData = {new_customers_data};',
        content,
        flags=re.DOTALL
    )

# 删除产品数据（用空数组替换）
m = re.search(r'var productsData = \[.*?\];', content, flags=re.DOTALL)
if m:
    print(f'原产品数据大小: {len(m.group(0))} 字符')
    content = re.sub(r'var productsData = \[.*?\];', 'var productsData = [];', content, flags=re.DOTALL)
    print('已删除产品数据')

# 写入精简后的文件
with open('湘里情智营·客户决策_v2_simple.html', 'w', encoding='utf-8') as f:
    f.write(content)

import os
size = os.path.getsize('湘里情智营·客户决策_v2_simple.html')
print(f'精简后文件大小: {size/1024/1024:.2f} MB')
