# IDH 协同平台 · 前端设计文档

> 版本: V1.0 | 日期: 2026-11 | 框架: Vue 3 + TypeScript + Vite

---

## 1. 技术选型

| 类别 | 选型 | 版本 | 理由 |
|------|------|------|------|
| 框架 | Vue 3 (Composition API) | 3.4+ | 生态成熟，响应式系统优越 |
| 语言 | TypeScript | 5.4+ | 类型安全，大型项目必备 |
| 构建 | Vite | 5.x | 极速 HMR，按需编译 |
| 状态管理 | Pinia | 2.x | Vue 3 官方推荐，支持 devtools |
| 路由 | Vue Router | 4.x | 嵌套路由、导航守卫 |
| HTTP | Axios | 1.x | 拦截器、取消请求 |
| UI 组件库(PC) | Element Plus | 2.x | 企业级中后台首选 |
| UI 组件库(Mobile) | Vant 4 | 4.x | 轻量移动端组件库 |
| 图表 | ECharts 5 | 5.x | 复杂图表需求满足 |
| 表单 | VeeValidate + Zod | — | 声明式验证，类型推导 |
| 国际化 | vue-i18n | 9.x | 中/英双语支持 |
| 扫码 | html5-qrcode | — | H5 浏览器扫码，无需安装 App |
| 实时通信 | WebSocket (原生) | — | 聊天消息实时推送 |
| 代码规范 | ESLint + Prettier | — | 统一代码风格 |

---

## 2. 目录结构

