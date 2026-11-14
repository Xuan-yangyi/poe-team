<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listConversations, getMessages, postMessage } from '@/api/conversation'
import { ElMessage } from 'element-plus'

const convs = ref<any[]>([])
const convLoading = ref(false)

const selectedConv = ref<any>(null)
const messages = ref<any[]>([])
const msgLoading = ref(false)

const newMsg = ref('')
const sending = ref(false)

async function loadConvs() {
  convLoading.value = true
  try {
    const resp = await listConversations()
    convs.value = resp.data.data
  } catch {
    ElMessage.error('加载会话失败')
  } finally { convLoading.value = false }
}

async function selectConv(conv: any) {
  selectedConv.value = conv
  msgLoading.value = true
  try {
    const resp = await getMessages(conv.id)
    messages.value = resp.data.data.reverse()
  } catch {
    ElMessage.error('加载消息失败')
  } finally { msgLoading.value = false }
}

async function sendMsg() {
  if (!newMsg.value.trim() || !selectedConv.value) return
  sending.value = true
  try {
    await postMessage(selectedConv.value.id, { content: newMsg.value })
    newMsg.value = ''
    await selectConv(selectedConv.value)
  } catch {
    ElMessage.error('发送失败')
  } finally { sending.value = false }
}

onMounted(loadConvs)
</script>

<template>
  <div class="page">
    <h3>协同会话</h3>
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card>
          <template #header>会话列表</template>
          <div v-loading="convLoading" style="min-height:200px">
            <div
              v-for="conv in convs"
              :key="conv.id"
              @click="selectConv(conv)"
              :class="{ 'conv-item': true, active: selectedConv?.id === conv.id }"
            >
              <strong>{{ conv.title || `${conv.conv_type} - ${conv.ref_id}` }}</strong>
              <div style="font-size:12px;color:#909399">{{ conv.conv_type }} · {{ conv.is_active ? '进行中' : '已关闭' }}</div>
            </div>
            <el-empty v-if="!convLoading && convs.length === 0" description="暂无会话" />
          </div>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card>
          <template #header>
            {{ selectedConv ? (selectedConv.title || selectedConv.ref_id) : '选择会话' }}
          </template>
          <div v-loading="msgLoading" style="height:400px;overflow-y:auto;margin-bottom:12px">
            <div v-for="msg in messages" :key="msg.id" class="msg-bubble">
              <div style="font-size:12px;color:#909399">{{ msg.sender_id }} · {{ msg.created_at }}</div>
              <div style="margin-top:4px">{{ msg.content }}</div>
            </div>
            <el-empty v-if="!msgLoading && selectedConv && messages.length === 0" description="暂无消息" />
            <el-empty v-if="!selectedConv" description="请选择一个会话" />
          </div>
          <div v-if="selectedConv" style="display:flex;gap:8px">
            <el-input
              v-model="newMsg"
              placeholder="输入消息..."
              @keyup.enter="sendMsg"
            />
            <el-button type="primary" :loading="sending" @click="sendMsg">发送</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.conv-item {
  padding: 12px;
  border-bottom: 1px solid #ebeef5;
  cursor: pointer;
}
.conv-item:hover { background: #f5f7fa; }
.conv-item.active { background: #ecf5ff; }
.msg-bubble {
  padding: 8px 12px;
  margin-bottom: 8px;
  background: #f5f7fa;
  border-radius: 8px;
}
</style>