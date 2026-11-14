<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listWorkOrders } from '@/api/work-order'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const filters = ref({
  status: '',
  idh_id: '',
})

async function fetch() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: page.value, page_size: pageSize.value }
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.idh_id) params.idh_id = filters.value.idh_id
    const resp = await listWorkOrders(params)
    rows.value = resp.data.data
    total.value = resp.data.meta?.total || 0
  } catch (e: any) {
    ElMessage.error('加载工单失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetch)
</script>

<template>
  <div class="page">
    <h3>工单管理</h3>

    <el-row :gutter="12" style="margin-bottom: 16px">
      <el-col :span="6">
        <el-select v-model="filters.status" placeholder="状态" clearable @change="fetch">
          <el-option label="草稿" value="draft" />
          <el-option label="已发行" value="issued" />
          <el-option label="已接单" value="accepted" />
          <el-option label="生产中" value="in_progress" />
          <el-option label="已完成" value="completed" />
        </el-select>
      </el-col>
      <el-col :span="6">
        <el-input v-model="filters.idh_id" placeholder="IDH客户" clearable @keyup.enter="fetch" />
      </el-col>
      <el-col :span="4">
        <el-button type="primary" @click="fetch">查询</el-button>
      </el-col>
    </el-row>

    <el-table :data="rows" v-loading="loading" stripe border style="width: 100%">
      <el-table-column prop="wo_no" label="工单号" width="200" />
      <el-table-column prop="idh_id" label="IDH" width="120" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'issued' ? 'success' : row.status === 'draft' ? 'info' : ''">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="customer_id" label="终端客户" width="120" />
      <el-table-column prop="due_date" label="交期" width="120" />
      <el-table-column prop="settle_mode" label="结算方式" width="100" />
      <el-table-column prop="priority" label="优先级" width="80" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" @click="$router.push(`/work-orders/${row.id}`)">详情</el-button>
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