```
frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── api/                      # 后端接口调用层
│   │   ├── request.ts            # Axios 实例（拦截器/Token/刷新）
│   │   ├── workOrder.ts          # 工单域 API
│   │   ├── shipment.ts           # 发运域 API
│   │   ├── inventory.ts          # 库存域 API
│   │   ├── production.ts         # 生产域 API
│   │   ├── reconciliation.ts     # 对账域 API
│   │   ├── alert.ts             # 预警域 API
│   │   ├── conversation.ts       # 通信域 API
│   │   └── ai.ts                # AI 服务 API
│   ├── assets/                   # 静态资源
│   │   ├── images/
│   │   └── styles/
│   │       ├── variables.scss    # 主题变量
│   │       ├── mixins.scss       # 混入
│   │       └── global.scss       # 全局样式
│   ├── components/               # 共享组件
│   │   ├── common/               # 通用组件
│   │   │   ├── StatusTag.vue     # 状态标签
│   │   │   ├── DiffCodeBadge.vue # 差异码徽标
│   │   │   ├── IdempotentBtn.vue # 幂等提交按钮
│   │   │   ├── TraceTimeline.vue # 追溯时间线
│   │   │   ├── EventList.vue     # 事件列表
│   │   │   └── AttachmentUpload.vue # 附件上传
│   │   ├── workorder/            # 工单组件
│   │   │   ├── WoCard.vue        # 工单卡片
│   │   │   ├── WoLineTable.vue   # 工单行明细表
│   │   │   └── WoStatusFlow.vue  # 工单状态流转图
│   │   ├── inventory/            # 库存组件
│   │   │   ├── StockSummary.vue  # 库存汇总卡片
│   │   │   ├── StockFilter.vue   # 库存筛选面板
│   │   │   └── AgingChart.vue    # 账龄分布图
│   │   ├── reconciliation/       # 对账组件
│   │   │   ├── ReconDiffTable.vue    # 差异明细表
│   │   │   ├── ReconSummaryCard.vue  # 对账汇总卡片
│   │   │   └── AdjustmentForm.vue    # 调整单表单
│   │   ├── chat/                 # 聊天组件
│   │   │   ├── ChatPanel.vue     # 聊天面板（主容器）
│   │   │   ├── ChatSidebar.vue   # 对话列表侧栏
│   │   │   ├── MessageBubble.vue # 消息气泡
│   │   │   ├── MessageInput.vue  # 消息输入框
│   │   │   ├── MessageTag.vue    # 消息标签标记
│   │   │   └── TagFilter.vue     # 标签筛选器
│   │   └── ai/                   # AI 组件
│   │       ├── AiChatPanel.vue   # AI 对话面板
│   │       ├── DiffHypothesis.vue # 差异归因卡片
│   │       └── DocumentPreview.vue # 单据识别预览
│   ├── composables/              # 组合式函数
│   │   ├── useAuth.ts            # 认证逻辑
│   │   ├── usePagination.ts      # 分页逻辑
│   │   ├── useWebSocket.ts       # WebSocket 连接
│   │   ├── useIdempotency.ts     # 幂等键生成
│   │   └── usePermission.ts      # 权限判断
│   ├── layouts/                  # 布局组件
│   │   ├── DefaultLayout.vue     # PC 默认布局（侧栏+顶栏+内容）
│   │   ├── MobileLayout.vue      # H5 布局（顶栏+标签栏+内容）
│   │   └── BlankLayout.vue       # 空白布局（全屏页如扫码）
│   ├── router/                   # 路由
│   │   ├── index.ts              # 路由入口
│   │   └── modules/              # 路由模块
│   │       ├── workorder.ts
│   │       ├── shipment.ts
│   │       ├── inventory.ts
│   │       ├── production.ts
│   │       ├── reconciliation.ts
│   │       ├── alert.ts
│   │       ├── chat.ts
│   │       └── mobile.ts         # H5 路由
│   ├── stores/                   # Pinia 状态管理
│   │   ├── auth.ts               # 认证/用户信息
│   │   ├── app.ts                # 全局应用状态（侧栏折叠等）
│   │   ├── chat.ts               # 聊天消息与连接
│   │   ├── notification.ts       # 通知/预警计数
│   │   └── tenant.ts             # 当前租户上下文
│   ├── types/                    # TypeScript 类型定义
│   │   ├── workOrder.ts
│   │   ├── shipment.ts
│   │   ├── inventory.ts
│   │   ├── reconciliation.ts
│   │   ├── conversation.ts
│   │   └── common.ts             # 通用类型（分页/响应/错误码）
│   ├── utils/                    # 工具函数
│   │   ├── format.ts             # 日期/数字格式化
│   │   ├── validation.ts         # 业务校验规则
│   │   └── download.ts           # 文件下载/导出
│   ├── views/                    # 页面视图
│   │   ├── workorder/
│   │   │   ├── WorkOrderList.vue     # 工单列表
│   │   │   ├── WorkOrderDetail.vue   # 工单详情
│   │   │   └── WorkOrderCreate.vue   # 工单创建
│   │   ├── shipment/
│   │   │   ├── ShipmentList.vue      # 发货单列表
│   │   │   ├── ShipmentDetail.vue    # 发货单详情
│   │   │   └── GoodsReceipt.vue      # 收货确认
│   │   ├── inventory/
│   │   │   ├── StockBoard.vue        # 库存看板
│   │   │   ├── StockLedger.vue       # 库存流水
│   │   │   └── TraceView.vue         # SN 追溯
│   │   ├── production/
│   │   │   ├── IssueScan.vue         # 领料扫码
│   │   │   ├── WipReport.vue         # 工序报工
│   │   │   └── FgReceipt.vue         # 成品入库
│   │   ├── reconciliation/
│   │   │   ├── ReconCenter.vue       # 对账中心
│   │   │   ├── ReconDetail.vue       # 差异明细
│   │   │   └── AdjustmentList.vue    # 调整单列表
│   │   ├── alert/
│   │   │   └── AlertList.vue         # 预警列表
│   │   ├── chat/
│   │   │   └── ChatView.vue          # 协同沟通台
│   │   ├── ai/
│   │   │   └── AiAssistant.vue       # AI 助手
│   │   ├── dashboard/
│   │   │   └── Dashboard.vue         # 首页仪表盘
│   │   ├── mobile/                   # H5 专用页面
│   │   │   ├── ScanIssue.vue         # 扫码领料
│   │   │   ├── ScanReport.vue        # 扫码报工
│   │   │   └── ScanReceive.vue       # 扫码收货
│   │   └── error/
│   │       ├── 403.vue
│   │       ├── 404.vue
│   │       └── 500.vue
│   ├── App.vue
│   └── main.ts
├── index.html
├── vite.config.ts
├── tsconfig.json
├── package.json
├── .env.development
├── .env.production
└── .eslintrc.cjs
```

---

## 3. 路由设计

