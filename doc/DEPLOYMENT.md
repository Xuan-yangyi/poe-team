# IDH 协同平台 · 部署运维文档

> 版本: V1.0 | 日期: 2026-11 | 首期: Docker Compose | 规模化: Kubernetes

---

## 1. 部署架构总览

### 1.1 基础设施拓扑

```
                        ┌──────────────┐
                        │   用户/IDH    │
                        └──────┬───────┘
                               │ HTTPS (TLS 1.3)
                        ┌──────┴───────┐
                        │   Nginx       │
                        │   (反向代理)   │
                        └──────┬───────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
       ┌──────┴──────┐ ┌──────┴──────┐ ┌──────┴──────┐
       │  Frontend    │ │  Backend ×2  │ │  AI Service  │
       │  (Nginx)     │ │  (SpringBoot)│ │  (FastAPI)   │
       └─────────────┘ └──────┬──────┘ └──────┬──────┘
                              │                │
              ┌───────────────┼────────────────┼───────────────┐
              │               │                │               │
       ┌──────┴──────┐ ┌──────┴──────┐ ┌──────┴──────┐ ┌──────┴──────┐
       │ PostgreSQL   │ │   Redis     │ │   Kafka     │ │   MinIO     │
       │ (Patroni ×3) │ │  (Sentinel) │ │  (KRaft ×3) │ │  (单节点)    │
       └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
              │
       ┌──────┴──────┐
       │ ClickHouse/  │
       │ Doris (OLAP) │
       └─────────────┘
```

### 1.2 部署模式

| 模式 | 环境 | 规模 | 工具 | 说明 |
|------|------|------|------|------|
| **MVP 模式** | 开发/小规模生产 | 1-2 台服务器 | Docker Compose | 单机部署所有服务 |
| **生产模式** | 正式生产 | 3+ 台服务器 | Kubernetes | 高可用、水平扩展 |

---

## 2. Docker Compose 部署（MVP 模式）

### 2.1 目录结构

```
docker/
├── docker-compose.yml          # 主编排文件
├── .env                        # 环境变量（生产值 → .env.prod）
├── nginx/
│   └── nginx.conf              # 反向代理配置
├── postgres/
│   └── init/                   # 初始化 SQL
│       ├── 01-create-db.sql
│       └── 02-create-extensions.sql
├── kafka/
│   └── kraft-setup.sh          # KRaft 模式初始化
└── ai-service/
    ├── Dockerfile
    └── models/                  # 模型挂载目录（外部存储）
        ├── Qwen2.5-32B-Instruct/
        └── bge-m3/
```

### 2.2 docker-compose.yml

