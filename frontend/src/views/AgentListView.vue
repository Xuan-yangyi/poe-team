<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listAgents, createAgent, updateAgent, deleteAgent, addAgentToGroup } from '@/api/agent'
import { listConversations } from '@/api/conversation'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const agents = ref<any[]>([])
const groups = ref<any[]>([])

// ── Create / Edit modal ──
const showDialog = ref(false)
const editing = ref<any>(null)
const saving = ref(false)
const form = ref({
  name: '', display_name: '', avatar_emoji: '🤖', role_description: '',
  system_prompt: '',
  provider: 'anthropic', api_base: 'https://www.sophnet.com/api/open-apis/anthropic',
  api_key: '', agent_model: 'DeepSeek-V4.1-Flash-1017',
  skills: [] as { name: string; description: string; trigger_keywords: string; action_type: string; skill_prompt: string; data_config?: any }[],
})
const newSkill = ref({ name: '', description: '', trigger_keywords: '', action_type: 'custom', skill_prompt: '' })

// ── Add to group modal ──
const showAddGroup = ref(false)
const addGroupAgent = ref<any>(null)
const selectedGroupId = ref('')

const ACTION_OPTIONS: { label: string; value: string }[] = [
  { label: '风险分析', value: 'analyze_risk' },
  { label: '进度检查', value: 'check_progress' },
  { label: '库存查询', value: 'query_inventory' },
  { label: '摘要生成', value: 'summarize' },
  { label: '自定义', value: 'custom' },
]

const PROVIDER_OPTIONS = [
  { label: 'Anthropic (Claude / DeepSeek via Anthropic协议)', value: 'anthropic' },
  { label: 'OpenAI (GPT)', value: 'openai' },
  { label: 'OpenAI 兼容 (DeepSeek/通义千问/Ollama)', value: 'openai_compatible' },
]

async function fetch() {
  loading.value = true
  try {
    const [aResp, gResp] = await Promise.all([
      listAgents(),
      listConversations({ conv_type: 'group' }),
    ])
    agents.value = aResp.data.data || []
    groups.value = (gResp.data.data || []).filter((g: any) => g.conv_type === 'group')
  } catch { /* silent */ }
  finally { loading.value = false }
}

function addSkill() {
  if (!newSkill.value.name.trim()) return
  form.value.skills.push({ ...newSkill.value })
  newSkill.value = { name: '', description: '', trigger_keywords: '', action_type: 'custom', skill_prompt: '' }
}

function removeSkill(idx: number) {
  form.value.skills.splice(idx, 1)
}

function openCreate() {
  editing.value = null
  form.value = {
    name: '', display_name: '', avatar_emoji: '🤖', role_description: '',
    system_prompt: '',
    provider: 'anthropic', api_base: 'https://www.sophnet.com/api/open-apis/anthropic',
    api_key: '', agent_model: 'DeepSeek-V4.1-Flash-1017',
    skills: [],
  }
  showDialog.value = true
}

function openEdit(agent: any) {
  editing.value = agent
  form.value = {
    name: agent.name,
    display_name: agent.display_name,
    avatar_emoji: agent.avatar_emoji,
    role_description: agent.role_description || '',
    system_prompt: agent.system_prompt || '',
    provider: agent.provider || 'anthropic',
    api_base: agent.api_base || '',
    api_key: '',  // masked — only set if user types new key
    agent_model: agent.agent_model || '',
    skills: (agent.skills || []).map((s: any) => ({ ...s })),
  }
  showDialog.value = true
}

async function doSave() {
  if (!form.value.name || !form.value.display_name || !form.value.system_prompt) {
    ElMessage.warning('请填写 Agent 名称、显示名和系统提示词')
    return
  }
  saving.value = true
  try {
    if (editing.value) {
      const payload: Record<string, any> = {
        display_name: form.value.display_name,
        avatar_emoji: form.value.avatar_emoji,
        role_description: form.value.role_description,
        system_prompt: form.value.system_prompt,
        provider: form.value.provider,
        api_base: form.value.api_base,
        agent_model: form.value.agent_model,
        skills: form.value.skills,
      }
      if (form.value.api_key) payload.api_key = form.value.api_key
      await updateAgent(editing.value.id, payload)
      ElMessage.success('Agent 已更新')
    } else {
      await createAgent({
        name: form.value.name,
        display_name: form.value.display_name,
        avatar_emoji: form.value.avatar_emoji,
        role_description: form.value.role_description,
        system_prompt: form.value.system_prompt,
        provider: form.value.provider,
        api_base: form.value.api_base,
        api_key: form.value.api_key,
        agent_model: form.value.agent_model,
        skills: form.value.skills,
      })
      ElMessage.success('Agent 创建成功')
    }
    showDialog.value = false
    await fetch()
  } catch (e: any) {
    console.error('Agent save error:', e)
    // Network error (no response)
    if (!e.response) {
      ElMessage.error('网络错误，请检查服务是否运行')
    } else {
      const status = e.response.status
      const detail = e.response.data?.detail
      const msg = detail?.message || (status === 422 ? '表单数据有误' : `请求失败 (${status})`)
      ElMessage.error(msg)
    }
  } finally { saving.value = false }
}

