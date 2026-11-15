<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { listConversations, getMessages, postMessage, createGroup, listUsers, getConversationMembers } from '@/api/conversation'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import EmojiPicker from '@/components/EmojiPicker.vue'
import { uploadFile } from '@/api/user'
import WorkbenchPanel from '@/views/WorkbenchPanel.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const isHome = computed(() => route.path === '/' || route.path === '')

// ── Name/avatar resolution ──
const userNameMap = computed(() => {
  const map: Record<string, string> = {}
  for (const m of mentionMembers.value) {
    map[m.user_id] = m.display_name || m.user_id?.slice(0, 8)
  }
  return map
})
const userEmojiMap = computed(() => {
  const map: Record<string, string> = {}
  for (const m of mentionMembers.value) {
    const name = m.display_name || m.user_id || '?'
    map[m.user_id] = name[0]
  }
  return map
})

// Deterministic pastel avatar color from sender_id
const AVATAR_COLORS = ['#5470c6','#91cc75','#fac858','#ee6666','#73c0de','#3ba272','#fc8452','#9a60b4','#ea7ccc','#48b8d0']
function avatarColor(senderId: string): string {
  if (!senderId) return AVATAR_COLORS[0]
  let hash = 0
  for (let i = 0; i < senderId.length; i++) hash = ((hash << 5) - hash + senderId.charCodeAt(i)) | 0
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length]
}

function formatTime(ts: string | null | undefined): string {
  if (!ts) return ''
  const d = new Date(ts)
  const now = new Date()
  const pad = (n: number) => n.toString().padStart(2, '0')
  const time = `${pad(d.getHours())}:${pad(d.getMinutes())}`
  if (d.toDateString() === now.toDateString()) return time
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  if (d.toDateString() === yesterday.toDateString()) return `昨天 ${time}`
  return `${d.getMonth() + 1}/${d.getDate()} ${time}`
}

// ── Auto-scroll ──
const chatMessagesRef = ref<HTMLElement | null>(null)

function scrollToBottom() {
  nextTick(() => {
    // Double rAF ensures the browser has painted the new messages before we scroll
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        const el = chatMessagesRef.value
        if (el) el.scrollTop = el.scrollHeight
      })
    })
  })
}

// ── Panels ──
const showWorkbench = ref(false)

// ── Conversations ──
const convs = ref<any[]>([])
const convLoading = ref(false)
const selectedConv = ref<any>(null)
const messages = ref<any[]>([])
const msgLoading = ref(false)
const newMsg = ref('')
const searchQuery = ref('')
const sending = ref(false)
const showMembers = ref(false)
const emojiRef = ref<InstanceType<typeof EmojiPicker> | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const uploading = ref(false)

function insertEmoji(emoji: string) {
  newMsg.value += emoji
  emojiRef.value?.close()
}

function triggerFileUpload() {
  fileInputRef.value?.click()
}

async function onFileSelected(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  uploading.value = true
  try {
    const resp = await uploadFile(file)
    const data = resp.data.data
    const isImage = file.type.startsWith('image/')
    const insert = isImage
      ? `![${file.name}](${data.url})`
      : `[file:${file.name}](${data.url})`
    newMsg.value = newMsg.value ? newMsg.value + '\n' + insert : insert
    ElMessage.success(`${file.name} 上传成功`)
  } catch {
    ElMessage.error('文件上传失败')
  } finally {
    uploading.value = false
    input.value = ''
  }
}

// ── @Mention ──
const mentionMembers = ref<any[]>([])
const showMention = ref(false)
const mentionIndex = ref(0)
const mentionStartPos = ref(-1)
const mentionQuery = ref('')
const mentionFiltered = computed(() => {
  if (!mentionQuery.value) return mentionMembers.value.slice(0, 8)
  const q = mentionQuery.value.toLowerCase()
  return mentionMembers.value
    .filter((m: any) =>
      m.display_name?.toLowerCase().includes(q) ||
      m.agent_name?.toLowerCase().includes(q) ||
      m.mention_handle?.toLowerCase().includes(q)
    )
    .slice(0, 8)
})