```yaml
version: '3.8'

services:
  # ==================== 反向代理 ====================
  nginx:
    image: nginx:1.25-alpine
    container_name: idh-nginx
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
      - frontend_dist:/var/www/frontend:ro
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - idh-net

  # ==================== 后端服务 ====================
  backend:
    build:
      context: ../backend
      dockerfile: Dockerfile
    container_name: idh-backend
    environment:
      - SPRING_PROFILES_ACTIVE=prod
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - REDIS_HOST=redis
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - MINIO_ENDPOINT=http://minio:9000
      - JWT_SECRET=${JWT_SECRET}
      - AI_SERVICE_URL=http://ai-service:8000
    expose:
      - "8080"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - idh-net

  # ==================== AI 推理服务 ====================
  ai-service:
    build:
      context: ../ai-service
      dockerfile: Dockerfile
    container_name: idh-ai
    environment:
      - MODEL_PATH=/models/Qwen2.5-32B-Instruct
      - EMBEDDING_MODEL=/models/bge-m3
      - GPU_MEMORY_UTILIZATION=0.90
    expose:
      - "8000"
    volumes:
      - ${MODEL_STORAGE_PATH:-./ai-service/models}:/models:ro
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 2
              capabilities: [gpu]
    restart: unless-stopped
    networks:
      - idh-net
    # 如果没有 GPU，用 CPU 模式 (注释掉 deploy.resources，取消下面注释):
    # command: ["--cpu-only"]

  # ==================== PostgreSQL 数据库 ====================
  postgres:
    image: pgvector/pgvector:pg15
    container_name: idh-postgres
    environment:
      - POSTGRES_DB=${DB_NAME}
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres/init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - idh-net

  # ==================== Redis 缓存 ====================
  redis:
    image: redis:7-alpine
    container_name: idh-redis
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    expose:
      - "6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    restart: unless-stopped
    networks:
      - idh-net

  # ==================== Kafka 消息队列 ====================
  kafka:
    image: apache/kafka:3.6.1
    container_name: idh-kafka
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: 'broker,controller'
      KAFKA_LISTENERS: 'PLAINTEXT://:9092,CONTROLLER://:9093'
      KAFKA_ADVERTISED_LISTENERS: 'PLAINTEXT://kafka:9092'
      KAFKA_CONTROLLER_LISTENER_NAMES: 'CONTROLLER'
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: 'CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT'
      KAFKA_CONTROLLER_QUORUM_VOTERS: '1@kafka:9093'
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
    expose:
      - "9092"
    volumes:
      - kafka_data:/var/lib/kafka/data
    restart: unless-stopped
    networks:
      - idh-net

  # ==================== MinIO 对象存储 ====================
  minio:
    image: minio/minio:latest
    container_name: idh-minio
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=${MINIO_USER}
      - MINIO_ROOT_PASSWORD=${MINIO_PASSWORD}
    ports:
      - "9000:9000"   # API
      - "9001:9001"   # Console
    volumes:
      - minio_data:/data
    restart: unless-stopped
    networks:
      - idh-net

  # ==================== 分析数据库 (可选) ====================
  clickhouse:
    image: clickhouse/clickhouse-server:latest
    container_name: idh-clickhouse
    environment:
      - CLICKHOUSE_DB=${CLICKHOUSE_DB}
      - CLICKHOUSE_USER=${CLICKHOUSE_USER}
      - CLICKHOUSE_PASSWORD=${CLICKHOUSE_PASSWORD}
    ports:
      - "8123:8123"
      - "9009:9009"
    volumes:
      - clickhouse_data:/var/lib/clickhouse
    restart: unless-stopped
    profiles:
      - full    # 仅在 --profile full 时启动
    networks:
      - idh-net

  # ==================== 数据库迁移 ====================
  flyway:
    image: flyway/flyway:10
    container_name: idh-flyway
    command: -url=jdbc:postgresql://postgres:5432/${DB_NAME}
             -user=${DB_USER} -password=${DB_PASSWORD}
             -locations=filesystem:/migrations migrate
    volumes:
      - ../migration:/migrations:ro
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - idh-net
    profiles:
      - init    # 仅在首次初始化时运行

volumes:
  frontend_dist:
  postgres_data:
  redis_data:
  kafka_data:
  minio_data:
  clickhouse_data:

networks:
  idh-net:
    driver: bridge
```

### 2.3 .env 文件

```bash
# 数据库
DB_NAME=idh_platform
DB_USER=idh_app
DB_PASSWORD=<生成强密码>

# Redis
REDIS_PASSWORD=<生成强密码>

# JWT
JWT_SECRET=<生成 256-bit 随机密钥>

# MinIO
MINIO_USER=idh_admin
MINIO_PASSWORD=<生成强密码>

# ClickHouse (可选)
CLICKHOUSE_DB=idh_analytics
CLICKHOUSE_USER=idh_readonly
CLICKHOUSE_PASSWORD=<生成强密码>

# AI 模型存储路径
MODEL_STORAGE_PATH=/data/models
```

### 2.4 首次启动

```bash
# 1. 生成密钥
openssl rand -base64 32  > jwt_secret.txt
openssl rand -base64 24  > db_password.txt

# 2. 初始化数据库（仅首次）
docker compose --profile init up flyway

# 3. 启动全部服务
docker compose up -d

# 4. 启动含分析库（可选）
docker compose --profile full up -d

# 5. 检查状态
docker compose ps
docker compose logs -f backend
```

---

## 3. Kubernetes 部署（生产模式）

