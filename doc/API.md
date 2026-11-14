# IDH 协同平台 · API 接口设计文档

> 版本: V1.0 | 日期: 2026-11 | 协议: RESTful JSON over HTTPS

---

## 1. 通用规范

### 1.1 认证

```
Authorization: Bearer <JWT_ACCESS_TOKEN>
```

- Access Token 有效期: 15 分钟
- Refresh Token 有效期: 24 小时
- 刷新接口: `POST /auth/refresh`

### 1.2 通用请求头

| Header | 必填 | 说明 |
|--------|------|------|
| `Authorization` | 是 | `Bearer <token>` |
| `Content-Type` | 是 | `application/json` |
| `X-Idempotency-Key` | 写操作建议 | 幂等键，用于安全重试 |
| `X-Trace-Id` | 建议 | 链路追踪 ID |

### 1.3 通用响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": { ... },
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 156,
    "trace_id": "a1b2c3d4"
  }
}
```

### 1.4 错误码

| code | HTTP Status | 说明 |
|------|-------------|------|
| `0` | 200 | 成功 |
| `1001` | 400 | 参数校验失败 |
| `1002` | 404 | 资源不存在 |
| `1003` | 409 | 资源冲突（如重复收货） |
| `1004` | 422 | 业务规则校验不通过 |
| `2001` | 401 | 未认证 / Token 过期 |
| `2002` | 403 | 无权限（跨租户访问） |
| `2003` | 403 | 角色权限不足 |
| `3001` | 500 | 服务器内部错误 |
| `3002` | 503 | 服务暂时不可用 |

### 1.5 分页

```
GET /resource?page=1&page_size=20&sort=-created_at
```

响应 `meta` 中含 `page`, `page_size`, `total`。

### 1.6 日期/时间格式

- 日期: `YYYY-MM-DD`
- 时间戳: ISO 8601 `2026-11-03T14:30:00+08:00`

### 1.7 幂等键

所有 `POST` 写操作建议携带 `X-Idempotency-Key` 头。服务端以 `(tenant_id, idempotency_key)` 做去重，24 小时内重复请求返回首次结果。

---

## 2. 工单域 `/work-orders`

### 2.1 创建工单（草稿）

```
POST /work-orders
```

**请求体:**
```json
{
  "idh_id": "IDH001",
  "customer_id": "CUST123",
  "due_date": "2026-12-15",
  "bom_ver": "V2.1",
  "settle_mode": "purchase",
  "priority": 5,
  "lines": [
    {
      "material_code": "BMX-SOC-BM1684X-BGA-01",
      "qty_ordered": 10000,
      "unit_price": 12.50
    }
  ]
}
```

**响应:** `201 Created`
```json
{
  "code": 0,
  "data": {
    "wo_no": "WO-20261103-001",
    "status": "draft",
    "created_at": "2026-11-03T10:00:00+08:00"
  }
}
```

### 2.2 下达工单

```
POST /work-orders/{wo_no}/issue
```

工单状态: `draft → issued`。系统自动生成事件 `WO.ISSUED` 并推送给 IDH。

**响应:** `200 OK`

### 2.3 IDH 接单

```
POST /work-orders/{wo_no}/accept
```

**请求体:**
```json
{
  "confirmed_due_date": "2026-12-18",
  "remark": "产能紧张，建议延期 3 天"
}
```

工单状态: `issued → accepted`。IDH 可提反建议交期，原厂需确认。

### 2.4 查询工单列表

```
GET /work-orders?status=in_production&idh_id=IDH001&page=1&page_size=20
```

**响应 `data` 字段:**
```json
[
  {
    "wo_no": "WO-20261103-001",
    "idh_id": "IDH001",
    "status": "in_production",
    "due_date": "2026-12-15",
    "settle_mode": "purchase",
    "lines": [
      {
        "line_no": 1,
        "material_code": "BMX-SOC-BM1684X-BGA-01",
        "qty_ordered": 10000,
        "qty_shipped": 10000,
        "qty_received": 10000,
        "qty_consumed": 4200
      }
    ],
    "updated_at": "2026-11-03T14:00:00+08:00"
  }
]
```

### 2.5 查询工单详情

```
GET /work-orders/{wo_no}
```

返回内容含完整工单信息 + 关联发货单列表 + 最近 10 条事件。

### 2.6 工单变更/暂停/取消

```
POST /work-orders/{wo_no}/change
```

**请求体:**
```json
{
  "change_type": "suspended",
  "reason_code": "QUALITY_HOLD",
  "remark": "批次 L2604-A17-2603 质量异常，暂停投产"
}
```

状态进入 `suspended/changed/cancelled`，需附原因码与审批记录。

---

## 3. 发运域 `/shipments`

### 3.1 创建发货单

```
POST /shipments
```

**请求体:**
```json
{
  "wo_no": "WO-20261103-001",
  "idh_id": "IDH001",
  "eta": "2026-11-10",
  "carrier": "SF-Express",
  "tracking_no": "SF1234567890",
  "lines": [
    {
      "material_code": "BMX-SOC-BM1684X-BGA-01",
      "lot_no": "L2604-A17-2603",
      "container_id": "CT-DN20261103-001",
      "parent_container_id": "CT-DN20261103-BOX-A",
      "container_type": "reel",
      "qty_per_container": 250,
      "qty_shipped": 250
    }
  ]
}
```

**校验:** `material_code` 和 `lot_no` 必须在系统主数据中存在。

**响应:** `201 Created`
```json
{
  "code": 0,
  "data": {
    "dn_no": "DN-20261103-001",
    "status": "draft"
  }
}
```

### 3.2 确认发货

```
POST /shipments/{dn_no}/confirm
```

状态: `draft → shipped`，生成事件 `DN.SHIPPED`，更新 `wo_line.qty_shipped`。

### 3.3 查询发货单

```
GET /shipments?wo_no=WO-20261103-001
GET /shipments/{dn_no}
```

### 3.4 IDH 收货确认

```
POST /goods-receipts
```

**请求体:**
```json
{
  "dn_no": "DN-20261103-001",
  "lot_no": "L2604-A17-2603",
  "container_id": "CT-DN20261103-001",
  "qty_received": 248,
  "qty_shipped": 250,
  "diff_reason": "short",
  "received_by": "operator_zhang"
}
```

**校验:**
- 幂等: `(dn_no, container_id)` 唯一，重复请求返回 `409`
- 数量: `qty_received > qty_shipped` 时拦截 → `422`
- 批次: `lot_no` 存在且与 DN 中的一致

生成事件 `GR.CONFIRMED`，更新 `wo_line.qty_received`。

---

## 4. 库存域 `/inventory`

### 4.1 库存查询

```
GET /inventory/stock
```

**参数:**

| 参数 | 必填 | 说明 |
|------|------|------|
| `material_code` | 否 | 料号筛选 |
| `lot_no` | 否 | 批次筛选 |
| `idh_id` | 否 | IDH 筛选（原厂可用） |
| `status` | 否 | available / allocated / frozen / in_transit |
| `owner` | 否 | factory / idh |
| `aging_gt` | 否 | 账龄大于 N 天 |

**响应:**
```json
{
  "code": 0,
  "data": [
    {
      "material_code": "BMX-SOC-BM1684X-BGA-01",
      "lot_no": "L2604-A17-2603",
      "idh_id": "IDH001",
      "owner": "factory",
      "status": "available",
      "qty": 1800,
      "aging_days": 45,
      "as_of": "2026-11-03T02:00:00+08:00"
    }
  ]
}
```

**权限:** 原厂看全量；IDH 只看到自己物理仓库的库存。

### 4.2 库存流水

```
GET /inventory/stock-ledger?lot_no=L2604-A17-2603&from=2026-10-01&to=2026-11-01
```

按时间倒序返回该批次的全部库存变动记录，含来源事件 ID。

### 4.3 批次追溯

```
GET /inventory/trace/{sn}
```

从成品 SN 反查到晶圆批的完整链路。

**响应:**
```json
{
  "code": 0,
  "data": {
    "sn": "BM1684X-2603-000123",
    "trace": [
      { "step": "成品入库", "event": "FG.RECEIVED", "ts": "2026-10-22T16:00:00+08:00", "wo_no": "WO-20261001-001" },
      { "step": "芯片领用", "event": "ISSUE.POSTED", "ts": "2026-10-21T09:00:00+08:00", "lot_no": "L2604-A17-2603", "qty": 1 },
      { "step": "收货", "event": "GR.CONFIRMED", "ts": "2026-10-10T11:00:00+08:00", "dn_no": "DN-20261003-001" },
      { "step": "发货", "event": "DN.SHIPPED", "ts": "2026-10-03T08:00:00+08:00", "carrier": "SF-Express" },
      { "step": "晶圆批次", "wafer_lot": "L2604", "assembly_lot": "A17", "date_code": "2603" }
    ]
  }
}
```

---

## 5. 生产域 `/production`

### 5.1 领料投产

```
POST /issues
```

**请求体:**
```json
{
  "wo_no": "WO-20261103-001",
  "lot_no": "L2604-A17-2603",
  "material_code": "BMX-SOC-BM1684X-BGA-01",
  "qty": 1200,
  "operator": "operator_zhang",
  "scan_method": "h5"
}
```

**校验:**
- `qty ≤ lot.qty_available`
- 累计 `issue.qty ≤ wo_line.qty_ordered × (1 + material.std_loss_rate)`

生成事件 `ISSUE.POSTED`，B 账扣减消耗。

### 5.2 工序报工

```
POST /wip-reports
```

**请求体:**
```json
{
  "wo_no": "WO-20261103-001",
  "process_code": "smt",
  "process_seq": 1,
  "qty_in": 1200,
  "qty_out": 1180,
  "qty_scrap": 12,
  "scrap_reason": "drop",
  "reported_by": "operator_li"
}
```

**校验:** `qty_out + qty_scrap ≤ qty_in`

### 5.3 成品入库

```
POST /fg-receipts
```

**请求体:**
```json
{
  "wo_no": "WO-20261103-001",
  "sn": "BM1684X-2603-000123",
  "qty": 1,
  "lot_no": "L2604-A17-2603",
  "received_by": "operator_wang"
}
```

**校验:** `sn` 全局唯一。累计入库 = 工单数量时触发单耗核算。

---

## 6. 对账域 `/reconciliation`

### 6.1 触发自动核对（管理员/定时）

```
POST /reconciliation/{period}/run
```

手动触发或由定时任务 (02:00) 调用。计算期间内 A/B/C 三账差异，生成 `recon_item`。

### 6.2 查询对账期间

```
GET /reconciliation?period=2026-10&idh_id=IDH001
```

**响应:**
```json
{
  "code": 0,
  "data": {
    "period": "2026-10",
    "idh_id": "IDH001",
    "status": "open",
    "summary": {
      "total_items": 15,
      "matched": 10,
      "diff_count": 5,
      "diff_rate": 0.003,
      "diff_code_breakdown": { "D01": 1, "D03": 2, "D04": 2 }
    }
  }
}
```

### 6.3 查询差异明细

```
GET /reconciliation/{period_id}/items?status=pending&diff_code=D03&page=1
```

### 6.4 差异申辩

```
POST /reconciliation/{period_id}/items/{item_id}/dispute
```

**请求体:**
```json
{
  "reason": "领用后已报工，但系统未同步",
  "attachments": ["s3://receipts/photo_20261103_001.jpg"],
  "proposed_action": "补录报工数据"
}
```

48 小时申辩窗口。同时自动创建 `conv_type=recon` 的 CollabChat 对话。

### 6.5 创建调整单

```
POST /adjustments
```

**请求体:**
```json
{
  "period_id": 1,
  "recon_item_id": 5,
  "lot_no": "L2604-A17-2603",
  "qty_before": 1820,
  "qty_after": 1790,
  "diff_code": "D04",
  "reason": "12 颗报废未申报，现场核查属实"
}
```

> 调整单需**双签**后生效（原厂 1 人 + IDH 1 人电子签）。只有调整单，没有直接改数。

### 6.6 签批调整单

```
POST /adjustments/{adj_no}/approve
```

**请求体:**
```json
{
  "role": "factory"
}
```

双方都签批后状态 → `approved`，调整生效，库存台账更新。

### 6.7 锁账

```
POST /reconciliation/{period_id}/lock
```

状态 `adjusting → locked`。生成对账单 PDF、双签存档。锁账后调整进入下期。

---

## 7. 预警域 `/alerts`

### 7.1 查询预警

```
GET /alerts?status=open&severity=critical&page=1
```

### 7.2 确认预警

```
POST /alerts/{alert_id}/acknowledge
```

### 7.3 关闭预警

```
POST /alerts/{alert_id}/resolve
```

**请求体:**
```json
{
  "resolution": "已补发 50 颗安全库存，预计 D+2 到货"
}
```

关闭时必须附处理摘要。同时自动创建预警处理线程对话。

---

## 8. 协同沟通域 `/conversations`

### 8.1 获取或创建对话

```
GET /conversations?conv_type=wo&ref_id=WO-20261103-001
```

若已存在返回现有对话；若不存在返回 200 带空 data，客户端调 POST 创建。

### 8.2 创建对话

```
POST /conversations
```

**请求体:**
```json
{
  "conv_type": "wo",
  "ref_id": "WO-20261103-001",
  "title": "WO-20261103-001 沟通",
  "member_ids": ["user_factory_01", "user_idh_01"]
}
```

### 8.3 发送消息

```
POST /conversations/{conv_id}/messages
```

**请求体:**
```json
{
  "msg_type": "text",
  "content": "L2604-A17-2603 批次的 1200 颗已领料投产",
  "parent_msg_id": null
}
```

> 消息只追加，不可编辑删除。

### 8.4 查询消息列表

```
GET /conversations/{conv_id}/messages?before=2026-11-03T10:00:00Z&limit=50
```

按时间倒序游标分页。

### 8.5 添加消息标签

```
POST /messages/{msg_id}/tags
```

**请求体:**
```json
{
  "tag_type": "commitment",
  "tag_value": "2026-12-18",
  "tagged_by": "ai",
  "confidence": 0.92
}
```

### 8.6 按标签查询消息（AI 分析用）

```
GET /messages/search?tag_type=commitment&ref_id=WO-20261103-001
```

---

## 9. AI 服务 `/ai`

> AI 推理全部私有化部署，不走公有云 API。

### 9.1 单据结构化

```
POST /ai/structurize-document
```

**请求体 (multipart/form-data):**
```
file: <PDF 工单合同/装箱单/送货单>
doc_type: work_order | packing_list | delivery_note
```

**响应:**
```json
{
  "code": 0,
  "data": {
    "fields": [
      { "key": "material_code", "value": "BM1684X", "confidence": 0.96 },
      { "key": "qty", "value": 10000, "confidence": 0.99 },
      { "key": "due_date", "value": "2026-12-15", "confidence": 0.88 }
    ],
    "raw_text": "...",
    "needs_review": true
  }
}
```

### 9.2 差异归因

```
POST /ai/attribute-diff
```

**请求体:**
```json
{
  "recon_item_id": 5,
  "include_chat_context": true
}
```

**响应:**
```json
{
  "code": 0,
  "data": {
    "hypotheses": [
      {
        "rank": 1,
        "cause": "领用但未报工：聊天记录提到 21 号投产，但系统无 WIP.REPORTED",
        "confidence": "high",
        "evidence_event_ids": ["evt-003087", "evt-003088"],
        "evidence_chat_msg_ids": ["msg-0042"],
        "suggested_action": "联系 operator_zhang 确认是否已贴片完成，补报 WIP",
        "owner_suggestion": "IDH"
      }
    ]
  }
}
```

### 9.3 自然语言问数

```
POST /ai/query
```

**请求体:**
```json
{
  "query": "上个月 BM1684X 在 IDH001 的库存差异多少，主因是什么"
}
```

**响应:**
```json
{
  "code": 0,
  "data": {
    "answer": "2026-10 期间，BM1684X 在 IDH001 的差异为 -20 颗（系统差异）和 +30 颗（实物差异）。主因为 D03 领用未报工（2 笔）和 D04 报废未申报（2 笔）。",
    "sql": "SELECT ...",
    "chart_data": { ... },
    "sources": ["recon_item.id=5", "recon_item.id=7"]
  }
}
```

---

## 10. Webhook 事件推送

### 10.1 事件订阅

```
POST /webhooks/subscribe
```

**请求体:**
```json
{
  "url": "https://idh-erp.example.com/webhook/idh-platform",
  "event_types": ["WO.ISSUED", "DN.SHIPPED", "RECON.LOCKED"],
  "secret": "whsec_..."
}
```

### 10.2 推送格式

```
POST {subscriber_url}
X-Webhook-Signature: sha256=...
X-Webhook-Id: wh_abc123
```

**请求体:**
```json
{
  "event_id": "evt-123456",
  "event_type": "WO.ISSUED",
  "ts": "2026-11-03T08:00:00+08:00",
  "payload": {
    "wo_no": "WO-20261103-001",
    "idh_id": "IDH001",
    "status": "issued"
  }
}
```

**重试策略:** 首次失败后 1min/5min/15min/1h/6h 各重试一次，5 次全失败后标记 dead。

---

## 11. 汇总：API 端点清单

| 方法 | 路径 | 说明 | 域 |
|------|------|------|----|
| `POST` | `/work-orders` | 创建工单 | 工单 |
| `POST` | `/work-orders/{wo}/issue` | 下达工单 | 工单 |
| `POST` | `/work-orders/{wo}/accept` | IDH 接单 | 工单 |
| `POST` | `/work-orders/{wo}/change` | 变更/暂停/取消 | 工单 |
| `GET` | `/work-orders` | 工单列表 | 工单 |
| `GET` | `/work-orders/{wo}` | 工单详情 | 工单 |
| `POST` | `/shipments` | 创建发货单 | 发运 |
| `POST` | `/shipments/{dn}/confirm` | 确认发货 | 发运 |
| `GET` | `/shipments` | 发货单列表 | 发运 |
| `GET` | `/shipments/{dn}` | 发货单详情 | 发运 |
| `POST` | `/goods-receipts` | IDH 收货确认 | 发运 |
| `GET` | `/inventory/stock` | 库存查询 | 库存 |
| `GET` | `/inventory/stock-ledger` | 库存流水 | 库存 |
| `GET` | `/inventory/trace/{sn}` | SN 追溯 | 库存 |
| `POST` | `/issues` | 领料投产 | 生产 |
| `POST` | `/wip-reports` | 工序报工 | 生产 |
| `POST` | `/fg-receipts` | 成品入库 | 生产 |
| `POST` | `/reconciliation/{period}/run` | 触发对账 | 对账 |
| `GET` | `/reconciliation` | 对账期间查询 | 对账 |
| `GET` | `/reconciliation/{pid}/items` | 差异明细 | 对账 |
| `POST` | `/reconciliation/{pid}/items/{id}/dispute` | 差异申辩 | 对账 |
| `POST` | `/adjustments` | 创建调整单 | 对账 |
| `POST` | `/adjustments/{adj}/approve` | 签批调整单 | 对账 |
| `POST` | `/reconciliation/{pid}/lock` | 锁账 | 对账 |
| `GET` | `/alerts` | 预警列表 | 预警 |
| `POST` | `/alerts/{id}/acknowledge` | 确认预警 | 预警 |
| `POST` | `/alerts/{id}/resolve` | 关闭预警 | 预警 |
| `GET` | `/conversations` | 获取对话 | 通信 |
| `POST` | `/conversations` | 创建对话 | 通信 |
| `POST` | `/conversations/{cid}/messages` | 发送消息 | 通信 |
| `GET` | `/conversations/{cid}/messages` | 消息列表 | 通信 |
| `POST` | `/messages/{mid}/tags` | 添加标签 | 通信 |
| `GET` | `/messages/search` | 标签检索 | 通信 |
| `POST` | `/ai/structurize-document` | 单据结构化 | AI |
| `POST` | `/ai/attribute-diff` | 差异归因 | AI |
| `POST` | `/ai/query` | 自然语言问数 | AI |
| `POST` | `/webhooks/subscribe` | 事件订阅 | Webhook |

---

> 配套文档: [ARCHITECTURE.md](./ARCHITECTURE.md) · [DATABASE.md](./DATABASE.md) · [FRONTEND.md](./FRONTEND.md) · [DEPLOYMENT.md](./DEPLOYMENT.md) · [DESIGN_SYSTEM.md](./DESIGN_SYSTEM.md)