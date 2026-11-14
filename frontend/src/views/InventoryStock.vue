<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getStock } from '@/api/inventory'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const filters = ref({
  material_id: '',
  lot_id: '',
  status: '',
  owner: '',
})

async function fetch() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: page.value, page_size: pageSize.value }
    if (filters.value.material_id) params.material_id = filters.value.material_id
    if (filters.value.lot_id) params.lot_id = filters.value.lot_id
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.owner) params.owner = filters.value.owner
    const resp = await getStock(params)
    rows.value = resp.data.data
    total.value = resp.data.meta?.total || 0
  } catch {
    ElMessage.error('加载库存失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetch)
</script>

<template>
  <div class="page">
    <h3>库存管理</h3>

    <el-row :gutter="12" style="margin-bottom: 16px">
      <el-col :span="5">
        <el-input v-model="filters.material_id" placeholder="物料ID" clearable @keyup.enter="fetch" />
      </el-col>
      <el-col :span="5">
        <el-input v-model="filters.lot_id" placeholder="批次ID" clearable @keyup.enter="fetch" />
      </el-col>
      <el-col :span="4">
        <el-select v-model="filters.status" placeholder="状态" clearable @change="fetch">
          <el-option label="可用" value="available" />
          <el-option label="已预留" value="reserved" />
          <el-option label="已消耗" value="consumed" />
        </el-select>
      </el-col>
      <el-col :span="4">
        <el-select v-model="filters.owner" placeholder="归属" clearable @change="fetch">
          <el-option label="原厂" value="factory" />
          <el-option label="IDH" value="idh" />
        </el-select>
      </el-col>
      <el-col :span="4">
        <el-button type="primary" @click="fetch">查询</el-button>
      </el-col>
    </el-row>

    <el-table :data="rows" v-loading="loading" stripe border>
      <el-table-column prop="material_id" label="物料ID" width="250" />
      <el-table-column prop="lot_id" label="批次ID" width="250" />
      <el-table-column prop="idh_id" label="IDH" width="100" />
      <el-table-column prop="owner" label="归属" width="80" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'available' ? 'success' : row.status === 'reserved' ? 'warning' : 'info'">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="qty_change" label="变动数量" width="100" />
      <el-table-column prop="qty_after" label="结余" width="100" />
      <el-table-column prop="event_type" label="来源事件" min-width="160" />
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