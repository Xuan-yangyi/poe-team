<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
</script>

<template>
  <div class="dashboard">
    <h2>欢迎使用 IDH 协同平台</h2>
    <el-row :gutter="20" style="margin-top: 24px">
      <el-col :span="6">
        <el-card shadow="hover">
          <router-link to="/work-orders" style="text-decoration: none; color: #303133;">
            <h3>工单管理</h3>
            <p style="color: #909399">创建、发行、变更工单</p>
          </router-link>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <router-link to="/shipments" style="text-decoration: none; color: #303133;">
            <h3>发货管理</h3>
            <p style="color: #909399">出货确认、收货登记</p>
          </router-link>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <router-link to="/inventory" style="text-decoration: none; color: #303133;">
            <h3>库存管理</h3>
            <p style="color: #909399">库存快照、批次流水</p>
          </router-link>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <router-link to="/alerts" style="text-decoration: none; color: #303133;">
            <h3>告警中心</h3>
            <p style="color: #909399">查看、确认、关闭告警</p>
          </router-link>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>