// Filter conversation list by search
const filteredConvs = computed(() => {
  if (!searchQuery.value.trim()) return convs.value
  const q = searchQuery.value.toLowerCase()
  return convs.value.filter((c: any) =>
    convTitle(c).toLowerCase().includes(q) ||
    (c.conv_type === 'group' && '群聊'.includes(q))
  )
})

// Markdown rendering with inline images and file download cards
function renderMarkdown(raw: string): string {
  // Pre-process: [file:NAME](URL) → download card HTML
  let preprocessed = raw.replace(
    /\[file:([^\]]+)\]\((\/uploads\/[^)]+)\)/g,
    (_m, name, url) => `<div class="file-card">
      <div class="file-card-icon">
        <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="#666" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
      </div>
      <div class="file-card-body">
        <a href="${url}" download class="file-card-name">${name}</a>
        <span class="file-card-hint">点击下载</span>
      </div>
    </div>`
  )

  try {
    let html = marked.parse(preprocessed, { async: false }) as string

    // Post-process: wrap <img> tags in responsive container with lightbox
    html = html.replace(
      /<img\s+src="(\/uploads\/[^"]+)"\s+alt="([^"]*)"[^>]*>/g,
      (_m: string, src: string, alt: string) =>
        `<div class="msg-image-wrapper">
          <img src="${src}" alt="${alt}" loading="lazy" onclick="this.closest('.msg-image-wrapper').classList.toggle('expanded')" />
          <span class="msg-image-caption">${alt || ''}</span>
        </div>`
    )

    return html
  } catch {
    const escaped = preprocessed.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    return escaped.replace(/\n/g, '<br>')
  }
}

async function loadConvs() {
  convLoading.value = true
  try {
    const resp = await listConversations()
    convs.value = resp.data.data
  } catch {
    // silent fail
  } finally { convLoading.value = false }
}

async function selectConv(conv: any) {
  selectedConv.value = conv
  showWorkbench.value = false
  // Navigate to home so chat window can render
  if (route.path !== '/') router.push('/')
  msgLoading.value = true
  try {
    const [msgResp, memberResp] = await Promise.all([
      getMessages(conv.id),
      getConversationMembers(conv.id).catch(() => ({ data: { data: [] } })),
    ])
    messages.value = msgResp.data.data.reverse()
    mentionMembers.value = memberResp.data.data || []
    scrollToBottom()
  } catch {
    ElMessage.error('加载消息失败')
  } finally { msgLoading.value = false }
}

function onMsgInput(e: any) {
  // Detect @mention trigger
  const val = e?.target?.value ?? newMsg.value
  const cursorPos = e?.target?.selectionStart ?? val.length

  // Find the @ position before cursor
  let atPos = -1
  for (let i = cursorPos - 1; i >= 0; i--) {
    if (val[i] === '@') {
      // Check that @ is at start or preceded by space/newline
      if (i === 0 || val[i - 1] === ' ' || val[i - 1] === '\n') { atPos = i; break }
    }
    if (val[i] === ' ' || val[i] === '\n') break
  }

  if (atPos >= 0) {
    mentionStartPos.value = atPos
    mentionQuery.value = val.slice(atPos + 1, cursorPos)
    mentionIndex.value = 0
    showMention.value = true
  } else {
    showMention.value = false
    mentionStartPos.value = -1
    mentionQuery.value = ''
  }
}

function insertMention(member: any) {
  const val = newMsg.value
  const handle = member.mention_handle || `@${member.display_name}`
  const before = val.slice(0, mentionStartPos.value)
  const after = val.slice(mentionStartPos.value + 1 + mentionQuery.value.length)
  newMsg.value = before + handle + ' ' + after
  showMention.value = false
  mentionStartPos.value = -1
  mentionQuery.value = ''
  nextTick(() => {
    const input = document.querySelector('.chat-input input, .chat-input textarea') as HTMLInputElement
    input?.focus()
  })
}

