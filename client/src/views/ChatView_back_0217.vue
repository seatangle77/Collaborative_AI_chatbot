<template>
  <el-container class="chat-container">
    <!-- 侧边栏 -->
    <el-aside width="250px">
      <Sidebar @select-group="fetchChatData" />
    </el-aside>

    <el-container>
      <!-- 头部 -->
      <el-header class="chat-header">
        <div>聊天室</div>
      </el-header>

      <!-- 主体内容 -->
      <el-container class="main-content">
        <!-- 聊天窗口 -->
        <el-main class="chat-window">
          <ChatWindow :messages="messages" :users="users" />
          <MessageInput @send-message="sendMessage" />
        </el-main>

        <!-- 右侧功能区域 -->
        <el-aside width="500px" class="chat-sidebar">
          <el-card class="agenda-card">
            <h3>聊天议程</h3>
            <div v-for="agenda in chatAgendas" :key="agenda.id">
              <strong>{{ agenda.agenda_title }}</strong>
              <p>{{ agenda.agenda_description }}</p>
            </div>
          </el-card>

          <el-card class="summary-card">
            <h3>实时汇总</h3>
            <div v-for="summary in chatSummaries" :key="summary.id">
              <p>{{ summary.summary_text }}</p>
            </div>
          </el-card>

          <el-card class="recent-summary-card">
            <h3>前1分钟总结</h3>
            <div v-for="summary in recentSummary" :key="summary.id">
              <p>{{ summary.summary_text }}</p>
            </div>
          </el-card>
        </el-aside>
      </el-container>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";
import Sidebar from "../components/Sidebar.vue";
import ChatWindow from "../components/ChatWindow.vue";
import MessageInput from "../components/MessageInput.vue";

const messages = ref([]);
const users = ref({});
const chatAgendas = ref([]);
const chatSummaries = ref([]);
const recentSummary = ref([]);
const currentGroupId = ref("");
const discussionInsights = ref([]);
const discussionTerms = ref([]);

// 获取用户列表
const fetchUsers = async () => {
  try {
    const response = await axios.get("http://localhost:8000/api/users/");
    users.value = response.data.reduce((acc, user) => {
      acc[user.user_id] = user.name;
      return acc;
    }, {});
  } catch (error) {
    console.error("获取用户列表失败:", error);
  }
};

// 获取聊天记录
const fetchChatHistory = async (groupId) => {
  try {
    const response = await axios.get(
      `http://localhost:8000/api/chat/${groupId}`
    );
    messages.value = response.data;
  } catch (error) {
    console.error("获取聊天记录失败:", error);
  }
};

// 获取聊天议程
const fetchChatAgendas = async (groupId) => {
  try {
    const response = await axios.get(
      `http://localhost:8000/api/chat/agenda/${groupId}`
    );
    chatAgendas.value = response.data;
  } catch (error) {
    console.error("获取聊天议程失败:", error);
  }
};

// 获取聊天汇总
const fetchChatSummaries = async (groupId) => {
  try {
    const response = await axios.get(
      `http://localhost:8000/api/chat/summaries/${groupId}`
    );
    chatSummaries.value = response.data;
  } catch (error) {
    console.error("获取聊天汇总失败:", error);
  }
};

// 获取最近聊天总结
const fetchRecentSummary = async (groupId) => {
  try {
    const response = await axios.get(
      `http://localhost:8000/api/chat/summary/latest/${groupId}`
    );
    recentSummary.value = response.data;
  } catch (error) {
    console.error("获取最近聊天总结失败:", error);
  }
};

// 获取讨论见解
const fetchDiscussionInsights = async (groupId) => {
  try {
    const response = await axios.get(
      `http://localhost:8000/api/discussion/insights/${groupId}`
    );
    discussionInsights.value = response.data;
  } catch (error) {
    console.error("获取讨论见解失败:", error);
  }
};

// 获取讨论术语
const fetchDiscussionTerms = async (groupId) => {
  try {
    const response = await axios.get(
      `http://localhost:8000/api/discussion/terms/${groupId}`
    );
    discussionTerms.value = response.data;
  } catch (error) {
    console.error("获取讨论术语失败:", error);
  }
};

// 发送消息
const sendMessage = async (message) => {
  try {
    const response = await axios.post("http://localhost:8000/api/chat/send", {
      group_id: currentGroupId.value,
      user_id: "123",
      message,
    });
    messages.value.push(response.data);
  } catch (error) {
    console.error("发送消息失败:", error);
  }
};

// 获取聊天记录和相关数据
const fetchChatData = (groupId) => {
  currentGroupId.value = groupId;
  fetchChatHistory(groupId);
  fetchChatAgendas(groupId);
  fetchChatSummaries(groupId);
  fetchRecentSummary(groupId);
  fetchDiscussionInsights(groupId);
  fetchDiscussionTerms(groupId);
};

// 页面加载时获取第一个小组的数据
onMounted(() => {
  fetchUsers();
  fetchChatData("1178968c-480b-4ece-bbba-d759eb70f16b"); // 默认加载第一个小组数据
});
</script>

<style scoped>
.chat-container {
  height: 100vh;
  display: flex;
  flex-direction: row;
}

.chat-header {
  background: #409eff;
  color: white;
  padding: 20px;
  font-size: 24px;
  text-align: center;
}

.chat-footer {
  padding: 10px;
}

.main-content {
  display: flex;
  flex-direction: row;
  flex: 1;
}

.el-main {
  padding: 0 !important;
  margin: 0 !important;
  height: calc(100vh - 60px); /* 确保高度一致 */
  overflow: hidden; /* 避免溢出 */
}

.chat-sidebar {
  padding: 15px;
  background-color: #f4f4f4;
  height: 100%;
  overflow-y: auto;
  border-left: 1px solid #ddd;
}

.agenda-card,
.summary-card,
.recent-summary-card {
  margin-bottom: 15px;
  padding: 15px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.agenda-card h3,
.summary-card h3,
.recent-summary-card h3 {
  font-size: 18px;
  color: #409eff;
  margin: 0;
}

.agenda-card p,
.summary-card p,
.recent-summary-card p {
  font-size: 14px;
  color: #333;
}

.chat-window {
  padding: 20px;
  background-color: #fff;
  flex: 1;
  overflow-y: auto;
}

.el-menu-item {
  color: white;
  font-size: 16px;
}

.el-menu-item:hover {
  background-color: #2980b9;
}
</style>
