# 湘里情智营·客户决策系统 - 维护文档

## 页面结构

### 三大主页面
1. **日报页 (pgReport)** - 核心经营指标和毛利区间分布
2. **产品页 (pgProduct)** - 产品中心，支持搜索、筛选和排序
3. **客户页 (pgCustomer)** - 客户管理，按ABCD分层展示

### 数据刷新机制
- 页面顶部有"🔄 刷新数据"按钮
- 点击后会重新从CDN获取最新数据
- 刷新后会显示"☁️ 数据: 云端 | 🟢 网络: 在线 | 更新时间: xxx"

## 产品页面更新逻辑

### 产品列表渲染 (renderProduct函数)
- 从 `productsData` 全局变量获取产品列表（1471个产品）
- 支持以下筛选功能：
  - 按产品名称/编码/规格/分类搜索
  - 按分类筛选 (pCategory下拉框)
  - 按毛利率区间筛选 (pProfitRange下拉框)
- 支持排序：
  - 按销售额排序 (sales_desc/sales_asc)
  - 按毛利率排序 (profit_desc/profit_asc)
- 产品卡片显示：排名、编码、名称、规格、一批价、二批价、毛利率、零售价

### 重要修复记录

#### 2026-04-25: 修复产品页面portrait变量未定义错误
**问题**: 产品页面显示"未找到匹配的产品"，控制台报错 "portrait is not defined"

**原因**: `renderProduct` 函数中引用了未定义的 `portrait` 变量（该变量仅在 `showProductDetail` 函数中定义）

**修复方案**: 
```javascript
// 修复前:
var profitRate = p.profit;
if ((!profitRate || profitRate === 0) && portrait['毛利率(%)']) {
    profitRate = parseFloat(portrait['毛利率(%)']);
}

// 修复后:
var profitRate = p.profit;
```

**提交**: `534c2f8` - fix: 修复产品页面portrait变量未定义错误

## 客户预计进货时间计算逻辑

### ABCD分层规则
| 分层 | 名称 | 进货间隔 | 说明 |
|------|------|---------|------|
| A类 | 核心客户 | +15天 | 高价值核心客户 |
| B类 | 重要客户 | +30天 | 重要客户 |
| C类 | 普通客户 | +45天 | 普通客户 |
| D类 | 待优化客户 | +60天 | 需要优化跟进 |

### 计算公式
```
nextDate = lastDate + interval_days
```
- `lastDate`: 客户最后一次下单日期
- `nextDate`: 预计下次进货日期
- `interval_days`: 根据分层确定的间隔天数

### 数据来源
- 字段名: `nextDate` (在 `data_core.json` 的 `customersData` 数组中)
- 分层字段: `level` (如 "A类核心客户", "B类重要客户", "C类普通客户", "D类待优化客户")

## 数据文件说明

### data_core.json
核心数据文件，包含：
- `updateTime`: 数据更新时间
- `dailyReportData`: 当日报表数据
- `salesProgressData`: 销售进度数据
- `productsData`: 产品列表（1471条）
- `customersData`: 客户列表（4264条）
- `productPortraitData`: 产品画像数据
- `productSalesmen`: 业务员产品关联

### data_recs.json
推荐数据文件，包含按区域划分的客户推荐信息。

## GitHub Pages部署

### 仓库
- GitHub: https://github.com/xiangliqing888/xiangliqing-data
- Pages URL: https://xiangliqing888.github.io/xiangliqing-data/

### CDN缓存清除
使用 jsDelivr 的 purge API 清除缓存：
```
GET https://purge.jsdelivr.net/gh/xiangliqing888/xiangliqing-data@main/index.html
```

### 部署流程
1. 推送代码到 `main` 分支
2. GitHub Actions 自动部署到 GitHub Pages
3. 如需立即生效，调用 CDN purge API 清除缓存

## 代码提交规范

### 提交信息格式
```
<type>: <subject>

<body>
```

### Type 类型
- `fix`: 错误修复
- `feat`: 新功能
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `perf`: 性能优化

### 示例
```
fix: 修复产品页面portrait变量未定义错误

- 移除renderProduct函数中对未定义portrait变量的引用
- 简化毛利率显示逻辑，直接使用p.profit数据
- 确保产品列表能正常渲染
```


---

## 毛利区间分布逻辑（2026-04-25补充）

### 数据来源
- 从T+系统销货单明细表提取每笔订单的毛利率
- 按毛利率区间统计销售额和占比

### 区间划分（6个区间）
| 区间 | 毛利率范围 | 目标占比 | 说明 |
|------|-----------|---------|------|
| 高利区间 | ≥18% | 25% | 优质订单，应增加占比 |
| 中高区间 | 13%-18% | 25% | 达标区间 |
| 基准区间 | 8%-13% | 25% | 及格线 |
| 低利区间 | 5%-8% | 15% | 需优化 |
| 微利区间 | <5% | 10% | 预警区 |
| 亏损区间 | <0% | 0% | 红线，应杜绝 |

### 预警规则
- **🟢正常**：实际占比 ≤ 目标占比（好）
- **🔴预警**：实际占比 > 目标占比（需关注）

### 展示位置
- 日报页面 → 毛利区间分布表格
- 显示：区间名称、销售额、实际占比、目标占比、预警状态

### 计算公式
```
占比 = 区间销售额 / 当日总销售额
预警 = 占比 > 目标占比 ? "🔴预警" : "🟢正常"
```

### 数据结构示例
```json
{
  "当日": [
    {
      "区间": "≥18%高利区间",
      "销售额": 120866.5,
      "占比": 0.313,
      "目标占比": 0.25,
      "预警": "🟢正常"
    }
  ],
  "月累计": [...]
}
```

### 页面代码位置
- 文件：`index.html`
- 函数：`renderReport()`
- 行号：约523-546行
- 数据源：`dailyReportData['毛利区间']['当日']`