### 3.1 集群规划

| 节点类型 | 数量 | 规格建议 | 运行服务 |
|----------|------|---------|---------|
| Master | 3 | 4C8G | K8s 控制面 |
| App | 2+ | 8C16G | Backend (多副本), Nginx |
| Data | 3 | 16C32G + SSD | PostgreSQL (Patroni), Redis (Sentinel) |
| AI | 1-2 | 16C32G + 2×L20 GPU | AI Service |
| Storage | 3 | 8C16G + HDD | MinIO (分布式) |
| Queue | 3 | 8C16G | Kafka (KRaft) |

### 3.2 K8s 资源定义（关键部分）

#### backend-deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: idh-backend
  namespace: idh-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: idh-backend
  template:
    metadata:
      labels:
        app: idh-backend
    spec:
      containers:
        - name: backend
          image: registry.example.com/idh-backend:{{VERSION}}
          ports:
            - containerPort: 8080
          env:
            - name: SPRING_PROFILES_ACTIVE
              value: "k8s"
            - name: DB_HOST
              valueFrom:
                secretKeyRef:
                  name: idh-db-secret
                  key: host
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: idh-db-secret
                  key: password
          resources:
            requests:
              cpu: "1"
              memory: "2Gi"
            limits:
              cpu: "2"
              memory: "4Gi"
          livenessProbe:
            httpGet:
              path: /actuator/health/liveness
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /actuator/health/readiness
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: idh-backend-svc
  namespace: idh-platform
spec:
  selector:
    app: idh-backend
  ports:
    - port: 8080
      targetPort: 8080
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: idh-backend-hpa
  namespace: idh-platform
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: idh-backend
  minReplicas: 2
  maxReplicas: 8
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

#### ingress.yaml

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: idh-ingress
  namespace: idh-platform
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
    - hosts:
        - idh-platform.example.com
      secretName: idh-tls
  rules:
    - host: idh-platform.example.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: idh-backend-svc
                port:
                  number: 8080
          - path: /ws
            pathType: Prefix
            backend:
              service:
                name: idh-backend-svc
                port:
                  number: 8080
          - path: /
            pathType: Prefix
            backend:
              service:
                name: idh-frontend-svc
                port:
                  number: 80
```

### 3.3 PostgreSQL 高可用 (Patroni + etcd)

```
┌─────────┐    ┌─────────┐    ┌─────────┐
│ Patroni  │    │ Patroni  │    │ Patroni  │
│ Node 1   │◀──▶│ Node 2   │◀──▶│ Node 3   │
│ (Master) │    │(Replica) │    │(Replica) │
└────┬─────┘    └────┬─────┘    └────┬─────┘
     │               │               │
     └───────────────┼───────────────┘
                     │
              ┌──────┴──────┐
              │  etcd ×3    │
              │ (Leader选举) │
              └─────────────┘
```

- **Patroni**: 自动故障转移，Master 宕机后 30s 内提升 Replica
- **etcd**: 分布式配置存储，Leader 选举
- **pgBackRest**: WAL 归档 + 全量备份
- **连接串**: 应用连接 Patroni REST API 获取当前 Master 地址

### 3.4 Redis 哨兵模式

```
          ┌──────────┐
          │ Sentinel │ ×3
          └────┬─────┘
               │ 监控
    ┌──────────┼──────────┐
    │          │          │
┌───┴───┐ ┌───┴───┐ ┌───┴───┐
│Master │ │Slave 1│ │Slave 2│
└───────┘ └───────┘ └───────┘
```

- 3 个 Sentinel 节点监控 Master
- Master 故障时自动选举新 Master
- 应用通过 Sentinel 获取当前 Master 地址

---

## 4. 数据库运维

### 4.1 迁移管理 (Flyway)

```
migration/
├── V001__init_schema.sql          # 初始建表
├── V002__add_event_log_index.sql  # 事件日志索引
├── V003__seed_materials.sql       # 基础物料数据
├── V004__add_rls_policies.sql     # RLS 安全策略
└── ...
```

**迁移规则:**
- 版本号不可重复，不可修改已执行的迁移
- 所有迁移写入一个事务
- 生产环境禁止 `flyway:clean` 和 `flyway:repair`
- 发版前先在 staging 环境验证迁移

### 4.2 备份策略

| 类型 | 频率 | 保留 | 工具 |
|------|------|------|------|
| WAL 归档 | 持续 | 7 天 | pgBackRest |
| 全量备份 | 每日 01:00 | 30 天 | pgBackRest |
| 差异备份 | 每 6 小时 | 7 天 | pgBackRest |
| 异地备份 | 每日 | 90 天 | pgBackRest + S3 |

```bash
# pgBackRest 配置示例
[global]
repo1-path=/backup/pgbackrest
repo1-retention-full=30
repo1-retention-diff=7