### 3.1 PC 端路由表

| 路径 | 页面 | 权限 | 说明 |
|------|------|------|------|
| `/` | Dashboard | 全部 | 首页仪表盘 |
| `/work-orders` | WorkOrderList | 全部 | 工单列表 |
| `/work-orders/create` | WorkOrderCreate | factory | 创建工单（仅原厂） |
| `/work-orders/:woNo` | WorkOrderDetail | 全部 | 工单详情 + CollabChat 侧栏 |
| `/shipments` | ShipmentList | 全部 | 发货单列表 |
| `/shipments/:dnNo` | ShipmentDetail | 全部 | 发货单详情 |
| `/shipments/:dnNo/receipt` | GoodsReceipt | idh | 收货确认（仅 IDH） |
| `/inventory/stock` | StockBoard | 全部 | 库存看板 |
| `/inventory/ledger` | StockLedger | 全部 | 库存流水 |
| `/inventory/trace/:sn` | TraceView | 全部 | SN 追溯 |
| `/production/issue` | IssueScan | idh | 领料投产 |
| `/production/wip` | WipReport | idh | 工序报工 |
| `/production/fg` | FgReceipt | idh | 成品入库 |
| `/reconciliation` | ReconCenter | 全部 | 对账中心 |
| `/reconciliation/:periodId` | ReconDetail | 全部 | 差异明细 |
| `/adjustments` | AdjustmentList | 全部 | 调整单列表 |
| `/alerts` | AlertList | 全部 | 预警列表 |
| `/chat` | ChatView | 全部 | 协同沟通台 |
| `/ai` | AiAssistant | 全部 | AI 助手 |

### 3.2 路由守卫

```
router.beforeEach:
  1. 检查 Token 是否存在 / 有效 → 无效跳转登录
  2. 检查路由 meta.roles → 不满足跳 403
  3. 设置文档标题
```

### 3.3 H5 端路由

| 路径 | 页面 | 说明 |
|------|------|------|
| `/m/scan/issue` | ScanIssue | 扫码领料 |
| `/m/scan/report` | ScanReport | 扫码报工 |
| `/m/scan/receive` | ScanReceive | 扫码收货 |

H5 路由独立于 PC 路由，挂载在 MobileLayout 下，使用 hash 模式以支持扫码场景。

---

## 4. 布局设计

### 4.1 PC 端 DefaultLayout

```
┌──────────────────────────────────────────────┐
│ 顶栏 (Header)                     🔔 ⚙️ 👤  │
│ Logo · 租户切换 · 全局搜索         通知 设置 用户│
├────────┬─────────────────────────────────────┤
│ 侧栏    │                                     │
│ (Side)  │        主内容区 (Main)               │
│        │                                     │
│ 📊 首页 │                                     │
│ 📋 工单 │                                     │
│ 🚚 发运 │                                     │
│ 📦 库存 │                                     │
│ ⚙️ 生产 │                                     │
│ 📐 对账 │                                     │
│ 🔔 预警 │                                     │
│ 💬 沟通 │                                     │
│ 🤖 AI  │                                     │
│        │                                     │
│ 可折叠  │                                     │
├────────┴─────────────────────────────────────┤
│ 页脚: IDH 协同平台 v1.0 · © 2026              │
└──────────────────────────────────────────────┘
```

- 侧栏宽度: 220px（展开）/ 64px（折叠）
- 侧栏菜单根据角色动态过滤（原厂 vs IDH）
- 工单详情页右侧可选展开 CollabChat 面板（宽度 380px）

### 4.2 H5 端 MobileLayout

```
┌──────────────────────┐
│ 顶栏: 页面标题  [返回]│
├──────────────────────┤
│                      │
│     主内容区          │
│   （扫码摄像头视图）   │
│                      │
│                      │
├──────────────────────┤
│ 🏠首页 📋工单 🔍扫码 💬沟通 👤我的 │
└──────────────────────┘
```

- 底部标签栏固定，5 个入口
- 扫码页面全屏，隐藏标签栏

---

## 5. 核心页面设计

### 5.1 首页仪表盘 (Dashboard)

**布局:** 三栏网格

