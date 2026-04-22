import re
from datetime import datetime

# 读取HTML文件
with open('湘里情智营·客户决策.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 修改DATA_URL，每次加载时自动添加时间戳
# 把静态URL改为动态生成
old_url_pattern = r"var DATA_URL = 'https://cdn.jsdelivr.net/gh/xiangliqing888/xiangliqing-data@main/data\.json[^']*';"
new_url = "var DATA_URL = 'https://cdn.jsdelivr.net/gh/xiangliqing888/xiangliqing-data@main/data.json?t=' + Date.now();"

content = re.sub(old_url_pattern, new_url, content)

# 2. 确保dataSource默认是cloud
content = content.replace("var dataSource = 'embedded'", "var dataSource = 'cloud'")

# 3. 移除内嵌数据（如果有的话）- 确保每次都从云端获取

# 保存修改
with open('湘里情智营·客户决策.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("修改完成！")
print("- DATA_URL: 每次加载自动添加时间戳")
print("- dataSource: 默认使用云端数据")
