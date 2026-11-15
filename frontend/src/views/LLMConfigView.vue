<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { getPresets, listConfigs, createConfig, updateConfig, deleteConfig, testConfig } from '@/api/llm'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const configs = ref<any[]>([])
const presets = ref<any[]>([])

// ── Create / Edit modal ──
const showModal = ref(false)
const editing = ref<any>(null)
const saving = ref(false)
const form = ref({
  provider: 'anthropic',
  api_base: 'https://api.anthropic.com',
  api_key: '',
  model: 'claude-sonnet-4-20250514',
  extra_params: '',
  description: '',
})

// ── Test state ──
const testing = ref<string | null>(null)
const testResults = ref<Record<string, { ok: boolean; message: string; latency_ms: number }>>({})

const PROVIDER_LABELS: Record<string, string> = {
  anthropic: 'Anthropic',
  openai: 'OpenAI',
  openai_compatible: 'OpenAI 兼容',
  custom: '自定义',
}

async function fetch() {
  loading.value = true
  try {
    const [cResp, pResp] = await Promise.all([
      listConfigs(),
      getPresets(),
    ])
    configs.value = cResp.data.data || []
    presets.value = pResp.data.data || []
  } catch { /* silent */ }
  finally { loading.value = false }
}

function onProviderChange(key: string) {
  const preset = presets.value.find((p: any) => p.key === key)
  if (preset && preset.api_base) {
    form.value.api_base = preset.api_base
    form.value.model = preset.model
  } else {
    form.value.api_base = ''
    form.value.model = ''
  }
}

function openCreate() {
  editing.value = null
  form.value = {
    provider: 'anthropic',
    api_base: 'https://api.anthropic.com',
    api_key: '',
    model: 'claude-sonnet-4-20250514',
    extra_params: '',
    description: '',
  }
  showModal.value = true
}

function openEdit(cfg: any) {
  editing.value = cfg
  form.value = {
    provider: cfg.provider,
    api_base: cfg.api_base,
    api_key: '',  // Don't show masked key; user must re-enter to change
    model: cfg.model,
    extra_params: cfg.extra_params ? JSON.stringify(cfg.extra_params, null, 2) : '',
    description: cfg.description || '',
  }
  showModal.value = true
}

async function doSave() {
  if (!form.value.api_base || !form.value.model) {
    ElMessage.warning('请填写 API 地址和模型名称')
    return
  }
  saving.value = true
  try {
    const payload: Record<string, any> = {
      provider: form.value.provider,
      api_base: form.value.api_base,
      model: form.value.model,
      description: form.value.description,
    }
    if (form.value.api_key) {
      payload.api_key = form.value.api_key
    }
    if (form.value.extra_params.trim()) {
      try {
        payload.extra_params = JSON.parse(form.value.extra_params)
      } catch {
        ElMessage.warning('额外参数不是有效的 JSON')
        saving.value = false
        return
      }
    }

    if (editing.value) {
      await updateConfig(editing.value.id, payload)
      ElMessage.success('配置已更新')
    } else {
      await createConfig(payload)
      ElMessage.success('配置已创建')
    }
    showModal.value = false
    await fetch()
  } catch { ElMessage.error('保存失败') }
  finally { saving.value = false }
}

async function doDelete(cfg: any) {
  try {
    await ElMessageBox.confirm(`确定删除此配置吗？`, '确认删除', { type: 'warning' })
    await deleteConfig(cfg.id)
    ElMessage.success('已删除')
    await fetch()
  } catch { /* cancelled */ }
}

async function doTest(cfg: any) {
  testing.value = cfg.id
  try {
    const resp = await testConfig(cfg.id)
    testResults.value[cfg.id] = resp.data.data
    if (resp.data.data.ok) {
      ElMessage.success(`连接成功 (${resp.data.data.latency_ms}ms): ${resp.data.data.message}`)
    } else {
      ElMessage.error(`连接失败: ${resp.data.data.message}`)
    }
  } catch {
    ElMessage.error('测试请求失败')
  } finally { testing.value = null }
}