| 区域 | 内容 | 组件 |
|------|------|------|
| 左上 | 关键指标卡片 | 待处理工单数 / 在制数 / 本月发货量 / 库存总量 |
| 中上 | 预警速览 | 最近 5 条未处理预警 |
| 右上 | 交期看板 | 近 30 天到期工单甘特条 |
| 左下 | 库存概览 | 按物料 Top 5 的库存饼图 |
| 中下 | 对账摘要 | 本期对账状态 + 差异率 |
| 右下 | 最近沟通 | 最近活跃对话列表，点击跳转 |

**角色差异:**
- 原厂: 全局数据，含所有 IDH
- IDH: 只看自己工单和库存

### 5.2 工单详情页 (WorkOrderDetail)

```
┌─────────────────────────────────────────────────────┐
│ ← 返回列表    WO-20261103-001    [in_production]    │
├─────────────────────────────────────────────────────┤
│ 📋 基本信息: IDH / 客户 / 下达日期 / 交期 / BOM 版本  │
│ 📊 数量进度: 带进度条的四个数量指标                    │
│  ┌──────────────────────────────────────────────┐   │
│  │ qty_ordered:  ████████████████████ 10000     │   │
│  │ qty_shipped:  ████████████████████ 10000 100%│   │
│  │ qty_received: ████████████████████ 10000 100%│   │
│  │ qty_consumed: ████████░░░░░░░░░░░░  4200  42%│   │
│  └──────────────────────────────────────────────┘   │
│ 📋 行明细表: 料号 / 下单数 / 发货数 / 收货数 / 消耗数 │
│ 📦 关联发货单列表 (可展开)                            │
│ 📜 最近事件 (时间线)                                  │
│ 💬 CollabChat 面板（右侧可展开/收起）                  │
│ [下达] [接单] [变更] [暂停]  ← 按钮根据状态+角色显示  │
└─────────────────────────────────────────────────────┘
```

### 5.3 库存看板 (StockBoard)

**功能:**
- 筛选面板: 物料 / 批次 / IDH / 状态 / 归属方 / 账龄大于 N 天
- 汇总卡片: 可用 / 已分配 / 冻结 / 在途 四个指标
- 表格: 物料 → 批次 → 数量 → 账龄 → 状态 → 操作
- 操作: 查看流水、标记冻结/解冻（需权限）
- 导出 Excel

**权限:** 原厂看全部 IDH；IDH 只能看到自己库存。

### 5.4 对账中心 (ReconCenter)

```
┌──────────────────────────────────────────────────┐
│  对账中心                          [2026-10 ▼]    │
├──────────────────────────────────────────────────┤
│  对账状态: 已开启        整体差异率: 0.3%          │
│                                                    │
│  差异分类摘要卡:                                    │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐    │
│  │ D01  │ │ D02  │ │ D03  │ │ D04  │ │ D05  │    │
│  │ 发货  │ │ 收货  │ │ 领用  │ │ 报废  │ │ 数差  │    │
│  │ 未收  │ │ 差异  │ │ 未报  │ │ 未报  │ │       │    │
│  │  1   │ │  0   │ │  2   │ │  2   │ │  0   │    │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘    │
│                                                    │
│  ┌────────────────────────────────────────────┐   │
│  │ 差异明细列表                                 │   │
│  │ ID │ 批次            │ 差异码 │ 差异量 │ 状态 │   │
│  │ 5  │ L2604-A17-2603 │ D04   │ -30   │ 待处理│   │
│  │ 7  │ L2604-A17-2603 │ D03   │ -20   │ 申辩中│   │
│  │ ... │                                 [下页]│   │
│  └────────────────────────────────────────────┘   │
│                                                    │
│  [触发核对] [锁账]                                 │
└──────────────────────────────────────────────────┘
```

### 5.5 协同沟通台 (ChatView)

采用 Slack/飞书 风格三栏布局：