function onMentionKeydown(e: KeyboardEvent) {
  if (!showMention.value) return
  const items = mentionFiltered.value
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    mentionIndex.value = (mentionIndex.value + 1) % items.length
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    mentionIndex.value = (mentionIndex.value - 1 + items.length) % items.length
  } else if (e.key === 'Enter' || e.key === 'Tab') {
    e.preventDefault()
    if (items.length > 0) insertMention(items[mentionIndex.value])
  } else if (e.key === 'Escape') {
    showMention.value = false
  }
}

async function sendMsg() {
  if (!newMsg.value.trim() || !selectedConv.value) return
  sending.value = true
  const convId = selectedConv.value.id
  try {
    await postMessage(convId, { content: newMsg.value.trim() })
    newMsg.value = ''
    sending.value = false

    // Refresh messages directly (not via selectConv — avoids loading spinner & scroll reset)
    try {
      const msgResp = await getMessages(convId)
      messages.value = msgResp.data.data.reverse()
      scrollToBottom()
    } catch { /* keep existing messages if refresh fails */ }

    // Background poll for agent response (arrives async within seconds)
    const hasAgents = mentionMembers.value.some((m: any) => m.role === 'agent')
    if (hasAgents) {
      const existingIds = new Set(messages.value.map((m: any) => m.id))
      for (let i = 0; i < 15; i++) {
        await new Promise(r => setTimeout(r, 1200))
        if (selectedConv.value?.id !== convId) break  // user switched conv
        try {
          const msgResp = await getMessages(convId)
          const msgs = (msgResp.data.data || []).reverse()
          const hasNew = msgs.some((m: any) => !existingIds.has(m.id))
          if (hasNew) {
            messages.value = msgs
            scrollToBottom()
            break
          }
        } catch { break }
      }
    }
  } catch {
    sending.value = false
    ElMessage.error('发送失败')
  }
}

// Compute display title: for direct chats, show the other user's name
function convTitle(conv: any): string {
  if (conv.conv_type === 'group') return conv.title || '群聊'
  if (conv.conv_type === 'direct' && conv.member_names?.length) {
    const myName = auth.userInfo?.username
    const other = conv.member_names.find((n: string) => n !== myName)
    return other || conv.member_names[0]
  }
  return conv.title || conv.conv_type
}

function convSubtitle(conv: any): string {
  if (conv.conv_type === 'group') return `${conv.member_names?.length || 0} 位成员`
  if (conv.conv_type === 'direct') return '私聊'
  return conv.conv_type
}

function openWorkbench() {
  router.push('/')
  showWorkbench.value = true
  selectedConv.value = null
}

const showUserMenu = ref(false)

function openSettings(section?: string) {
  router.push('/settings' + (section ? `?tab=${section}` : ''))
  selectedConv.value = null
  showWorkbench.value = false
  showUserMenu.value = false
}

function handleLogout() {
  showUserMenu.value = false
  auth.logout()
  router.push('/login')
}

// ── Group creation ──
const showGroupModal = ref(false)
const groupName = ref('')
const allUsers = ref<any[]>([])
const selectedUserIds = ref<string[]>([])
const groupCreating = ref(false)

async function openGroupModal() {
  groupName.value = ''
  selectedUserIds.value = []
  try {
    const resp = await listUsers()
    allUsers.value = resp.data.data || []
  } catch {
    ElMessage.error('加载用户列表失败')
  }
  showGroupModal.value = true
}

async function doCreateGroup() {
  if (!groupName.value.trim()) {
    ElMessage.warning('请输入群聊名称')
    return
  }
  if (selectedUserIds.value.length === 0) {
    ElMessage.warning('请至少选择一位成员')
    return
  }
  groupCreating.value = true
  try {
    await createGroup({ title: groupName.value.trim(), member_ids: selectedUserIds.value })
    ElMessage.success('群聊创建成功')
    showGroupModal.value = false
    await loadConvs()
  } catch {
    ElMessage.error('创建群聊失败')
  } finally { groupCreating.value = false }
}

onMounted(loadConvs)
</script>

