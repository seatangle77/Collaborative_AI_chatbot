<template>
  <el-container class="dashboard-container">
    <!-- 📌 头部 -->
    <el-header class="dashboard-header">
      <!-- ✅ 小组选择 -->
      <el-select
        v-model="selectedGroupId"
        class="group-select"
        @change="selectGroup"
      >
        <el-option
          v-for="group in groups"
          :key="group.id"
          :label="group.name"
          :value="group.id"
        />
      </el-select>

      <!-- ✅ 用户选择（仅显示当前小组的用户） -->
      <el-select
        v-model="selectedUser"
        placeholder="选择用户"
        class="user-select"
      >
        <el-option
          v-for="(name, userId) in filteredUsers"
          :key="userId"
          :label="name"
          :value="userId"
        />
      </el-select>

      <!-- ✅ 标题：当前用户 + Session 名称 -->
      <div class="header-title">
        {{ currentUserName }}
        <span class="agent-name">🤖 {{ agentName }}</span>
        - {{ selectedSessionTitle || "No Active Session" }}
      </div>

      <!-- ✅ AI 供应商选择器 -->
      <el-select
        v-model="selectedAiProvider"
        class="ai-provider-select"
        @change="changeAiProvider"
      >
        <el-option label="xAI" value="xai" />
        <el-option label="HKUST GZ" value="hkust_gz" />
      </el-select>
    </el-header>

    <!-- 📌 主体 -->
    <el-container class="main-content">
      <!-- ✅ 聊天记录 -->
      <el-main class="chat-section">
        <ChatWindow
          :messages="messages"
          :users="users"
          :groupId="selectedGroupId"
          :sessionId="selectedSessionId"
          :userId="selectedUser"
          :aiProvider="selectedAiProvider"
        />
      </el-main>

      <!-- ✅ 右侧 AI 助手 -->
      <el-aside class="side-panel">
        <RealTimeSummary :discussion_summary="chatSummaries" />
        <TerminologyHelper />
        <ReminderPanel />
      </el-aside>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue";
import axios from "axios";
import ChatWindow from "../components/ChatWindow.vue";
import RealTimeSummary from "../components/RealTimeSummary.vue";
import TerminologyHelper from "../personal_device/TerminologyHelper.vue";
import ReminderPanel from "../personal_device/ReminderPanel.vue";
import {
  createWebSocket,
  onMessageReceived,
  closeWebSocket,
  changeAiProviderAndTriggerSummary,
} from "../services/websocketService";

// ✅ **存储状态**
const messages = ref([]);
const users = ref({});
const chatSummaries = ref([]);
const groups = ref([]);
const groupMembers = ref([]);
const selectedUser = ref(null);
const selectedGroupId = ref(null);
const selectedSessionId = ref(null);
const selectedSessionTitle = ref("");
const currentUserName = ref("未登录用户");
const selectedAiProvider = ref("xai");
const agentName = ref("无 AI 代理");

// 获取用户对应的 AI 代理
const fetchUserAgent = async (userId) => {
  if (!userId) {
    agentName.value = "无 AI 代理";
    return;
  }

  try {
    const response = await axios.get(
      `http://localhost:8000/api/users/${userId}/agent`
    );
    agentName.value = response.data.agent_name || "无 AI 代理";
  } catch (error) {
    console.error("获取 AI 代理失败:", error);
    agentName.value = "无 AI 代理";
  }
};

// ✅ **计算当前小组的用户**
const filteredUsers = computed(() => {
  if (!selectedGroupId.value || !users.value || !groupMembers.value.length)
    return {};
  return Object.fromEntries(
    Object.entries(users.value).filter(([userId]) =>
      groupMembers.value.includes(userId)
    )
  );
});

// ✅ **监听 `filteredUsers` 变化，确保 `selectedUser` 有默认值**
watch(
  filteredUsers,
  (newUsers) => {
    if (Object.keys(newUsers).length > 0) {
      selectedUser.value = Object.keys(newUsers)[0]; // 选当前小组的第一个用户
      currentUserName.value = newUsers[selectedUser.value];
    }
  },
  { immediate: true }
);

// ✅ **获取所有小组**
const fetchGroups = async () => {
  try {
    const response = await axios.get("http://localhost:8000/api/groups");
    groups.value = response.data;
    if (groups.value.length > 0) {
      selectGroup(groups.value[0].id);
    }
  } catch (error) {
    console.error("获取小组数据失败:", error);
  }
};

// ✅ 切换 AI 供应商
const changeAiProvider = () => {
  if (!selectedGroupId.value) return;
  console.log(`🔄 AI 供应商切换: ${selectedAiProvider.value}，触发 AI 总结`);
  changeAiProviderAndTriggerSummary(
    selectedGroupId.value,
    selectedAiProvider.value
  );
};

// ✅ **获取所有用户**
const fetchUsers = async () => {
  try {
    const response = await axios.get("http://localhost:8000/api/users");
    users.value = response.data.reduce((acc, user) => {
      acc[user.user_id] = user.name;
      return acc;
    }, {});

    // ✅ 如果 `users` 里有用户，默认选中第一个
    if (Object.keys(users.value).length > 0) {
      selectedUser.value = Object.keys(users.value)[0];
      currentUserName.value = users.value[selectedUser.value] || "未登录用户";
    }
  } catch (error) {
    console.error("获取用户列表失败:", error);
  }
};