[main]
pg1-path=/var/lib/postgresql/data
pg1-port=5432
```

### 4.3 恢复步骤

```bash
# 1. 停止应用
kubectl scale deployment idh-backend --replicas=0

# 2. 恢复数据库
pgbackrest --stanza=main --type=time \
  --target="2026-11-14 02:00:00+08:00" restore

# 3. 启动数据库
pg_ctl start

# 4. 验证数据
psql -c "SELECT count(*) FROM event_log WHERE created_at > '2026-11-14';"

# 5. 恢复应用
kubectl scale deployment idh-backend --replicas=3

# 6. 触发全量重算对账
curl -X POST https://idh-platform.example.com/api/reconciliation/2026-11/run
```

---

## 5. 监控与告警

### 5.1 监控栈

```
┌────────────────────────────────────────────┐
│ 应用层: Spring Boot Actuator + Micrometer   │
├────────────────────────────────────────────┤
│ 采集层: Prometheus + Node Exporter          │
├────────────────────────────────────────────┤
│ 可视化: Grafana                             │
├────────────────────────────────────────────┤
│ 告警:   Alertmanager → 企微 / 邮件          │
└────────────────────────────────────────────┘
```

### 5.2 关键监控指标

| 指标类别 | 具体指标 | 告警阈值 |
|----------|---------|---------|
| **系统** | CPU / 内存 / 磁盘 / 网络 | CPU > 80% / 磁盘 > 85% |
| **JVM** | Heap / GC / Threads | GC 暂停 > 1s |
| **数据库** | 连接数 / 慢查询 / 复制延迟 | 连接 > 80% / 延迟 > 5s |
| **业务** | API P95 延迟 / 错误率 / 扫码响应 | P95 > 1000ms / 错误 > 1% |
| **队列** | Kafka Lag / 消费者延迟 | Lag > 10000 |
| **对账** | 双轨不一致 / 对账失败 | 任何不一致立即告警 |

### 5.3 Grafana 仪表盘

| 仪表盘 | 内容 |
|--------|------|
| **系统概览** | 所有节点 CPU/内存/磁盘/网络 |
| **应用性能** | API QPS、延迟分布、错误率、JVM |
| **数据库** | 连接数、慢查询、复制状态、WAL 大小 |
| **业务指标** | 工单量、发货量、对账差异率、库存周转 |
| **Kafka** | 消息吞吐、Lag、消费者状态 |

### 5.4 日志

```yaml
# 日志格式 (JSON)
logging:
  pattern:
    console: |
      {
        "ts": "%d{ISO8601}",
        "level": "%level",
        "logger": "%logger",
        "thread": "%thread",
        "trace_id": "%mdc{traceId}",
        "tenant_id": "%mdc{tenantId}",
        "user_id": "%mdc{userId}",
        "message": "%msg"
      }