<template>
  <div class="main-layout">
    <!-- ═══ Left sidebar ═══ -->
    <div class="sidebar">
      <!-- User info -->
      <div class="sidebar-header">
        <div class="user-avatar">
          <span>{{ (auth.userInfo?.display_name || auth.userInfo?.username || '?')[0] }}</span>
        </div>
        <div class="user-detail">
          <div class="user-name">{{ auth.userInfo?.display_name || auth.userInfo?.username }}</div>
          <div class="user-role">{{ auth.userInfo?.role === 'factory_admin' ? '工厂' : 'IDH' }}</div>
        </div>
        <div class="user-menu-wrapper">
          <div class="three-dots" @click.stop="showUserMenu = !showUserMenu" title="更多">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/></svg>
          </div>
          <div v-if="showUserMenu" class="user-dropdown" @click.stop style="font-size:10px;line-height:1.4">
            <div class="dropdown-item" @click="openSettings('profile')" style="font-size:10px">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              用户信息完善
            </div>
            <div class="dropdown-item" @click="openSettings('security')" style="font-size:10px">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
              用户安全
            </div>
            <div class="dropdown-divider"></div>
            <div class="dropdown-item danger" @click="handleLogout" style="font-size:10px">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
              退出登录
            </div>
          </div>
        </div>
        <!-- Close dropdown on outside click -->
        <div v-if="showUserMenu" class="dropdown-mask" @click="showUserMenu = false"></div>
      </div>

      <!-- Search -->
      <div class="search-box">
        <el-input v-model="searchQuery" placeholder="搜索会话..." size="small" clearable />
      </div>

      <!-- Conversation list -->
      <div class="conv-list" v-loading="convLoading">
        <div class="list-label">会话</div>
        <div
          v-for="conv in filteredConvs"
          :key="conv.id"
          class="conv-item"
          :class="{ active: selectedConv?.id === conv.id }"
          @click="selectConv(conv)"
        >
          <div class="conv-avatar" :class="{ group: conv.conv_type === 'group' }">
            {{ conv.conv_type === 'group' ? '#' : (convTitle(conv))[0] }}
          </div>
          <div class="conv-info">
            <div class="conv-title">{{ convTitle(conv) }}</div>
            <div class="conv-preview">{{ conv.last_msg_preview || convSubtitle(conv) }}</div>
          </div>
        </div>
        <el-empty
          v-if="!convLoading && convs.length === 0"
          description="暂无会话"
          :image-size="48"
        />
      </div>

      <!-- ═══ Sidebar footer ═══ -->
      <div class="sidebar-footer">
        <div class="sidebar-actions">
          <el-button text size="small" class="action-btn" @click="openGroupModal">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            创建群聊
          </el-button>
        </div>
        <div
          class="workbench-btn"
          :class="{ active: showWorkbench }"
          @click="openWorkbench"
        >
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7" rx="1"/>
            <rect x="14" y="3" width="7" height="7" rx="1"/>
            <rect x="3" y="14" width="7" height="7" rx="1"/>
            <rect x="14" y="14" width="7" height="7" rx="1"/>
          </svg>
          <span>工作台</span>
        </div>
      </div>
    </div>

    <!-- ═══ Right panel ═══ -->
    <div class="main-panel">
      <div v-if="!isHome" class="business-page">
        <router-view />
      </div>

      <WorkbenchPanel v-else-if="showWorkbench" />

      <!-- Chat window -->
      <div v-else-if="selectedConv" class="chat-window">
        <div class="chat-header">
          <div class="chat-header-title" @click="showMembers = !showMembers" style="cursor:pointer">
            {{ convTitle(selectedConv) }}
            <span class="chat-header-meta">{{ convSubtitle(selectedConv) }}</span>
            <svg class="member-arrow" :class="{ open: showMembers }" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
          </div>
          <!-- Group member panel -->
          <div v-if="showMembers && selectedConv?.conv_type === 'group'" class="member-panel">
            <div
              v-for="m in mentionMembers"
              :key="m.user_id"
              class="member-row"
            >
              <span class="member-avatar" :style="{ background: avatarColor(m.user_id), color: '#fff' }">{{ m.display_name?.[0] || '?' }}</span>
              <div class="member-info">
                <span class="member-name">{{ m.display_name }}</span>
                <span v-if="m.agent_name" class="member-badge">@{{ m.agent_name }}</span>
                <span v-if="m.role === 'agent'" class="member-role-tag">Agent</span>
              </div>
            </div>
          </div>
        </div>

        <div class="chat-messages" ref="chatMessagesRef">
          <div v-if="msgLoading" class="chat-loading">
            <span>加载中...</span>
          </div>
          <div v-else-if="messages.length === 0" class="chat-empty">
            <el-empty description="暂无消息，发送第一条消息吧" :image-size="80" />
          </div>
          <template v-else>
            <div
              v-for="msg in messages"
              :key="msg.id"
              class="msg-row"
              :class="{ mine: msg.sender_id === auth.userInfo?.user_id }"
            >
              <div
                class="msg-avatar"
                :style="{ background: avatarColor(msg.sender_id), color: '#fff' }"
              >{{ userEmojiMap[msg.sender_id] || (msg.sender_id?.[0] ?? '?') }}</div>
              <div class="msg-body">
                <div class="msg-sender">{{ userNameMap[msg.sender_id] || msg.sender_id?.slice(0, 8) || '未知' }}</div>
                <div class="msg-bubble" v-html="renderMarkdown(msg.content)"></div>
                <div class="msg-time">{{ formatTime(msg.created_at) }}</div>
              </div>
            </div>
          </template>
        </div>

        <div class="chat-input">
          <div class="input-wrapper">
            <el-input
              v-model="newMsg"
              placeholder="输入消息，@ 提及成员，回车发送"
              size="large"
              @input="onMsgInput"
              @keydown="onMentionKeydown"
              @keyup.enter.exact="sendMsg"
              :disabled="sending"
            >
              <template #append>
                <el-button type="primary" :loading="sending" @click="sendMsg">发送</el-button>
              </template>
            </el-input>
          </div>
          <div class="input-toolbar">
            <EmojiPicker ref="emojiRef" @select="insertEmoji" />
            <input
              ref="fileInputRef"
              type="file"
              accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.txt,.csv,.zip"
              style="display:none"
              @change="onFileSelected"
            />
            <div class="upload-trigger" :class="{ active: uploading }" @click="triggerFileUpload" title="上传文件/图片">
              <svg v-if="!uploading" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              <el-icon v-else class="is-loading"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg></el-icon>
            </div>
          </div>
            <!-- @Mention popup -->
            <div v-if="showMention && mentionFiltered.length > 0" class="mention-popup">
              <div
                v-for="(m, idx) in mentionFiltered"
                :key="m.user_id"
                class="mention-item"
                :class="{ active: idx === mentionIndex }"
                @click="insertMention(m)"
                @mouseenter="mentionIndex = idx"
              >
                <span class="mention-avatar">{{ m.display_name?.[0] || '?' }}</span>
                <div class="mention-info">
                  <span class="mention-name">{{ m.display_name }}</span>
                  <span v-if="m.agent_name" class="mention-handle">@{{ m.agent_name }}</span>
                </div>
                <span v-if="m.agent_name" class="mention-badge">Agent</span>
              </div>
            </div>
          </div>
        </div>

      <!-- Welcome state -->
      <div v-else class="welcome">
        <div class="welcome-icon">
          <svg viewBox="0 0 24 24" width="64" height="64" fill="none" stroke="#c0c4cc" stroke-width="1.5">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        </div>
        <h2>IDH 协同平台</h2>
        <p>选择左侧会话开始沟通，或点击<strong>工作台</strong>处理业务</p>
      </div>
    </div>
  </div>

    <!-- ═══ Group creation modal ═══ -->
    <el-dialog v-model="showGroupModal" title="创建群聊" width="460px" :close-on-click-modal="false">
      <el-form label-position="top">
        <el-form-item label="群聊名称" required>
          <el-input v-model="groupName" placeholder="输入群聊名称" maxlength="30" show-word-limit />
        </el-form-item>
        <el-form-item label="选择成员">
          <div class="member-checklist">
            <el-checkbox-group v-model="selectedUserIds">
              <div
                v-for="u in allUsers"
                :key="u.id"
                class="member-item"
              >
                <el-checkbox :value="u.id" :disabled="u.username === auth.userInfo?.username">
                  <span class="member-name">{{ u.display_name || u.username }}</span>
                  <span class="member-meta">{{ u.tenant_id }} · {{ u.role }}</span>
                </el-checkbox>
              </div>
            </el-checkbox-group>
            <el-empty
              v-if="allUsers.length === 0"
              description="暂无可用成员"
              :image-size="40"
            />
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showGroupModal = false">取消</el-button>
        <el-button type="primary" :loading="groupCreating" @click="doCreateGroup">
          创建
        </el-button>
      </template>
    </el-dialog>