// ✅ **获取小组成员**
const fetchGroupMembers = async (groupId) => {
  if (!groupId) return;
  try {
    const response = await axios.get(
      `http://localhost:8000/api/groups/${groupId}/members`
    );
    groupMembers.value = response.data.map((member) => member.user_id);
  } catch (error) {
    console.error("获取小组成员失败:", error);
  }
};

// ✅ **监听 groupId 变化，自动更新选中的用户**
watch(
  [selectedGroupId, users, groupMembers],
  () => {
    if (selectedGroupId.value && Object.keys(filteredUsers.value).length > 0) {
      selectedUser.value = Object.keys(filteredUsers.value)[0]; // 选中当前组的第一个用户
      currentUserName.value = filteredUsers.value[selectedUser.value];
    }
  },
  { immediate: true }
);

// ✅ **监听 `users` 变化，动态更新 `selectedUser`**
watch(
  users,
  (newUsers) => {
    if (newUsers && Object.keys(newUsers).length > 0) {
      selectedUser.value = Object.keys(newUsers)[0];
      currentUserName.value = newUsers[selectedUser.value] || "未登录用户";
    }
  },
  { immediate: true }
);

// ✅ **选择小组**
const selectGroup = async (groupId) => {
  if (!groupId || groupId === selectedGroupId.value) return;
  selectedGroupId.value = groupId;
  closeWebSocket();
  fetchGroupMembers(groupId);
  fetchSessionAndData(groupId);
};

// ✅ **获取当前 Session**
const fetchSessionAndData = async (groupId) => {
  try {
    const response = await axios.get(
      `http://localhost:8000/api/sessions/${groupId}`
    );
    selectedSessionId.value = response.data.id;
    selectedSessionTitle.value = response.data.session_title;
    fetchChatData(groupId);
  } catch (error) {
    console.error("获取 Session 失败:", error);
  }
};

// ✅ **获取聊天记录**
const fetchChatHistory = async (groupId) => {
  if (!groupId) return;
  try {
    const response = await axios.get(
      `http://localhost:8000/api/chat/${groupId}`
    );
    messages.value = response.data.reverse();
  } catch (error) {
    console.error("获取聊天记录失败:", error);
  }
};

// ✅ **获取 AI 会议总结**
const fetchChatSummaries = async (groupId) => {
  if (!groupId) return;
  try {
    const response = await axios.get(
      `http://localhost:8000/api/chat_summaries/${groupId}`
    );
    chatSummaries.value = response.data;
  } catch (error) {
    console.error("获取 AI 会议总结失败:", error);
  }
};

// ✅ **初始化 WebSocket**
const initWebSocket = (groupId) => {
  if (!groupId) return;
  createWebSocket(groupId);

  onMessageReceived((data) => {
    if (data.type === "message") {
      messages.value.push(data.message);
    } else if (data.type === "ai_summary") {
      chatSummaries.value.push({ summary_text: data.summary_text });
    }
  });
};

// ✅ **获取所有聊天数据**
const fetchChatData = async (groupId) => {
  if (!groupId) return;
  fetchUsers(); // ✅ 先获取用户
  fetchGroupMembers(groupId);
  fetchChatHistory(groupId);
  fetchChatSummaries(groupId);
  initWebSocket(groupId);
};

// ✅ **监听小组变化，自动更新数据**
watch(selectedGroupId, async (newGroupId) => {
  if (newGroupId) {
    fetchChatData(newGroupId);
  }
});

// ✅ **监听用户变化**
watch(
  selectedUser,
  (newUserId) => {
    if (newUserId && users.value[newUserId]) {
      currentUserName.value = users.value[newUserId];
      fetchUserAgent(newUserId);
    }
  },
  { immediate: true }
);

// ✅ **页面加载时获取数据**
onMounted(() => {
  fetchGroups();
  fetchUsers(); // ✅ 确保初始化时获取所有用户
});
</script>

<style scoped>
.dashboard-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f7f8fc;
}
.agent-name {
  font-size: 16px;
  font-weight: bold;
  color: #fff;
  background: rgba(255, 152, 0, 0.1);
  padding: 4px 8px;
  border-radius: 5px;
  margin-left: 8px;
}

.dashboard-header {
  background: linear-gradient(135deg, #ffa726, #fb8c00);
  color: white;
  padding: 16px 20px;
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.group-select,
.ai-provider-select {
  width: 180px;
  border-radius: 8px;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  transition: background 0.3s ease;
}

.user-select {
  width: 150px;
  margin-left: -13%;
}

.main-content {
  display: flex;
  flex: 1;
  padding: 20px;
}

.chat-section {
  flex: 2;
  background: white;
  padding: 15px;
  border-radius: 10px;
  box-shadow: 0px 3px 8px rgba(0, 0, 0, 0.08);
  overflow-y: auto;
  min-height: 400px;
}

.side-panel {
  flex: 1;
  padding: 15px;
  background: #ffffff;
  border-radius: 10px;
  box-shadow: 0px 3px 8px rgba(0, 0, 0, 0.1);
  margin-left: 15px;
}
</style>
