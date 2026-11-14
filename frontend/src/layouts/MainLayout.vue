<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <el-container class="layout">
    <el-aside width="200px">
      <div class="logo">IDH 平台</div>
      <el-menu
        :default-active="route.path"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <el-menu-item index="/">
          <el-icon><svg viewBox="0 0 24 24" width="18" height="18"><rect x="3" y="3" width="7" height="7" fill="currentColor"/><rect x="14" y="3" width="7" height="7" fill="currentColor"/><rect x="3" y="14" width="7" height="7" fill="currentColor"/><rect x="14" y="14" width="7" height="7" fill="currentColor"/></svg></el-icon>
          <span>工作台</span>
        </el-menu-item>
        <el-menu-item index="/work-orders">
          <el-icon><svg viewBox="0 0 24 24" width="18" height="18"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" fill="none" stroke="currentColor" stroke-width="2"/></svg></el-icon>
          <span>工单管理</span>
        </el-menu-item>
        <el-menu-item index="/shipments">
          <el-icon><svg viewBox="0 0 24 24" width="18" height="18"><rect x="1" y="3" width="15" height="13" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><polygon points="16,8 20,14 23,14 23,21 16,21" fill="none" stroke="currentColor" stroke-width="2"/></svg></el-icon>
          <span>发货管理</span>
        </el-menu-item>
        <el-menu-item index="/inventory">
          <el-icon><svg viewBox="0 0 24 24" width="18" height="18"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" fill="none" stroke="currentColor" stroke-width="2"/></svg></el-icon>
          <span>库存管理</span>
        </el-menu-item>
        <el-menu-item index="/alerts">
          <el-icon><svg viewBox="0 0 24 24" width="18" height="18"><circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/><line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2"/><line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="2"/></svg></el-icon>
          <span>告警中心</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header>
        <span class="user-info">
          {{ auth.userInfo?.username }} ({{ auth.userInfo?.role }})
        </span>
        <el-button text @click="handleLogout">退出</el-button>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout {
  height: 100vh;
}
.el-aside {
  background: #304156;
  overflow: hidden;
}
.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  background: #2b3a4a;
}
.el-menu {
  border-right: none;
}
.el-header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  border-bottom: 1px solid #e4e7ed;
  background: #fff;
  padding: 0 20px;
}
.user-info {
  margin-right: 12px;
  color: #606266;
  font-size: 14px;
}
.el-main {
  background: #f0f2f5;
}
</style>