</template>

<style scoped>
/* ═══ Layout ═══ */
.main-layout {
  display: flex;
  height: 100vh;
  background: #f5f5f5;
}

.business-page {
  flex: 1;
  overflow-y: auto;
  background: #fff;
}

.business-page :deep(.page) {
  padding: 24px 32px;
}

.business-page :deep(h3) {
  margin: 0 0 16px;
  font-size: 18px;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 12px;
}

/* ═══ Sidebar ═══ */
.sidebar {
  width: 280px;
  min-width: 280px;
  background: #2e2e2e;
  color: #ddd;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  display: flex;
  align-items: center;
  padding: 16px;
  gap: 12px;
  background: #252525;
  position: relative;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 4px;
  background: #409eff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  flex-shrink: 0;
}

.user-detail {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 14px;
  color: #eee;
}

/* ── Three-dot menu ── */
.user-menu-wrapper { position: relative; }

.three-dots {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 6px;
  cursor: pointer;
  color: #888;
  transition: all 0.15s;
}
.three-dots:hover { background: rgba(255,255,255,0.1); color: #fff; }

.user-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.18);
  min-width: 150px;
  padding: 4px;
  z-index: 100;
  font-size: 10px;
  line-height: 1.3;
}

.user-dropdown * {
  font-size: inherit !important;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  border-radius: 6px;
  color: #333;
  cursor: pointer;
  transition: background 0.12s;
  white-space: nowrap;
}
.dropdown-item:hover { background: #f5f7fa; }
.dropdown-item.danger { color: #e34d59; }
.dropdown-item.danger:hover { background: #fef0f0; }

.dropdown-divider {
  height: 1px;
  background: #eee;
  margin: 4px 8px;
}

.dropdown-mask {
  position: fixed;
  inset: 0;
  z-index: 50;
}

.user-role {
  font-size: 12px;
  color: #999;
}

.search-box {
  padding: 12px 16px;
}

.search-box :deep(.el-input__wrapper) {
  background: #3a3a3a;
  border: none;
  box-shadow: none;
}

.search-box :deep(.el-input__inner) {
  color: #ccc;
}

.conv-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px;
}

.list-label {
  font-size: 12px;
  color: #888;
  padding: 8px 8px 4px;
}

.conv-item {
  display: flex;
  align-items: center;
  padding: 10px 8px;
  border-radius: 6px;
  cursor: pointer;
  gap: 10px;
  margin-bottom: 2px;
}

.conv-item:hover {
  background: #3a3a3a;
}

.conv-item.active {
  background: #404040;
}

.conv-avatar {
  width: 36px;
  height: 36px;
  border-radius: 4px;
  background: #5b8c5a;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.conv-avatar.group {
  background: #e6a23c;
}

.conv-info {
  flex: 1;
  min-width: 0;
}

.conv-title {
  font-size: 14px;
  color: #ddd;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-preview {
  font-size: 12px;
  color: #888;
  margin-top: 2px;
}

/* Sidebar footer */
.sidebar-footer {
  background: #252525;
}

.sidebar-actions {
  padding: 6px 12px 0;
}

.action-btn {
  width: 100%;
  color: #aaa !important;
  justify-content: flex-start;
  gap: 8px;
  font-size: 13px;
}

.action-btn:hover {
  color: #fff !important;
  background: #3a3a3a;
}

.workbench-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  color: #aaa;
  font-size: 14px;
  transition: all 0.2s;
  margin: 4px 8px 8px;
}

.workbench-btn:hover {
  background: #3a5a8c;
  color: #fff;
}

.workbench-btn.active {
  background: #409eff;
  color: #fff;
}

/* ═══ Main panel ═══ */
.main-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat-window {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #fff;
}

.chat-header {
  display: flex;
  align-items: center;
  padding: 14px 20px;
  background: #fafafa;
  border-bottom: 1px solid #e8e8e8;
  min-height: 56px;
  position: relative;
}

.chat-header-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.chat-header-meta {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
  font-weight: normal;
}

.member-arrow {
  margin-left: 6px;
  transition: transform 0.2s;
  color: #909399;
}
.member-arrow.open { transform: rotate(180deg); }

.member-panel {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-top: none;
  border-radius: 0 0 8px 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  max-height: 240px;
  overflow-y: auto;
  z-index: 10;
}

.member-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  border-bottom: 1px solid #f0f0f0;
}
.member-row:last-child { border-bottom: none; }