```
┌──────────┬───────────────────────┬──────────────────┐
│ 对话列表  │     消息区             │    详情面板       │
│ (300px)  │     (flex)            │    (320px)       │
├──────────┼───────────────────────┼──────────────────┤
│ 🔍 搜索   │ WO-20261103-001 沟通  │ 📌 承诺标签       │
│          │                       │  · 2026-12-18   │
│ 📌 固定:  │ ┌───────────────────┐ │    交期承诺       │
│ WO-001   │ │ 张三: L2604-A17.. │ │                  │
│ WO-002   │ │ 已领投产，预计...  │ │ 🔢 数字标签       │
│          │ │     10:30         │ │  · 1200 颗      │
│ 💬 最近:  │ └───────────────────┘ │  · 12 颗报废     │
│ DN-005   │ ┌───────────────────┐ │                  │
│ RECON-10 │ │ 李四: 收到，今天  │ │ ⚠️ 问题标签      │
│ ...      │ │ 完成贴片后报工    │ │  · 质量异常      │
│          │ │     10:32         │ │                  │
│          │ └───────────────────┘ │ 📎 共享文件      │
│          │                       │  · photo_001.jpg│
│          │ ┌───────────────────┐ │                  │
│          │ │ 系统: 系统检测到  │ │                  │
│          │ │ 承诺交期 12.18    │ │                  │
│          │ │     10:33 [AI]   │ │                  │
│          │ └───────────────────┘ │                  │
│          ├───────────────────────┤                  │
│          │ [😊] [📎] 输入消息... │ [发送]           │
├──────────┴───────────────────────┴──────────────────┤
│ 状态栏: 🟢 在线 · 2 人参与                           │
└─────────────────────────────────────────────────────┘
```

**功能要点:**
- 对话列表按 `conv_type` 分组（wo / dn / recon / alert / group）
- 消息气泡区分我方/对方/系统/AI，渲染 `msg_type`（text / image / file）
- AI 自动扫描消息，打标签（承诺/数字/问题/原因/决定/提及），显示置信度
- 右侧面板聚合标签，按时间线展示承诺兑现状态
- 支持 @提及、附件上传（图片/PDF）
- WebSocket 实时推送新消息

### 5.6 AI 助手 (AiAssistant)

```
┌──────────────────────────────────────────────────┐
│  AI 助手                                          │
├──────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────┐  │
│  │ 🤖 有什么可以帮你的？                        │  │
│  │                                             │  │
│  │ 快捷入口:                                   │  │
│  │ [📄 上传单据识别] [🔍 差异归因] [📊 问数]   │  │
│  │                                             │  │
│  │ 💬 上个月 BM1684X 在 IDH001 的库存差异...   │  │
│  │                                             │  │
│  │ ┌──────────────────────────────────────┐   │  │
│  │ │ 📊 2026-10 BM1684X @IDH001 差异分析   │   │  │
│  │ │                                      │   │  │
│  │ │ 差异: -20 (系统) +30 (实物)           │   │  │
│  │ │ 主因: D03 领用未报工 2笔              │   │  │
│  │ │       D04 报废未申报 2笔              │   │  │
│  │ │                                      │   │  │
│  │ │ [柱状图: 差异分布]                    │   │  │
│  │ │                                      │   │  │
│  │ │ 来源: recon_item.id=5,7              │   │  │
│  │ └──────────────────────────────────────┘   │  │
│  │                                             │  │
│  │ 输入你的问题...                     [发送] │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

---

## 6. 状态管理 (Pinia Store)

### 6.1 auth.ts

```typescript
interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: {
    id: string;
    name: string;
    role: 'factory_admin' | 'factory_op' | 'idh_admin' | 'idh_op';
    tenantId: string;
    idhId?: string;      // IDH 用户关联的 IDH
  } | null;
  permissions: string[];
}

// actions: login, logout, refreshToken, fetchUserInfo
```

### 6.2 chat.ts

```typescript
interface ChatState {
  conversations: Conversation[];
  activeConvId: string | null;
  messages: Map<string, Message[]>;  // convId → messages
  unreadCount: Map<string, number>;
  wsConnected: boolean;
  onlineUsers: Set<string>;
}

// actions: fetchConversations, fetchMessages, sendMessage,
//          connectWs, disconnectWs, markRead
```

### 6.3 notification.ts

```typescript
interface NotificationState {
  alerts: Alert[];
  unreadAlertCount: number;
  reconItems: ReconItem[];    // 待处理差异
  pendingAdjustments: number; // 待签批调整单
}

