<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getMyProfile, updateProfile, changePassword, uploadFile } from '@/api/user'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

// ── Tab routing from query ──
const activeTab = ref<string>((route.query.tab as string) || 'profile')
watch(() => route.query.tab, (val) => {
  if (val) activeTab.value = val as string
})
function switchTab(tab: string) {
  activeTab.value = tab
  router.replace({ query: { tab } })
}

// ── Profile ──
const profile = ref({
  username: '',
  display_name: '',
  avatar_emoji: '',
  avatar_url: '',
  email: '',
  role: '',
})

const saving = ref(false)

const AVATAR_EMOJIS = [
  '😊', '😎', '🤖', '🦊', '🐱', '🐶', '🐼', '🐨', '🐯', '🦁',
  '🐮', '🐷', '🐸', '🐵', '🐔', '🐧', '🐦', '🐤', '🦄', '🐙',
  '👽', '🤠', '😇', '🤓', '🧑‍💻', '👩‍💻', '👨‍🔧', '👩‍🏭', '🧑‍🚀', '🦸',
  '🌟', '🔥', '💡', '🎯', '🚀', '💎', '🎨', '🎵', '📚', '⚡',
]

async function loadProfile() {
  try {
    const resp = await getMyProfile()
    Object.assign(profile.value, resp.data.data)
  } catch { /* defaults */ }
}

async function doSaveProfile() {
  if (!profile.value.display_name) { ElMessage.warning('请填写显示名称'); return }
  saving.value = true
  try {
    await updateProfile({
      display_name: profile.value.display_name,
      avatar_emoji: profile.value.avatar_emoji,
      avatar_url: profile.value.avatar_url,
      email: profile.value.email,
    })
    if (auth.userInfo) {
      auth.userInfo.display_name = profile.value.display_name
    }
    localStorage.setItem('user_info', JSON.stringify(auth.userInfo))
    ElMessage.success('个人资料已更新')
  } catch (e: any) {
    const msg = e?.response?.data?.detail?.message || '保存失败'
    ElMessage.error(msg)
  } finally { saving.value = false }
}

// ── Avatar upload ──
const avatarUploading = ref(false)
async function onAvatarUpload(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) { ElMessage.warning('请选择图片文件'); return }
  avatarUploading.value = true
  try {
    const resp = await uploadFile(file)
    profile.value.avatar_url = resp.data.data.url
    profile.value.avatar_emoji = ''  // clear emoji when using image
    ElMessage.success('头像已上传')
  } catch { ElMessage.error('头像上传失败') }
  finally { avatarUploading.value = false; input.value = '' }
}

// ── Password ──
const pwdSaving = ref(false)
const pwdForm = ref({ current_password: '', new_password: '', confirm_password: '' })

async function doChangePassword() {
  if (!pwdForm.value.current_password || !pwdForm.value.new_password) {
    ElMessage.warning('请填写完整密码信息'); return
  }
  if (pwdForm.value.new_password !== pwdForm.value.confirm_password) {
    ElMessage.warning('两次输入的新密码不一致'); return
  }
  if (pwdForm.value.new_password.length < 6) {
    ElMessage.warning('密码长度至少6个字符'); return
  }
  pwdSaving.value = true
  try {
    await changePassword({
      current_password: pwdForm.value.current_password,
      new_password: pwdForm.value.new_password,
    })
    ElMessage.success('密码已修改')
    pwdForm.value = { current_password: '', new_password: '', confirm_password: '' }
  } catch (e: any) {
    const msg = e?.response?.data?.detail?.message || '密码修改失败'
    ElMessage.error(msg)
  } finally { pwdSaving.value = false }
}

// ── Avatar preview computed ──
function avatarPreview(): string | null {
  if (profile.value.avatar_url) return profile.value.avatar_url
  if (profile.value.avatar_emoji) return null  // emoji is rendered as text
  return null
}

