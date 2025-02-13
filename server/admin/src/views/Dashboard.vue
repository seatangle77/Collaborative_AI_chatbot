<template>
  <el-container>
    <!-- 侧边栏 -->
    <el-aside width="250px">
      <el-menu :default-openeds="['1', '2', '3', '4']">
        <el-sub-menu index="1">
          <template #title
            ><el-icon><User /></el-icon>用户管理</template
          >
          <el-menu-item v-for="api in apiCategories[0].apis" :key="api.url">
            <el-icon><UserFilled /></el-icon> {{ api.name }}
          </el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="2">
          <template #title
            ><el-icon><Menu /></el-icon>小组管理</template
          >
          <el-menu-item v-for="api in apiCategories[1].apis" :key="api.url">
            <el-icon><Menu /></el-icon> {{ api.name }}
          </el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="3">
          <template #title
            ><el-icon><ChatDotRound /></el-icon>聊天管理</template
          >
          <el-menu-item v-for="api in apiCategories[2].apis" :key="api.url">
            <el-icon><ChatDotRound /></el-icon> {{ api.name }}
          </el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="4">
          <template #title
            ><el-icon><Cpu /></el-icon>AI 机器人</template
          >
          <el-menu-item v-for="api in apiCategories[3].apis" :key="api.url">
            <el-icon><Cpu /></el-icon> {{ api.name }}
          </el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="5">
          <template #title
            ><el-icon><ChatDotRound /></el-icon>聊天议程与汇总</template
          >
          <el-menu-item v-for="api in apiCategories[4].apis" :key="api.url">
            <el-icon><ChatDotRound /></el-icon> {{ api.name }}
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <!-- 主要内容 -->
    <el-container>
      <el-header>
        <div>后台管理面板</div>
      </el-header>
      <el-main>
        <el-card class="dashboard-card">
          <h2>API 测试</h2>
          <div v-for="(category, index) in apiCategories" :key="index">
            <el-divider>{{ category.category }}</el-divider>
            <div class="api-buttons">
              <ApiButton
                v-for="api in category.apis"
                :key="api.url"
                :apiUrl="api.url"
                :label="api.name"
              />
            </div>
          </div>
        </el-card>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref } from "vue";
import {
  Menu,
  User,
  UserFilled,
  ChatDotRound,
  Cpu,
} from "@element-plus/icons-vue";
import ApiButton from "../components/ApiButton.vue"; // ✅ 引入 API 按钮组件

// API 分类数据
const apiCategories = ref([
  {
    category: "用户管理 API",
    apis: [
      { name: "获取所有用户", url: "http://localhost:8000/api/users" },
      {
        name: "获取单个用户",
        url: "http://localhost:8000/api/users/{user_id}",
      },
    ],
  },
  {
    category: "小组管理 API",
    apis: [
      { name: "获取所有小组", url: "http://localhost:8000/api/groups" },
      {
        name: "获取单个小组",
        url: "http://localhost:8000/api/groups/{group_id}",
      },
      {
        name: "获取小组成员",
        url: "http://localhost:8000/api/groups/{group_id}/members",
      },
    ],
  },
  {
    category: "聊天 API",
    apis: [
      {
        name: "获取聊天记录",
        url: "http://localhost:8000/api/chat/{group_id}",
      },
      { name: "发送聊天消息", url: "http://localhost:8000/api/chat/send" },
    ],
  },
  {
    category: "AI 机器人 API",
    apis: [
      { name: "AI 生成回答", url: "http://localhost:8000/api/ai/respond" },
    ],
  },
  {
    category: "聊天议程与汇总 API",
    apis: [
      {
        name: "获取聊天议程",
        url: "http://localhost:8000/api/chat/agenda/{group_id}",
      },
      {
        name: "获取聊天汇总",
        url: "http://localhost:8000/api/chat/summary/{group_id}",
      },
    ],
  },
]);
</script>

<style scoped>
/* 页面布局 */
.el-container {
  height: 100vh;
}

.el-header {
  background: #f5f7fa;
  padding: 20px;
  font-size: 20px;
  font-weight: bold;
  text-align: center;
}

.el-main {
  padding: 20px;
}

/* 卡片样式 */
.dashboard-card {
  padding: 20px;
}

/* API 按钮区域 */
.api-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 10px;
}
</style>