.member-row .member-avatar {
  width: 28px;
  height: 28px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.member-row .member-info {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.member-row .member-name {
  font-size: 13px;
  color: #303133;
}

.member-row .member-badge {
  font-size: 11px;
  color: #409eff;
  background: #ecf5ff;
  padding: 0 4px;
  border-radius: 3px;
}

.member-row .member-role-tag {
  font-size: 10px;
  background: #e6f7ff;
  color: #1890ff;
  padding: 1px 6px;
  border-radius: 3px;
  border: 1px solid #91d5ff;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.chat-loading {
  display: flex;
  justify-content: center;
  padding: 40px;
  color: #c0c4cc;
}

.chat-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.msg-row {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  align-items: flex-start;
}

.msg-row.mine {
  flex-direction: row-reverse;
}

.msg-avatar {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
  transition: transform 0.15s;
}
.msg-avatar:hover { transform: scale(1.1); }

.msg-body {
  max-width: 60%;
}

.msg-row.mine .msg-body {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.msg-sender {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.msg-row.mine .msg-sender {
  text-align: right;
}

.msg-bubble {
  padding: 10px 14px;
  background: #f0f0f0;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
}

.msg-row.mine .msg-bubble {
  background: #409eff;
  color: #fff;
}

/* ── Markdown content styling ── */
.msg-bubble :deep(p) { margin: 0 0 6px; }
.msg-bubble :deep(p:last-child) { margin-bottom: 0; }
.msg-bubble :deep(strong) { font-weight: 600; }
.msg-bubble :deep(em) { font-style: italic; }
.msg-bubble :deep(code) {
  background: rgba(0,0,0,0.08);
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 13px;
  font-family: 'SF Mono', 'Fira Code', monospace;
}
.msg-row.mine .msg-bubble :deep(code) { background: rgba(255,255,255,0.2); }
.msg-bubble :deep(pre) {
  background: rgba(0,0,0,0.06);
  padding: 8px 12px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 6px 0;
  font-size: 13px;
}
.msg-row.mine .msg-bubble :deep(pre) { background: rgba(255,255,255,0.15); }
.msg-bubble :deep(ul), .msg-bubble :deep(ol) { margin: 4px 0; padding-left: 18px; }
.msg-bubble :deep(li) { margin-bottom: 2px; }
.msg-bubble :deep(blockquote) {
  border-left: 3px solid #d0d0d0;
  margin: 4px 0;
  padding: 2px 10px;
  color: #666;
}
.msg-row.mine .msg-bubble :deep(blockquote) {
  border-left-color: rgba(255,255,255,0.4);
  color: rgba(255,255,255,0.85);
}
.msg-bubble :deep(a) { color: #409eff; text-decoration: underline; }
.msg-row.mine .msg-bubble :deep(a) { color: #fff; }
.msg-bubble :deep(h1), .msg-bubble :deep(h2), .msg-bubble :deep(h3) { margin: 4px 0; font-size: 1em; font-weight: 600; }
.msg-bubble :deep(hr) { border: none; border-top: 1px solid #ddd; margin: 8px 0; }

/* ── Inline images ── */
.msg-bubble :deep(.msg-image-wrapper) {
  margin: 6px 0;
  max-width: 320px;
  cursor: pointer;
}
.msg-bubble :deep(.msg-image-wrapper img) {
  width: 100%;
  border-radius: 6px;
  display: block;
  transition: filter 0.15s;
}
.msg-bubble :deep(.msg-image-wrapper:hover img) {
  filter: brightness(0.95);
}
.msg-bubble :deep(.msg-image-wrapper.expanded img) {
  max-width: 100vw;
  max-height: 70vh;
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 9999;
  width: auto;
  height: auto;
  border-radius: 10px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.4);
}
.msg-bubble :deep(.msg-image-wrapper.expanded::after) {
  content: '';
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  z-index: 9998;
}
.msg-bubble :deep(.msg-image-caption) {
  display: block;
  font-size: 11px;
  color: #999;
  margin-top: 3px;
}

/* ── File download cards ── */
.msg-bubble :deep(.file-card) {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(0,0,0,0.04);
  border-radius: 8px;
  padding: 10px 14px;
  margin: 4px 0;
  max-width: 280px;
}
.msg-row.mine .msg-bubble :deep(.file-card) {
  background: rgba(255,255,255,0.15);
}
.msg-bubble :deep(.file-card-icon) {
  width: 40px;
  height: 40px;
  background: #fff;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.msg-bubble :deep(.file-card-body) {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.msg-bubble :deep(.file-card-name) {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
  text-decoration: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.msg-row.mine .msg-bubble :deep(.file-card-name) { color: #fff; }
.msg-bubble :deep(.file-card-hint) {
  font-size: 11px;
  color: #999;
}
.msg-row.mine .msg-bubble :deep(.file-card-hint) { color: rgba(255,255,255,0.7); }

.msg-time {
  font-size: 11px;
  color: #c0c4cc;
  margin-top: 4px;
  padding: 0 2px;
}

.msg-row.mine .msg-time {
  text-align: right;
}

.chat-input {
  padding: 10px 20px 14px;
  border-top: 1px solid #e8e8e8;
  background: #fafafa;
}

.input-toolbar {
  display: flex;
  gap: 4px;
  margin-top: 6px;
}

.upload-trigger {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 6px;
  cursor: pointer;
  color: #999;
  transition: all 0.15s;
}
.upload-trigger:hover { background: #e8e8e8; color: #666; }
.upload-trigger.active { color: #409eff; }

/* ═══ Welcome ═══ */
.welcome {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #fff;
  color: #909399;
}

.welcome-icon {
  margin-bottom: 16px;
}

.welcome h2 {
  font-size: 20px;
  color: #606266;
  margin-bottom: 8px;
}

.welcome p {
  font-size: 14px;
}

/* ═══ Group modal ═══ */
.member-checklist {
  max-height: 260px;
  overflow-y: auto;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  padding: 8px 12px;
  width: 100%;
}

.member-item {
  padding: 6px 0;
  border-bottom: 1px solid #f5f5f5;
}

.member-item:last-child {
  border-bottom: none;
}

.member-name {
  font-size: 14px;
  color: #303133;
}

.member-meta {
  font-size: 12px;
  color: #909399;
  margin-left: 6px;
}

/* ═══ @Mention popup ═══ */
.input-wrapper {
  position: relative;
}

.mention-popup {
  position: absolute;
  bottom: 100%;
  left: 0;
  margin-bottom: 4px;
  width: 320px;
  max-height: 280px;
  overflow-y: auto;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 -2px 12px rgba(0,0,0,0.12), 0 4px 12px rgba(0,0,0,0.08);
  z-index: 1000;
}

.mention-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  cursor: pointer;
  transition: background 0.15s;
}

.mention-item:hover,
.mention-item.active {
  background: #ecf5ff;
}

.mention-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #409eff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}

.mention-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.mention-name {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.mention-handle {
  font-size: 12px;
  color: #409eff;
  margin-top: 1px;
}

.mention-badge {
  font-size: 11px;
  background: #e6f7ff;
  color: #1890ff;
  padding: 2px 6px;
  border-radius: 3px;
  flex-shrink: 0;
}
</style>