onMounted(loadProfile)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h3>⚙️ 个人设置</h3>
    </div>

    <!-- Tabs -->
    <div class="settings-tabs">
      <div
        class="settings-tab"
        :class="{ active: activeTab === 'profile' }"
        @click="switchTab('profile')"
      >
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
        用户信息完善
      </div>
      <div
        class="settings-tab"
        :class="{ active: activeTab === 'security' }"
        @click="switchTab('security')"
      >
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
        用户安全
      </div>
    </div>

    <!-- ── Profile tab ── -->
    <div v-if="activeTab === 'profile'" class="tab-content">
      <el-card shadow="hover" class="settings-card">
        <el-form label-position="top">
          <el-form-item label="头像">
            <div class="avatar-section">
              <div class="avatar-preview">
                <img v-if="avatarPreview()" :src="avatarPreview()" class="avatar-img" />
                <span v-else class="avatar-emoji-big">{{ profile.avatar_emoji || '😊' }}</span>
              </div>
              <div class="avatar-actions">
                <label class="upload-btn" :class="{ loading: avatarUploading }">
                  {{ avatarUploading ? '上传中...' : '上传图片' }}
                  <input type="file" accept="image/*" style="display:none" @change="onAvatarUpload" :disabled="avatarUploading" />
                </label>
                <span style="font-size:12px;color:#999;margin-left:8px">或选择表情</span>
              </div>
            </div>
            <div class="emoji-picker-grid">
              <span
                v-for="emoji in AVATAR_EMOJIS"
                :key="emoji"
                class="emoji-option"
                :class="{ selected: profile.avatar_emoji === emoji }"
                @click="profile.avatar_url = ''; profile.avatar_emoji = emoji"
              >{{ emoji }}</span>
            </div>
          </el-form-item>

          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="用户名">
                <el-input v-model="profile.username" disabled />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="角色">
                <el-tag>{{ profile.role === 'factory_admin' ? '工厂管理员' : profile.role === 'idh_admin' ? 'IDH 管理员' : profile.role }}</el-tag>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="显示名称" required>
                <el-input v-model="profile.display_name" placeholder="输入显示名称" maxlength="30" show-word-limit />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="邮箱">
                <el-input v-model="profile.email" placeholder="example@idh.com" type="email" maxlength="200" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item>
            <el-button type="primary" :loading="saving" @click="doSaveProfile">保存资料</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- ── Security tab ── -->
    <div v-if="activeTab === 'security'" class="tab-content">
      <el-card shadow="hover" class="settings-card">
        <template #header>
          <span class="card-title">🔒 修改密码</span>
        </template>
        <el-form label-position="top" style="max-width:420px">
          <el-form-item label="当前密码">
            <el-input v-model="pwdForm.current_password" type="password" show-password placeholder="输入当前密码" />
          </el-form-item>
          <el-form-item label="新密码">
            <el-input v-model="pwdForm.new_password" type="password" show-password placeholder="至少6个字符" />
          </el-form-item>
          <el-form-item label="确认新密码">
            <el-input v-model="pwdForm.confirm_password" type="password" show-password placeholder="再次输入新密码" />
          </el-form-item>
          <el-form-item>
            <el-button type="warning" :loading="pwdSaving" @click="doChangePassword">修改密码</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.page { padding: 24px 32px; }
.page-header { margin-bottom: 20px; }
.page-header h3 { margin: 0; font-size: 18px; color: #303133; }

/* ── Tabs ── */
.settings-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
  border-bottom: 1px solid #e8e8e8;
}

.settings-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  font-size: 14px;
  color: #606266;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: all 0.15s;
}
.settings-tab:hover { color: #409eff; }
.settings-tab.active { color: #409eff; border-bottom-color: #409eff; font-weight: 600; }

.tab-content { max-width: 700px; }

.settings-card { border-radius: 8px; }

.card-title { font-size: 15px; font-weight: 600; color: #303133; }

/* ── Avatar section ── */
.avatar-section {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 14px;
}

.avatar-preview {
  width: 72px;
  height: 72px;
  border-radius: 8px;
  background: #f5f7fa;
  border: 2px dashed #d9d9d9;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-emoji-big {
  font-size: 36px;
  line-height: 1;
}

.avatar-actions { display: flex; align-items: center; }

.upload-btn {
  display: inline-block;
  padding: 6px 16px;
  background: #409eff;
  color: #fff;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: opacity 0.15s;
}
.upload-btn:hover { opacity: 0.85; }
.upload-btn.loading { opacity: 0.6; pointer-events: none; }

.emoji-picker-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.emoji-option {
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  border-radius: 6px;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.15s;
  background: #f5f7fa;
}
.emoji-option:hover { background: #ecf5ff; transform: scale(1.1); }
.emoji-option.selected { border-color: #409eff; background: #ecf5ff; }
</style>