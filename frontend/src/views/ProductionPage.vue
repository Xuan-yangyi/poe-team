<script setup lang="ts">
import { ref } from 'vue'
import { createIssue, createWipReport, createFgReceipt } from '@/api/production'
import { ElMessage } from 'element-plus'

const activeTab = ref('issue')

const issueForm = ref({ wo_id: '', lot_id: '', material_id: '', qty: 100, operator: '', scan_method: 'h5' })
const wipForm = ref({ wo_id: '', process_code: '', process_seq: 1, qty_in: 0, qty_out: 0, qty_scrap: 0, scrap_reason: '', reported_by: '' })
const fgForm = ref({ wo_id: '', sn: '', qty: 1, lot_id: '', received_by: '' })

const issueLoading = ref(false)
const wipLoading = ref(false)
const fgLoading = ref(false)

async function submitIssue() {
  if (!issueForm.value.wo_id || !issueForm.value.lot_id || !issueForm.value.material_id) {
    ElMessage.warning('请填写完整信息')
    return
  }
  issueLoading.value = true
  try {
    const resp = await createIssue(issueForm.value)
    ElMessage.success(`发料成功 qty=${resp.data.data.qty}`)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail?.message || '发料失败')
  } finally { issueLoading.value = false }
}

async function submitWip() {
  wipLoading.value = true
  try {
    const resp = await createWipReport(wipForm.value)
    ElMessage.success(`WIP汇报成功 process=${resp.data.data.process_code}`)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail?.message || 'WIP汇报失败')
  } finally { wipLoading.value = false }
}

async function submitFg() {
  if (!fgForm.value.sn || !fgForm.value.lot_id) {
    ElMessage.warning('请填写SN和批次')
    return
  }
  fgLoading.value = true
  try {
    const resp = await createFgReceipt(fgForm.value)
    ElMessage.success(`成品入库成功 SN=${resp.data.data.sn}`)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail?.message || '入库失败')
  } finally { fgLoading.value = false }
}
</script>

<template>
  <div class="page">
    <h3>生产执行</h3>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="物料发料" name="issue">
        <el-form label-width="100px" style="max-width: 500px">
          <el-form-item label="工单ID"><el-input v-model="issueForm.wo_id" /></el-form-item>
          <el-form-item label="批次ID"><el-input v-model="issueForm.lot_id" /></el-form-item>
          <el-form-item label="物料ID"><el-input v-model="issueForm.material_id" /></el-form-item>
          <el-form-item label="数量"><el-input-number v-model="issueForm.qty" :min="1" /></el-form-item>
          <el-form-item label="操作员"><el-input v-model="issueForm.operator" placeholder="扫描枪/工号" /></el-form-item>
          <el-form-item label="扫描方式">
            <el-radio-group v-model="issueForm.scan_method">
              <el-radio value="h5">H5</el-radio>
              <el-radio value="pda">PDA</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item><el-button type="primary" :loading="issueLoading" @click="submitIssue">确认发料</el-button></el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="WIP工序汇报" name="wip">
        <el-form label-width="100px" style="max-width: 500px">
          <el-form-item label="工单ID"><el-input v-model="wipForm.wo_id" /></el-form-item>
          <el-form-item label="工序代码"><el-input v-model="wipForm.process_code" /></el-form-item>
          <el-form-item label="工序序号"><el-input-number v-model="wipForm.process_seq" :min="1" /></el-form-item>
          <el-form-item label="投入数"><el-input-number v-model="wipForm.qty_in" :min="0" /></el-form-item>
          <el-form-item label="产出数"><el-input-number v-model="wipForm.qty_out" :min="0" /></el-form-item>
          <el-form-item label="报废数"><el-input-number v-model="wipForm.qty_scrap" :min="0" /></el-form-item>
          <el-form-item label="报废原因"><el-input v-model="wipForm.scrap_reason" /></el-form-item>
          <el-form-item label="汇报人"><el-input v-model="wipForm.reported_by" /></el-form-item>
          <el-form-item><el-button type="primary" :loading="wipLoading" @click="submitWip">提交汇报</el-button></el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="成品入库" name="fg">
        <el-form label-width="100px" style="max-width: 500px">
          <el-form-item label="工单ID"><el-input v-model="fgForm.wo_id" /></el-form-item>
          <el-form-item label="SN"><el-input v-model="fgForm.sn" /></el-form-item>
          <el-form-item label="数量"><el-input-number v-model="fgForm.qty" :min="1" /></el-form-item>
          <el-form-item label="批次ID"><el-input v-model="fgForm.lot_id" /></el-form-item>
          <el-form-item label="接收人"><el-input v-model="fgForm.received_by" /></el-form-item>
          <el-form-item><el-button type="primary" :loading="fgLoading" @click="submitFg">确认入库</el-button></el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>