```

- 日志收集: Filebeat → Elasticsearch
- 日志保留: 热数据 7 天，冷数据 90 天 (S3)
- 审计日志 (event_log 表): 永久保留、只追加

---

## 6. 安全加固

### 6.1 网络安全

| 措施 | 说明 |
|------|------|
| TLS 1.3 | 全链路 HTTPS |
| 防火墙 | 仅开放 443 端口，内部端口仅集群内访问 |
| NetworkPolicy (K8s) | 按 namespace 隔离，仅 nginx 可访问 backend |
| WAF | 防 SQL 注入、XSS（可选，内网可省略） |

### 6.2 应用安全

| 措施 | 实现 |
|------|------|
| JWT 短期化 | Access Token 15min |
| 密码哈希 | bcrypt (cost=12) |
| SQL 注入防护 | JPA 参数化查询 |
| CORS | 仅允许白名单域名 |
| 速率限制 | Redis + 令牌桶，写操作 100/min/user |
| 幂等键去重 | `(tenant_id, idempotency_key)` 24h |
| 敏感字段加密 | `unit_price` 等字段存储加密 |

### 6.3 数据安全

| 措施 | 说明 |
|------|------|
| 租户隔离 | PostgreSQL RLS 强制过滤 |
| 字段脱敏 | IDH 侧不可见 `unit_price` 和 `customer_id` |
| 传输加密 | TLS 1.3 |
| 存储加密 | 磁盘级 LUKS 加密 |
| 备份加密 | pgBackRest 备份文件加密 |
| AI 数据 | **全私有化部署，数据不出内网** |
| 审计 | 不可篡改的 `event_log` |

### 6.4 密钥管理

```bash
# 所有密钥通过环境变量或 K8s Secret 注入
# 禁止硬编码在代码或配置文件中

# K8s Secret 示例
kubectl create secret generic idh-db-secret \
  --from-literal=host=patroni.idh-platform.svc \
  --from-literal=password=$(openssl rand -base64 32) \
  -n idh-platform

kubectl create secret generic idh-jwt-secret \
  --from-literal=secret=$(openssl rand -base64 64) \
  -n idh-platform
```

---

## 7. CI/CD 流水线

### 7.1 分支策略

```
main ──────────────────────────────────────────▶
  │
  ├── develop ─────────────────────────────────▶
  │     │
  │     ├── feature/wo-status-machine
  │     ├── feature/chat-websocket
  │     └── ...
  │
  └── hotfix/critical-bug