// actions: fetchUnreadCount (定时轮询 30s)
```

---

## 7. API 集成层

### 7.1 request.ts — Axios 实例

```typescript
// 核心功能:
// 1. baseURL 从环境变量读取
// 2. 请求拦截器: 注入 Authorization header + X-Trace-Id
// 3. 响应拦截器:
//    - code === 0: 返回 data
//    - code === 2001: 自动调用 refreshToken
//    - 其他错误码: 弹出 ElMessage 或抛出
// 4. 幂等键: POST 请求自动生成 X-Idempotency-Key (uuid v4)
// 5. 超时: 30s
// 6. 取消: 路由切换时取消 pending 请求 (AbortController)
```

### 7.2 API 模块示例

```typescript
// api/workOrder.ts
export const workOrderApi = {
  list: (params: WoListParams) =>
    request.get<PaginatedResponse<WorkOrder>>('/work-orders', { params }),

  detail: (woNo: string) =>
    request.get<WorkOrderDetail>(`/work-orders/${woNo}`),

  create: (data: CreateWoRequest) =>
    request.post<{ wo_no: string }>('/work-orders', data),

  issue: (woNo: string) =>
    request.post(`/work-orders/${woNo}/issue`),

  accept: (woNo: string, data: AcceptRequest) =>
    request.post(`/work-orders/${woNo}/accept`, data),

  change: (woNo: string, data: ChangeRequest) =>
    request.post(`/work-orders/${woNo}/change`, data),
};
```

---

## 8. H5 扫码设计

### 8.1 扫码核心流程

```
1. 用户登录 H5 → JWT Token 持久化
2. 进入扫码页 → 请求摄像头权限
3. html5-qrcode 持续扫描
4. 扫描到二维码/条码:
   a. 解析格式: { type: "lot"|"container"|"wo", value: "..." }
   b. 调用对应 API 获取详情
   c. 展示确认表单（数量/操作人/备注）
   d. 提交 → 成功反馈（振动 + 绿色勾）
   e. 3 秒后自动回到扫码界面
```

### 8.2 扫码页面适配

- 全屏摄像头预览，仅底部保留操作区
- 适配昏暗车间：开启手电筒选项
- 离线缓存：网络断开时本地暂存，恢复后批量提交
- PDA 适配：响应式布局，最小宽度 320px

---

## 9. 角色差异化 UI

| 功能点 | 原厂视角 | IDH 视角 |
|--------|---------|---------|
| 创建工单 | ✅ | ❌ |
| 下达工单 | ✅ | ❌ |
| IDH 接单 | ❌ | ✅ |
| 创建发货单 | ✅ | ❌ |
| 确认发货 | ✅ | ❌ |
| 收货确认 | ❌ | ✅ |
| 库存查询 | 全量 | 仅自己 |
| 领料/报工/入库 | ❌ | ✅ |
| 触发对账 | ✅ | ❌ |
| 锁账 | ✅ | ❌ |
| 差异申辩 | ❌ | ✅ |
| 创建/签批调整 | ✅ + ✅ | ✅（各一签） |
| `unit_price` 可见 | ✅ | ❌ (脱敏) |
| `customer_id` 可见 | ✅ | ❌ (脱敏) |
| 预警 | 全局 | 仅自己 |

实现方式：
- 路由 `meta.roles` 控制页面访问
- 组件内 `v-if="authStore.hasPermission('...')"` 控制按钮显示
- API 层 `stockStore` 自动按角色过滤（原厂加 `idh_id` 筛选项）

---

## 10. 主题与样式

> 详细视觉规范参见 [DESIGN_SYSTEM.md](./DESIGN_SYSTEM.md)，本节仅提取前端实现相关的关键变量。开发时以此为唯一 CSS 变量来源。

### 10.1 CSS 变量（来自 Design System）

```css
:root {
  /* 品牌色 */
  --brand:        #4F46E5;
  --brand-2:      #7C3AED;
  --brand-soft:   #EEF0FF;
  --cyan:         #06B6D4;

  /* 中性色 */
  --ink:          #0A0F1E;
  --ink-2:        #1B2436;
  --body:         #3F4B60;
  --muted:        #6B7A90;
  --faint:        #98A4B8;
  --line:         #E7EBF3;
  --line-2:       #F0F3F9;
  --canvas:       #F6F8FC;
  --paper:        #FFFFFF;

  /* 语义色 */
  --ok:           #10B981;
  --warn:         #F59E0B;
  --danger:       #EF4444;
  --info:         #0EA5E9;

  /* 圆角（仅五档） */
  --r-sm:         8px;   /* 小元件 */
  --r-md:         12px;  /* 输入框 */
  --r-lg:         16px;  /* 卡片 */
  --r-xl:         22px;  /* 大容器 */

  /* 阴影（仅三档） */
  --sh-1: 0 1px 2px rgba(10,15,30,.05);
  --sh-2: 0 2px 4px rgba(10,15,30,.04), 0 12px 28px -12px rgba(10,15,30,.10);
  --sh-3: 0 24px 60px -24px rgba(10,15,30,.22);

  /* 动效 */
  --ease: cubic-bezier(.2, .7, .2, 1);
}
```

### 10.2 字体

```css
font-family: "Inter", -apple-system, BlinkMacSystemFont,
  "PingFang SC", "HarmonyOS Sans SC", "Microsoft YaHei", sans-serif;
