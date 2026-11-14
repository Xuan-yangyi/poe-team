<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listAlerts, acknowledgeAlert, resolveAlert } from '@/api/alert'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const filters = ref({
  status: '',
  alert_type: '',
  severity: '',
})

async function fetch() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: page.value, page_size: pageSize.value }
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.alert_type) params.alert_type = filters.value.alert_type
    if (filters.value.severity) params.severity = filters.value.severity
    const resp = await listAlerts(params)
    rows.value = resp.data.data
    total.value = resp.data.meta?.total || 0
  } catch {
    ElMessage.error('加载告警失败')
  } finally {
    loading.value = false
  }
}

async function handleAck(alertId: string) {
  try {
    await acknowledgeAlert(alertId, { acknowledged_by: 'current_user' })
    ElMessage.success('已确认')
    fetch()
  } catch {
    ElMessage.error('确认失败')
  }
}

async function handleResolve(alertId: string) {
  try {
    const { value } = await ElMessageBox.prompt('请输入处理说明', '关闭告警')
    await resolveAlert(alertId, { resolved_by: 'current_user', resolution: value || '' })
    ElMessage.success('已关闭')
    fetch()
  } catch {
    // cancelled
  }
}

onMounted(fetch)
</script>

<template>
  <div class="page">
    <h3>告警中心</h3>

    <el-row :gutter="12" style="margin-bottom: 16px">
      <el-col :span="5">
        <el-select v-model="filters.status" placeholder="状态" clearable @change="fetch">
          <el-option label="未处理" value="open" />
          <el-option label="已确认" value="acknowledged" />
          <el-option label="已关闭" value="resolved" />
        </el-select>
      </el-col>
      <el-col :span="5">
        <el-select v-model="filters.severity" placeholder="严重程度" clearable @change="fetch">
          <el-option label="严重" value="critical" />
          <el-option label="警告" value="warning" />
          <el-option label="信息" value="info" />
        </el-select>
      </el-col>
      <el-col :span="4">
        <el-button type="primary" @click="fetch">查询</el-button>
      </el-col>
    </el-row>

    <el-table :data="rows" v-loading="loading" stripe border>
      <el-table-column prop="alert_type" label="类型" width="120" />
      <el-table-column prop="severity" label="严重程度" width="100">
        <template #default="{ row }">
          <el-tag :type="row.severity === 'critical' ? 'danger' : row.severity === 'warning' ? 'warning' : 'info'">
            {{ row.severity }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="200" />
      <el-table-column prop="detail" label="详情" min-width="250" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'open' ? 'danger' : row.status === 'acknowledged' ? 'warning' : 'success'">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="acknowledged_by" label="确认人" width="100" />
      <el-table-column prop="resolved_by" label="处理人" width="100" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'open'"
            size="small"
            type="warning"
            @click="handleAck(row.id)"
          >确认</el-button>
          <el-button
            v-if="row.status === 'open' || row.status === 'acknowledged'"
            size="small"
            type="success"
            @click="handleResolve(row.id)"
          >关闭</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page"
      :page-size="pageSize"
      :total="total"
      layout="total, prev, pager, next"
      style="margin-top: 16px; justify-content: flex-end"
      @current-change="fetch"
    />
  </div>
</template>