```

- `main`: 生产分支，仅通过 PR 合并
- `develop`: 开发分支
- `feature/*`: 功能分支
- `hotfix/*`: 紧急修复分支

### 7.2 Pipeline 阶段

```
Push → Build → Test → Security Scan → Deploy Staging → E2E Test → Deploy Prod
                       │                                      │
                       └── SAST (SonarQube)                   └── 人工审批
                           Dependency Scan (Trivy)
                           Container Scan
```

### 7.3 GitHub Actions 示例

```yaml
name: Build & Deploy

on:
  push:
    branches: [develop]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Java
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Build Backend
        run: cd backend && mvn -B package -DskipTests

      - name: Build Frontend
        run: cd frontend && npm ci && npm run build

      - name: Run Tests
        run: |
          cd backend && mvn test
          cd frontend && npm run test

      - name: Build Docker Images
        run: |
          docker build -t idh-backend:${{ github.sha }} backend/
          docker build -t idh-frontend:${{ github.sha }} frontend/

      - name: Push to Registry
        run: |
          docker push registry.example.com/idh-backend:${{ github.sha }}
          docker push registry.example.com/idh-frontend:${{ github.sha }}

  deploy-staging:
    needs: build
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Staging
        run: |
          kubectl set image deployment/idh-backend \
            backend=registry.example.com/idh-backend:${{ github.sha }} \
            -n idh-staging

  deploy-prod:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production  # 需要人工审批
    steps:
      - name: Deploy to Production
        run: |
          kubectl set image deployment/idh-backend \
            backend=registry.example.com/idh-backend:${{ github.sha }} \
            -n idh-platform
```

---

## 8. 容灾与故障处理

### 8.1 故障场景与应对

| 故障 | 影响 | 自动恢复 | 人工介入 |
|------|------|---------|---------|
| 单个 Backend Pod 宕机 | 无（K8s 自动重启） | ✅ K8s | — |
| PostgreSQL Master 故障 | 写入中断 ~30s | ✅ Patroni 自动切换 | 检查数据完整性 |
| Redis Master 故障 | 会话短暂失效 | ✅ Sentinel 自动切换 | — |
| Kafka Broker 故障 | 事件积压 | ✅ KRaft 自动选举 | 检查消费者 Lag |
| AI Service 故障 | AI 功能不可用 | ❌ | 重启或切 CPU 模式 |
| MinIO 故障 | 附件上传/下载不可用 | ❌ | 恢复备份 |
| 网络分区 | 部分节点不可达 | 部分 | 网络恢复后验证 |
| 全机房故障 | 全系统不可用 | ❌ | DR 切换 |

### 8.2 灾难恢复 (DR)

| 指标 | 目标 |
|------|------|
| RTO (恢复时间) | < 4 小时 |
| RPO (数据丢失) | < 1 小时 |
| DR 站点 | 异地机房，每日同步备份 |
| DR 演练 | 每季度一次 |

### 8.3 优雅降级

| 组件不可用 | 降级行为 |
|-----------|---------|
| ClickHouse/Doris | 对账查询回退到 PostgreSQL（限流 10 QPS） |
| AI Service | AI 功能显示"暂时不可用"，人工处理模式 |
| MinIO | 附件上传提示"稍后重试"，已有附件显示占位 |
| Kafka | 事件落本地 DB 队列，恢复后重放 |
| Redis | 会话降级到数据库（性能下降） |

---

## 9. 健康检查

### 9.1 健康端点

| 端点 | 用途 | 检查内容 |
|------|------|---------|
| `GET /actuator/health/liveness` | K8s Liveness | 进程是否存活 |
| `GET /actuator/health/readiness` | K8s Readiness | DB/Redis/Kafka 是否连通 |
| `GET /actuator/health` | 综合健康 | 所有组件状态汇总 |
| `GET /actuator/metrics` | Prometheus | 指标数据 |

### 9.2 检查脚本

```bash
#!/bin/bash
# check-health.sh - 定时拨测脚本

BASE_URL="https://idh-platform.example.com/api"
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"healthcheck","password":"..."}' | jq -r '.data.token')

# 检查关键接口
for endpoint in \
  "/work-orders?page=1&page_size=1" \
  "/inventory/stock?page=1&page_size=1" \
  "/alerts?page=1&page_size=1"
do
  status=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $TOKEN" \
    "$BASE_URL$endpoint")
  if [ "$status" != "200" ]; then
    echo "ALERT: $endpoint returned $status"
    # 触发告警
  fi
done

echo "Health check completed: $(date -Iseconds)"
```

---

## 10. 运维清单

### 10.1 日常检查

| 频率 | 项目 |
|------|------|
| 每日 | 检查 Grafana 仪表盘、告警处理、Kafka Lag |
| 每周 | 慢查询分析、磁盘使用趋势、备份验证 |
| 每月 | 安全补丁更新、证书到期检查、容量规划 |

### 10.2 对账窗口操作

```
每月 1 日 00:00 — 5 日 18:00 为对账窗口期

1. 00:00 — 系统自动冻结上月数据
2. 02:00 — 全量重算三账
3. 03:00 — 自动核对，生成差异报告
4. 08:00 — 通知 IDH 查看对账单
5. 1-2 日 — IDH 在线申辩 (48h 窗口)
6. 3-4 日 — 差异协商 + 调整单创建/双签
7. 5 日 18:00 — 锁账截止
8. 5 日后 — 生成对账 PDF，归档

窗口期内若系统故障:
  - < 2h: 窗口自动顺延
  - > 2h: 人工宣布延期通知
```

### 10.3 版本升级流程

```
1. 提前 3 天发送升级通知
2. 在 staging 环境验证完整流程
3. 升级前执行数据库全量备份
4. 灰度部署: 先 1 个 Pod → 观察 30min → 全量
5. 升级后验证: 健康检查 + 冒烟测试
6. 记录变更日志
```

---

> 配套文档: [ARCHITECTURE.md](./ARCHITECTURE.md) · [DATABASE.md](./DATABASE.md) · [API.md](./API.md) · [FRONTEND.md](./FRONTEND.md) · [DESIGN_SYSTEM.md](./DESIGN_SYSTEM.md)