async function doDelete(agent: any) {
  try {
    await ElMessageBox.confirm(`确定删除 Agent「${agent.display_name}」吗？`, '确认删除', { type: 'warning' })
    await deleteAgent(agent.id)
    ElMessage.success('已删除')
    await fetch()
  } catch { /* cancelled */ }
}

function openAddGroup(agent: any) {
  addGroupAgent.value = agent
  selectedGroupId.value = ''
  showAddGroup.value = true
}

async function doAddToGroup() {
  if (!selectedGroupId.value || !addGroupAgent.value) return
  try {
    await addAgentToGroup(selectedGroupId.value, addGroupAgent.value.user_id)
    ElMessage.success(`已将 ${addGroupAgent.value.display_name} 加入群聊`)
    showAddGroup.value = false
  } catch { ElMessage.error('添加失败') }
}

const PROVIDER_LABEL: Record<string, string> = {
  anthropic: 'Anthropic 协议',
  openai: 'OpenAI',
  openai_compatible: 'OpenAI 兼容',
}

function actionLabel(actionType: string): string {
  return ACTION_OPTIONS.find(o => o.value === actionType)?.label || actionType
}

onMounted(fetch)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h3>🤖 Agent 管理</h3>
      <el-button type="primary" @click="openCreate">创建 Agent</el-button>
    </div>

    <p class="page-desc">
      每个 Agent 是独立的 AI 角色，可加入群聊。@提及或关键词触发后，使用其自身配置的 API 地址和 Key 调用大模型生成回复。
    </p>

    <!-- Agent list -->
    <el-row :gutter="16" v-loading="loading">
      <el-col v-for="agent in agents" :key="agent.id" :span="8" style="margin-bottom: 16px">
        <el-card shadow="hover" class="agent-card" :class="{ inactive: !agent.is_active }">
          <div class="card-top">
            <span class="agent-emoji">{{ agent.avatar_emoji }}</span>
            <div class="agent-info">
              <div class="agent-name">{{ agent.display_name }}</div>
              <div class="agent-tag">@{{ agent.name }}</div>
            </div>
            <el-switch v-model="agent.is_active" size="small" disabled />
          </div>

          <div class="agent-meta-row">
            <el-tag size="small" effect="plain" type="info">
              {{ PROVIDER_LABEL[agent.provider] || agent.provider }}
            </el-tag>
            <el-tag size="small" effect="plain">{{ agent.agent_model }}</el-tag>
            <span v-if="!agent.api_key" style="font-size:11px;color:#e6a23c">未配置 Key</span>
          </div>

          <div class="agent-desc">{{ agent.role_description || '暂无描述' }}</div>

          <div class="agent-skills" v-if="agent.skills?.length">
            <el-tag v-for="s in agent.skills" :key="s.name" size="small" style="margin-right:4px;margin-bottom:4px">
              {{ s.name }}
            </el-tag>
          </div>

          <div class="agent-actions">
            <el-button size="small" @click="openAddGroup(agent)">加入群聊</el-button>
            <el-button size="small" @click="openEdit(agent)">编辑</el-button>
            <el-button size="small" type="danger" plain @click="doDelete(agent)">删除</el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8" v-if="!loading && agents.length === 0" style="margin-bottom:16px">
        <el-empty description="暂无 Agent，点击右上角创建" :image-size="80" />
      </el-col>
    </el-row>

    <!-- ═══ Create / Edit Dialog ═══ -->
    <el-dialog v-model="showDialog" :title="editing ? '编辑 Agent' : '创建 Agent'" width="700px" :close-on-click-modal="false">
      <el-form label-position="top">
        <!-- ── Basic Info ── -->
        <el-row :gutter="12">
          <el-col :span="4">
            <el-form-item label="图标">
              <el-input v-model="form.avatar_emoji" maxlength="2" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Agent ID" required>
              <el-input v-model="form.name" placeholder="risk_watcher" :disabled="!!editing" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="显示名称" required>
              <el-input v-model="form.display_name" placeholder="风险巡检员" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="角色描述">
          <el-input v-model="form.role_description" placeholder="例如：监控工单延期风险并在群聊中预警" />
        </el-form-item>

        <el-form-item label="系统提示词" required>
          <el-input v-model="form.system_prompt" type="textarea" :rows="4"
            placeholder="定义 Agent 的行为和语气..." />
        </el-form-item>

        <!-- ── LLM 算力配置 ── -->
        <el-divider content-position="left">🔗 算力配置</el-divider>

        <el-form-item label="Provider 协议">
          <el-select v-model="form.provider" style="width:100%">
            <el-option v-for="o in PROVIDER_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>

        <el-row :gutter="12">
          <el-col :span="16">
            <el-form-item label="API 地址">
              <el-input v-model="form.api_base" placeholder="https://www.sophnet.com/api/open-apis/anthropic" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="模型名称">
              <el-input v-model="form.agent_model" placeholder="DeepSeek-V4.1-Flash-1017" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="API Key">
          <el-input v-model="form.api_key" type="password" show-password
            :placeholder="editing ? '留空不修改已保存的 Key' : '输入 API Key'" />
        </el-form-item>

        <!-- ── Skills ── -->
        <el-divider content-position="left">🧩 技能</el-divider>

        <div v-for="(skill, idx) in form.skills" :key="idx" class="skill-row">
          <div class="skill-row-header">
            <el-tag size="small" type="success">{{ skill.name }}</el-tag>
            <el-tag size="small">{{ actionLabel(skill.action_type) }}</el-tag>
            <span v-if="skill.trigger_keywords" style="font-size:11px;color:#909399">触发: {{ skill.trigger_keywords }}</span>
            <el-button size="small" type="danger" text @click="removeSkill(idx)">移除</el-button>
          </div>
        </div>

        <div class="add-skill-form">
          <el-row :gutter="8">
            <el-col :span="8">
              <el-input v-model="newSkill.name" placeholder="技能名称" size="small" />
            </el-col>
            <el-col :span="8">
              <el-input v-model="newSkill.trigger_keywords" placeholder="关键词 (逗号分隔)" size="small" />
            </el-col>
            <el-col :span="4">
              <el-select v-model="newSkill.action_type" size="small">
                <el-option v-for="o in ACTION_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
            </el-col>
            <el-col :span="4">
              <el-button size="small" @click="addSkill">+ 添加</el-button>
            </el-col>
          </el-row>
          <el-input v-model="newSkill.description" placeholder="技能描述" size="small" style="margin-top:6px" />
          <el-input v-model="newSkill.skill_prompt" placeholder="技能额外提示词" size="small" type="textarea" :rows="2" style="margin-top:6px" />
        </div>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doSave" native-type="button">
          {{ editing ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- ═══ Add to Group Dialog ═══ -->
    <el-dialog v-model="showAddGroup" title="添加 Agent 到群聊" width="420px">
      <p style="margin-bottom:12px;color:#666">
        将 <strong>{{ addGroupAgent?.display_name }}</strong> 加入群聊，通过 @提及或关键词触发自动回复。
      </p>
      <el-select v-model="selectedGroupId" placeholder="选择群聊" style="width:100%">
        <el-option v-for="g in groups" :key="g.id" :label="g.title || '群聊'" :value="g.id" />
      </el-select>
      <template #footer>
        <el-button @click="showAddGroup = false">取消</el-button>
        <el-button type="primary" :disabled="!selectedGroupId" @click="doAddToGroup">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page { padding: 24px 32px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.page-header h3 { margin: 0; }
.page-desc { color: #909399; font-size: 14px; margin-bottom: 20px; line-height: 1.6; }

.agent-card { border-radius: 8px; }
.agent-card.inactive { opacity: 0.5; }
.card-top { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.agent-emoji { font-size: 32px; }
.agent-info { flex: 1; min-width: 0; }
.agent-name { font-size: 15px; font-weight: 600; }
.agent-tag { font-size: 12px; color: #409eff; }
.agent-meta-row { display: flex; gap: 6px; align-items: center; margin-bottom: 8px; }
.agent-desc { font-size: 13px; color: #666; margin-bottom: 10px; line-height: 1.5; }
.agent-skills { margin-bottom: 10px; }
.agent-actions { display: flex; gap: 8px; }

.skill-row { background: #f5f7fa; padding: 8px 12px; border-radius: 6px; margin-bottom: 8px; }
.skill-row-header { display: flex; align-items: center; gap: 8px; }
.add-skill-form { background: #fafafa; padding: 12px; border-radius: 6px; border: 1px dashed #d9d9d9; }
</style>