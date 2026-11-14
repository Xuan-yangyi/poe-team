<script setup lang="ts">
import { ref } from 'vue'
import { createPeriod, getPeriod, getItems, disputeItem, createAdjustment, approveAdjustment } from '@/api/reconciliation'
import { ElMessage } from 'element-plus'

const activeTab = ref('period')

const periodForm = ref({ period: '', idh_id: '' })
const periodLoading = ref(false)
const period = ref<any>(null)
const items = ref<any[]>([])

const itemLoading = ref(false)
const periodId = ref('')

const disputeReason = ref('')
const adjForm = ref({ period_id: 0, recon_item_id: 0, lot_id: '', qty_before: 0, qty_after: 0, diff_code: '', reason: '' })

async function submitPeriod() {
  periodLoading.value = true
  try {
    const resp = await createPeriod(periodForm.value)
    ElMessage.success(`对账周期创建成功 id=${resp.data.data.id}`)
    period.value = resp.data.data
    await loadItems()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail?.message || '创建失败')
  } finally { periodLoading.value = false }
}

async function loadPeriod() {
  if (!periodId.value) return
  itemLoading.value = true
  try {
    const resp = await getPeriod(Number(periodId.value))
    period.value = resp.data.data
    await loadItems()
  } catch (e: any) {
    ElMessage.error('加载对账周期失败')
  } finally { itemLoading.value = false }
}

async function loadItems() {
  if (!period.value) return
  try {
    const resp = await getItems(period.value.id)
    items.value = resp.data.data
  } catch { /* ignore */ }
}

async function handleDispute(item: any) {
  if (!disputeReason.value) return
  try {
    await disputeItem(item.id, { dispute_reason: disputeReason.value })
    ElMessage.success('已申辩')
    disputeReason.value = ''
    await loadItems()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail?.message || '申辩失败')
  }
}

async function submitAdjustment() {
  try {
    const resp = await createAdjustment(adjForm.value)
    ElMessage.success(`调整单创建成功 ${resp.data.data.adj_no}`)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail?.message || '创建调整单失败')
  }
}
</script>

<template>
  <div class="page">
    <h3>对账管理</h3>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="对账周期" name="period">
        <el-form inline>
          <el-form-item label="期间 (YYYY-MM)"><el-input v-model="periodForm.period" placeholder="2026-11" style="width:140px" /></el-form-item>
          <el-form-item label="IDH"><el-input v-model="periodForm.idh_id" style="width:120px" /></el-form-item>
          <el-form-item><el-button type="primary" :loading="periodLoading" @click="submitPeriod">创建周期</el-button></el-form-item>
        </el-form>
        <el-divider />
        <el-form inline>
          <el-form-item label="查询周期ID"><el-input v-model="periodId" placeholder="输入ID" style="width:120px" /></el-form-item>
          <el-form-item><el-button :loading="itemLoading" @click="loadPeriod">查询</el-button></el-form-item>
        </el-form>

        <template v-if="period">
          <el-descriptions :column="4" border style="margin: 16px 0">
            <el-descriptions-item label="期间">{{ period.period }}</el-descriptions-item>
            <el-descriptions-item label="IDH">{{ period.idh_id }}</el-descriptions-item>
            <el-descriptions-item label="状态">{{ period.status }}</el-descriptions-item>
            <el-descriptions-item label="匹配率">{{ period.matched }}/{{ period.total_items }}</el-descriptions-item>
          </el-descriptions>

          <h4>差异明细</h4>
          <el-table :data="items" stripe border>
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="material_id" label="物料" width="250" />
            <el-table-column prop="lot_id" label="批次" width="250" />
            <el-table-column prop="diff_code" label="差异类型" width="100" />
            <el-table-column prop="qty_a" label="原厂数" width="80" />
            <el-table-column prop="qty_b" label="IDH数" width="80" />
            <el-table-column prop="qty_diff" label="差异" width="80" />
            <el-table-column prop="status" label="状态" width="100" />
            <el-table-column label="操作" width="160">
              <template #default="{ row }">
                <template v-if="row.status === 'pending'">
                  <el-popover placement="top" :width="300" trigger="click">
                    <template #reference>
                      <el-button size="small" type="warning">申辩</el-button>
                    </template>
                    <el-input v-model="disputeReason" placeholder="申辩理由" />
                    <el-button size="small" type="primary" style="margin-top:8px" @click="handleDispute(row)">提交</el-button>
                  </el-popover>
                </template>
              </template>
            </el-table-column>
          </el-table>

          <h4 style="margin-top: 20px">创建调整单</h4>
          <el-form inline>
            <el-form-item label="差异项ID"><el-input-number v-model="adjForm.recon_item_id" style="width:120px" /></el-form-item>
            <el-form-item label="批次"><el-input v-model="adjForm.lot_id" style="width:200px" /></el-form-item>
            <el-form-item label="调整前"><el-input-number v-model="adjForm.qty_before" style="width:100px" /></el-form-item>
            <el-form-item label="调整后"><el-input-number v-model="adjForm.qty_after" style="width:100px" /></el-form-item>
            <el-form-item label="差异码"><el-input v-model="adjForm.diff_code" style="width:100px" /></el-form-item>
            <el-form-item label="原因"><el-input v-model="adjForm.reason" style="width:150px" /></el-form-item>
            <el-form-item><el-button type="primary" @click="submitAdjustment">创建</el-button></el-form-item>
          </el-form>
        </template>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>