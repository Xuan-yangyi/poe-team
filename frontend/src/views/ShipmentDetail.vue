<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getShipment, confirmShipment, createGoodsReceipt } from '@/api/shipment'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const shipment = ref<any>(null)
const receiptForm = ref({ dn_no: '', container_id: '', lot_id: '', qty_received: 0, qty_shipped: 0, diff_reason: '', received_by: '' })
const receiptVisible = ref(false)

async function fetch() {
  loading.value = true
  try {
    const resp = await getShipment(route.params.id as string)
    shipment.value = resp.data.data
    receiptForm.value.dn_no = shipment.value.dn_no
  } catch {
    ElMessage.error('加载发货单失败')
    router.push('/shipments')
  } finally { loading.value = false }
}

async function handleConfirm() {
  try {
    await confirmShipment(shipment.value.id)
    ElMessage.success('发货已确认')
    fetch()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail?.message || '确认失败')
  }
}

async function submitReceipt() {
  try {
    await createGoodsReceipt(receiptForm.value)
    ElMessage.success('收货登记成功')
    receiptVisible.value = false
    fetch()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail?.message || '登记失败')
  }
}

onMounted(fetch)
</script>

<template>
  <div class="page" v-loading="loading">
    <el-button text @click="router.push('/shipments')">← 返回发货列表</el-button>
    <template v-if="shipment">
      <h3>发货单详情 — {{ shipment.dn_no }}</h3>
      <el-descriptions :column="3" border style="margin-bottom: 20px">
        <el-descriptions-item label="发货单号">{{ shipment.dn_no }}</el-descriptions-item>
        <el-descriptions-item label="关联工单">{{ shipment.wo_id }}</el-descriptions-item>
        <el-descriptions-item label="IDH">{{ shipment.idh_id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag>{{ shipment.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="预计到货">{{ shipment.eta }}</el-descriptions-item>
        <el-descriptions-item label="承运商">{{ shipment.carrier }}</el-descriptions-item>
        <el-descriptions-item label="运单号">{{ shipment.tracking_no }}</el-descriptions-item>
      </el-descriptions>

      <div style="margin-bottom: 12px">
        <el-button v-if="shipment.status === 'draft'" type="primary" @click="handleConfirm">确认发货</el-button>
        <el-button type="success" @click="receiptVisible = true">登记收货</el-button>
      </div>

      <el-dialog v-model="receiptVisible" title="收货登记" width="500px">
        <el-form label-width="100px">
          <el-form-item label="发货单号"><el-input v-model="receiptForm.dn_no" disabled /></el-form-item>
          <el-form-item label="容器ID"><el-input v-model="receiptForm.container_id" /></el-form-item>
          <el-form-item label="批次"><el-input v-model="receiptForm.lot_id" /></el-form-item>
          <el-form-item label="实收数量"><el-input-number v-model="receiptForm.qty_received" :min="0" /></el-form-item>
          <el-form-item label="发货数量"><el-input-number v-model="receiptForm.qty_shipped" :min="0" /></el-form-item>
          <el-form-item label="差异原因"><el-input v-model="receiptForm.diff_reason" /></el-form-item>
          <el-form-item label="签收人"><el-input v-model="receiptForm.received_by" /></el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="receiptVisible = false">取消</el-button>
          <el-button type="primary" @click="submitReceipt">确认</el-button>
        </template>
      </el-dialog>
    </template>
  </div>
</template>