```

| 层级 | 字号 | 字重 | 字距 | 用途 |
|------|------|------|------|------|
| Display | 62px | 800 | -0.035em | Hero 大标题 |
| H2 | 34px | 800 | -0.025em | 页面标题 |
| H3 | 17px | 700 | -0.01em | 区块标题 |
| Body | 15.5px | 400 | 0 | 正文, 行高 1.8 |
| Micro | 11px | 700 | 0.16em | 标签/表头大写 |
| Code | 12.5px | — | — | 内联代码 |

### 10.3 间距（8pt 基准）

所有间距取自 4 的倍数: 4 / 8 / 12 / 16 / 24 / 32 / 56 / 88

### 10.4 动效时长

| 场景 | 时长 | 说明 |
|------|------|------|
| hover / 焦点 | 120–180ms | 背景或描边变化 |
| 弹窗 / 抽屉 | 240ms | 透明度 + 位移，不加缩放 |
| 数字变化 | 320ms | 滚动计数 |
| 卡片入场 | 600ms | 上移 16px + 淡入，列表错峰 60ms |

必须遵守 `prefers-reduced-motion`，减弱动效时所有位移与过渡取消。

### 10.5 响应式断点

| 名称 | 宽度 | 适用场景 |
|------|------|---------|
| `xs` | < 768px | 手机 (H5) |
| `sm` | ≥ 768px | 平板 |
| `md` | ≥ 1024px | 笔记本 |
| `lg` | ≥ 1440px | 桌面 / 大屏看板 |
| `xl` | ≥ 1920px | 超宽屏 |

---

## 11. 构建与部署

### 11.1 环境变量

```bash
# .env.development
VITE_API_BASE_URL=http://localhost:8080
VITE_WS_URL=ws://localhost:8080/ws
VITE_APP_TITLE=IDH协同平台(DEV)

# .env.production
VITE_API_BASE_URL=https://idh-platform.example.com
VITE_WS_URL=wss://idh-platform.example.com/ws
VITE_APP_TITLE=IDH协同平台
```

### 11.2 Vite 配置要点

```typescript
// vite.config.ts
export default defineConfig({
  plugins: [vue(), vueJsx()],
  resolve: {
    alias: {
      '@': '/src',
      '@components': '/src/components',
      '@views': '/src/views',
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8080',
      '/ws': { target: 'ws://localhost:8080', ws: true },
    },
  },
  build: {
    outDir: 'dist',
    chunkSizeWarningLimit: 500, // KB
    rollupOptions: {
      output: {
        manualChunks: {
          'element-plus': ['element-plus'],
          'echarts': ['echarts'],
          'vant': ['vant'],
        },
      },
    },
  },
});
```

### 11.3 Nginx 部署

```nginx
server {
    listen 443 ssl;
    server_name idh-platform.example.com;

    root /var/www/idh-platform/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8080;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /ws {
        proxy_pass http://backend:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

> 配套文档: [ARCHITECTURE.md](./ARCHITECTURE.md) · [DATABASE.md](./DATABASE.md) · [API.md](./API.md) · [DEPLOYMENT.md](./DEPLOYMENT.md) · [DESIGN_SYSTEM.md](./DESIGN_SYSTEM.md)