onMounted(fetch)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h3>⚙️ LLM 算力配置</h3>
      <el-button type="primary" @click="openCreate">添加配置</el-button>
    </div>

    <p class="page-desc">
      为当前租户配置大模型接入方式。Agent 将使用激活的配置来生成群聊回复。
      支持 Anthropic Claude、OpenAI GPT 系列，以及兼容 OpenAI 接口的第三方服务（如 DeepSeek、通义千问、本地模型）。
    </p>

    <!-- Config cards -->
    <el-row :gutter="16" v-loading="loading">
      <el-col v-for="cfg in configs" :key="cfg.id" :span="8" style="margin-bottom: 16px">
        <el-card shadow="hover" class="config-card" :class="{ inactive: !cfg.is_active }">
          <div class="cfg-header">
            <el-tag :type="cfg.provider === 'anthropic' ? '' : cfg.provider === 'openai' ? 'success' : 'info'" size="small">
              {{ PROVIDER_LABELS[cfg.provider] || cfg.provider }}
            </el-tag>
            <el-tag v-if="cfg.is_active" type="success" size="small" effect="dark">激活</el-tag>
            <el-tag v-else type="info" size="small">停用</el-tag>
          </div>

          <div class="cfg-model">{{ cfg.model }}</div>
          <div class="cfg-url">{{ cfg.api_base }}</div>
          <div class="cfg-key">
            <span v-if="cfg.api_key">{{ cfg.api_key }}</span>
            <span v-else style="color:#e6a23c">未设置 Key</span>
          </div>
          <div v-if="cfg.description" class="cfg-desc">{{ cfg.description }}</div>

          <!-- Test result -->
          <template v-if="testResults[cfg.id]">
            <div class="cfg-test-result" :class="{ ok: testResults[cfg.id]!.ok, fail: !testResults[cfg.id]!.ok }">
              <span v-if="testResults[cfg.id]!.ok">✓ {{ testResults[cfg.id]!.message }} ({{ testResults[cfg.id]!.latency_ms }}ms)</span>
              <span v-else>✗ {{ testResults[cfg.id]!.message }}</span>
            </div>
          </template>

          <div class="cfg-actions">
            <el-button size="small" :loading="testing === cfg.id" @click="doTest(cfg)">
              {{ testing === cfg.id ? '测试中...' : '测试连接' }}
            </el-button>
            <el-button size="small" @click="openEdit(cfg)">编辑</el-button>
            <el-button size="small" type="danger" plain @click="doDelete(cfg)">删除</el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8" v-if="!loading && configs.length === 0" style="margin-bottom:16px">
        <el-empty description="暂无 LLM 配置，点击右上角添加" :image-size="80" />
      </el-col>
    </el-row>

    <!-- ═══ Config Modal ═══ -->
    <el-dialog v-model="showModal" :title="editing ? '编辑 LLM 配置' : '添加 LLM 配置'" width="560px" :close-on-click-modal="false">
      <el-form label-position="top">
        <el-form-item label="Provider">
          <el-select v-model="form.provider" style="width:100%" @change="onProviderChange">
            <el-option
              v-for="p in presets"
              :key="p.key"
              :label="p.label"
              :value="p.key"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="API 地址" required>
          <el-input v-model="form.api_base" placeholder="https://api.anthropic.com" />
        </el-form-item>

        <el-form-item label="API Key">
          <el-input v-model="form.api_key" type="password" show-password
            :placeholder="editing ? '留空则不修改已有 Key' : '输入 API Key'"
          />
        </el-form-item>

        <el-form-item label="模型名称" required>
          <el-input v-model="form.model" placeholder="claude-sonnet-4-20250514" />
        </el-form-item>

        <el-form-item label="额外参数 (JSON)">
          <el-input v-model="form.extra_params" type="textarea" :rows="3"
            placeholder='{"temperature": 0.7, "max_tokens": 1024}'
          />
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="form.description" placeholder="此配置的用途说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showModal = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doSave">
          {{ editing ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page { padding: 24px 32px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.page-header h3 { margin: 0; }
.page-desc { color: #909399; font-size: 14px; margin-bottom: 20px; line-height: 1.6; }

.config-card { border-radius: 8px; }
.config-card.inactive { opacity: 0.55; }
.cfg-header { display: flex; gap: 8px; margin-bottom: 12px; }
.cfg-model { font-size: 16px; font-weight: 600; color: #303133; margin-bottom: 4px; }
.cfg-url { font-size: 12px; color: #909399; margin-bottom: 4px; word-break: break-all; }
.cfg-key { font-size: 12px; color: #67c23a; font-family: monospace; margin-bottom: 4px; }
.cfg-desc { font-size: 12px; color: #909399; margin-bottom: 8px; }
.cfg-test-result { font-size: 12px; padding: 6px 10px; border-radius: 4px; margin-bottom: 10px; }
.cfg-test-result.ok { background: #f0f9eb; color: #67c23a; }
.cfg-test-result.fail { background: #fef0f0; color: #f56c6c; }
.cfg-actions { display: flex; gap: 8px; }
</style>