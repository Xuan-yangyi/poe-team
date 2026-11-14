<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listShipments } from '@/api/shipment'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const filters = ref({ status: '', idh_id: '' })

async function fetch() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: page.value, page_size: pageSize.value }
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.idh_id) params.idh_id = filters.value.idh_id
    const resp = await listShipments(params)
    rows.value = resp.data.data
    total.value = resp.data.meta?.total || 0
  } catch {
    ElMessage.error('加载发货记录失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetch)
</script>

<template>
  <div class="page">
    <h3>发货管理</h3>

    <el-row :gutter="12" style="margin-bottom: 16px">
      <el-col :span="6">
        <el-select v-model="filters.status" placeholder="状态" clearable @change="fetch">
          <el-option label="草稿" value="draft" />
          <el-option label="已确认" value="confirmed" />
          <el-option label="运输中" value="in_transit" />
          <el-option label="已签收" value="delivered" />
        </el-select>
      </el-col>
      <el-col :span="6">
        <el-input v-model="filters.idh_id" placeholder="IDH" clearable @keyup.enter="fetch" />
      </el-col>
      <el-col :span="4">
        <el-button type="primary" @click="fetch">查询</el-button>
      </el-col>
    </el-row>

    <el-table :data="rows" v-loading="loading" stripe border>
      <el-table-column prop="dn_no" label="发货单号" width="200" />
      <el-table-column prop="wo_id" label="关联工单" width="200" />
      <el-table-column prop="idh_id" label="IDH" width="120" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'delivered' ? 'success' : ''">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="eta" label="预计到货" width="120" />
      <el-table-column prop="carrier" label="承运商" width="120" />
      <el-table-column prop="tracking_no" label="运单号" width="180" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" @click="$router.push(`/shipments/${row.id}`)">详情</el-button>
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