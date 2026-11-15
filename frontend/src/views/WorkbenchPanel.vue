<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const modules = [
  {
    key: 'work-orders',
    label: '工单管理',
    desc: '创建、发行、变更工单',
    color: '#409eff',
    icon: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z',
  },
  {
    key: 'shipments',
    label: '发货管理',
    desc: '出货确认、收货登记',
    color: '#67c23a',
    icon: 'M1 3h15v13H1z M16 8l4 6h-4z M19 14v7h-3v-7z',
  },
  {
    key: 'inventory',
    label: '库存管理',
    desc: '库存快照、批次流水',
    color: '#e6a23c',
    icon: 'M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z',
  },
  {
    key: 'production',
    label: '生产执行',
    desc: '领料、报工、成品入库',
    color: '#909399',
    icon: 'M12 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M12 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z',
  },
  {
    key: 'reconciliation',
    label: '对账管理',
    desc: '对账周期、差异处理',
    color: '#f56c6c',
    icon: 'M12 1v22 M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6',
  },
  {
    key: 'alerts',
    label: '告警中心',
    desc: '查看、确认、关闭告警',
    color: '#e040fb',
    icon: 'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z M12 8v4 M12 16h.01',
  },
  {
    key: 'agents',
    label: 'Agent 管理',
    desc: '创建AI角色、配置技能、加入群聊',
    color: '#00bcd4',
    icon: 'M12 2a4 4 0 0 1 4 4v2h3a1 1 0 0 1 1 1v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V9a1 1 0 0 1 1-1h3V6a4 4 0 0 1 4-4z M10 8h4V6a2 2 0 1 0-4 0v2z M9 13h6 M9 17h6',
  },
  ]

function navigate(key: string) {
  router.push(`/${key}`)
}
</script>

<template>
  <div class="workbench">
    <div class="wb-header">
      <h2>工作台</h2>
      <span class="wb-subtitle">选择业务模块开始处理</span>
    </div>
    <div class="wb-grid">
      <div
        v-for="m in modules"
        :key="m.key"
        class="wb-card"
        @click="navigate(m.key)"
      >
        <div class="wb-card-icon" :style="{ background: m.color }">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path :d="m.icon" />
          </svg>
        </div>
        <div class="wb-card-body">
          <div class="wb-card-title">{{ m.label }}</div>
          <div class="wb-card-desc">{{ m.desc }}</div>
        </div>
        <svg class="wb-card-arrow" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#c0c4cc" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
      </div>
    </div>
  </div>
</template>

<style scoped>
.workbench {
  flex: 1;
  padding: 24px 32px;
  background: #f5f7fa;
  overflow-y: auto;
}

.wb-header {
  margin-bottom: 24px;
}

.wb-header h2 {
  font-size: 22px;
  color: #303133;
  margin: 0 0 4px;
}

.wb-subtitle {
  font-size: 14px;
  color: #909399;
}

.wb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.wb-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #fff;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.wb-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.wb-card-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.wb-card-body {
  flex: 1;
  min-width: 0;
}

.wb-card-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.wb-card-desc {
  font-size: 13px;
  color: #909399;
  margin-top: 2px;
}

.wb-card-arrow {
  flex-shrink: 0;
}
</style>