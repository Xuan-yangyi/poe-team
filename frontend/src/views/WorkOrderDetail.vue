<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getWorkOrder, issueWorkOrder, acceptWorkOrder, changeWorkOrder } from '@/api/work-order'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const wo = ref<any>(null)
const lines = ref<any[]>([])

const changeForm = ref({ visible: false, qty: 0, lineIndex: -1 })

async function fetch() {
  loading.value = true
  try {
    const resp = await getWorkOrder(route.params.id as string)
    wo.value = resp.data.data
    lines.value = resp.data.data.lines || []
  } catch {
    ElMessage.error('加载工单失败')
    router.push('/work-orders')
  } finally {
    loading.value = false
  }
}

async function handleIssue() {
  try {
    await issueWorkOrder(wo.value.id)
    ElMessage.success('工单已发行')
    fetch()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail?.message || '发行失败')
  }
}

async function handleAccept() {
  try {
    await acceptWorkOrder(wo.value.id)
    ElMessage.success('已接单')
    fetch()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail?.message || '接单失败')
  }
}

function openChange(lineIndex: number) {
  changeForm.value = { visible: true, qty: lines.value[lineIndex].qty_ordered, lineIndex }
}

async function handleChange() {
  try {
    await changeWorkOrder(wo.value.id, { line_index: changeForm.value.lineIndex, qty: changeForm.value.qty })
    ElMessage.success('变更成功')
    changeForm.value.visible = false
    fetch()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail?.message || '变更失败')
  }
}

onMounted(fetch)
</script>

<template>
  <div class="page" v-loading="loading">
    <el-button text @click="router.push('/work-orders')">← 返回工单列表</el-button>
    <template v-if="wo">
      <h3>工单详情 — {{ wo.wo_no }}</h3>
      <el-descriptions :column="3" border style="margin-bottom: 20px">
        <el-descriptions-item label="IDH">{{ wo.idh_id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="wo.status === 'issued' ? 'success' : ''">{{ wo.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="终端客户">{{ wo.customer_id }}</el-descriptions-item>
        <el-descriptions-item label="BOM版本">{{ wo.bom_ver }}</el-descriptions-item>
        <el-descriptions-item label="结算方式">{{ wo.settle_mode }}</el-descriptions-item>
        <el-descriptions-item label="优先级">{{ wo.priority }}</el-descriptions-item>
        <el-descriptions-item label="交期">{{ wo.due_date }}</el-descriptions-item>
        <el-descriptions-item label="确认交期">{{ wo.confirmed_due_date }}</el-descriptions-item>
      </el-descriptions>

      <div style="margin-bottom: 12px">
        <el-button v-if="wo.status === 'draft'" type="primary" @click="handleIssue">发行</el-button>
        <el-button v-if="wo.status === 'issued'" type="success" @click="handleAccept">接单</el-button>
      </div>

      <h4>物料明细</h4>
      <el-table :data="lines" stripe border>
        <el-table-column prop="line_no" label="行号" width="60" />
        <el-table-column prop="material_id" label="物料" width="250" />
        <el-table-column prop="qty_ordered" label="下单量" width="100" />
        <el-table-column prop="qty_shipped" label="已发" width="80" />
        <el-table-column prop="qty_received" label="已收" width="80" />
        <el-table-column prop="qty_consumed" label="已耗" width="80" />
        <el-table-column prop="unit_price" label="单价" width="100" />
        <el-table-column label="操作" width="80">
          <template #default="{ $index }">
            <el-button size="small" @click="openChange($index)">变更</el-button>
          </template>
        </el-table-column>
      </el-table>
    </template>

    <el-dialog v-model="changeForm.visible" title="变更数量" width="400px">
      <el-input-number v-model="changeForm.qty" :min="1" style="width: 100%" />
      <template #footer>
        <el-button @click="changeForm.visible = false">取消</el-button>
        <el-button type="primary" @click="handleChange">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>