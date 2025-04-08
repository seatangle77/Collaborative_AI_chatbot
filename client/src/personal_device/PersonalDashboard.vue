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
          v-for="(user, userId) in filteredUsersInfo"
          :key="userId"
          :label="user.name"
          :value="userId"
        />
      </el-select>

      <el-button
        type="success"
        @click="handleUpdatePersonalPrompt"
        :disabled="!selectedUser"
        style="margin-left: 12px; margin-left: -4%"
      >
        Update PersonalAgent Prompt
      </el-button>

      <!-- ✅ 标题：当前用户 + Session 名称 -->
      <div class="header-title">
        <span v-if="selectedUser && users[selectedUser]">
          {{ users[selectedUser].name }}
        </span>
        <span
          class="agent-name"
          @click="showDrawer = true"
          style="cursor: pointer"
        >
          🤖 {{ agentName }}
          <el-icon style="color: white; margin-left: 5px"
            ><InfoFilled
          /></el-icon>
        </span>
        - {{ selectedSessionTitle || "No Active Session" }}
      </div>

      <!-- ✅ AI 供应商选择器 -->
      <el-select
        v-model="selectedAiProvider"
        class="ai-provider-select"
        @change="changeAiProvider"
      >
        <el-option label="Grok-2" value="xai" />
        <el-option label="GPT-4o" value="hkust_gz" />
        <el-option label="Genmini-2.5-pro" value="gemini" />
      </el-select>
    </el-header>

    <!-- 📌 主体 -->
    <el-container class="main-content">
      <!-- ✅ 用户信息卡片 -->
      <el-aside class="left-panel">
        <UserProfileCard :user="filteredUsersInfo[selectedUser]" />
      </el-aside>

      <!-- ✅ 聊天记录 -->
      <el-main class="chat-section">
        <ChatWindow
          :messages="messages"
          :users="userNames"
          :usersInfo="filteredUsersInfo"
          :aiBots="aiBots"
          :groupId="selectedGroupId"
          :sessionId="selectedSessionId"
          :userId="selectedUser"
          :aiProvider="selectedAiProvider"
          :agentId="agentId"
        />
      </el-main>

      <!-- ✅ 右侧 AI 助手 -->
      <el-aside class="side-panel">
        <RealTimeSummary :discussion_summary="chatSummaries" />
        <TerminologyHelper />
        <ReminderPanel />
      </el-aside>
    </el-container>

    <PersonalAgentDrawer
      v-if="agentId"
      :visible="showDrawer"
      :agentId="agentId"
      :promptVersions="personalPromptVersions"
      @update:visible="showDrawer = $event"
    />
  </el-container>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { InfoFilled } from "@element-plus/icons-vue";
import api from "../services/apiService";
import ChatWindow from "../components/ChatWindow.vue";
import RealTimeSummary from "../components/RealTimeSummary.vue";
import TerminologyHelper from "../personal_device/TerminologyHelper.vue";
import ReminderPanel from "../personal_device/ReminderPanel.vue";
import UserProfileCard from "../components/UserProfileCard.vue";
import PersonalAgentDrawer from "../components/PersonalAgentDrawer.vue";
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
const aiBots = ref([]);
const groups = ref([]);
const groupMembers = ref([]);
const selectedUser = ref(null);
const selectedGroupId = ref(null);
const selectedSessionId = ref(null);
const selectedSessionTitle = ref("");
const currentUserName = ref("未登录用户");
const selectedAiProvider = ref("xai");
const agentName = ref("无 AI 代理");
const agentId = ref(null);
const showDrawer = ref(false);
const personalPromptVersions = ref({});

// 获取用户对应的 AI 代理
const fetchUserAgent = async (userId) => {
  if (!userId) {
    agentName.value = "无 AI 代理";
    agentId.value = null;
    return;
  }

  try {
    const response = await api.getUserAgent(userId);
    agentName.value = response.agent_name || "无 AI 代理";
    agentId.value = response.agent_id || null;
  } catch (error) {
    console.error("获取 AI 代理失败:", error);
    agentName.value = "无 AI 代理";
    agentId.value = null;
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

// ✅ **计算用户名称**
const userNames = computed(() => {
  return Object.fromEntries(
    Object.entries(users.value).map(([id, user]) => [id, user.name])
  );
});

// ✅ **计算过滤后的用户信息**
const filteredUsersInfo = computed(() => {
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
    const response = await api.getGroups();
    groups.value = response;
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
    const response = await api.getUsers();
    users.value = response.reduce((acc, user) => {
      acc[user.user_id] = user;
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
    const response = await api.getGroupMembers(groupId);
    groupMembers.value = response.map((member) => member.user_id);
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
    const response = await api.getSession(groupId);
    selectedSessionId.value = response.id;
    selectedSessionTitle.value = response.session_title;
    fetchChatData(groupId);
  } catch (error) {
    console.error("获取 Session 失败:", error);
  }
};

// ✅ **获取聊天记录**
const fetchChatHistory = async (groupId) => {
  if (!groupId) return;
  try {
    const response = await api.getChatHistory(groupId);
    messages.value = response.reverse();
  } catch (error) {
    console.error("获取聊天记录失败:", error);
  }
};

// ✅ **获取 AI 会议总结**
const fetchChatSummaries = async (groupId) => {
  if (!groupId) return;
  try {
    const response = await api.getChatSummaries(groupId);
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

// ✅ **监听 agentId 变化（用于通知子组件更新）**
watch(agentId, async (newAgentId) => {
  if (newAgentId) {
    try {
      personalPromptVersions.value = await api.getPersonalPromptVersions(
        newAgentId
      );
    } catch (e) {
      console.error("❌ Failed to load personal prompt versions:", e);
    }
  }
});

// ✅ **更新个人代理提示**
const handleUpdatePersonalPrompt = async () => {
  if (!selectedUser.value || !users.value[selectedUser.value]) return;
  const agentId = users.value[selectedUser.value].agent_id;
  if (!agentId) {
    ElMessage.warning("当前用户未绑定个人 Agent");
    return;
  }

  try {
    const response = await api.generatePersonalPrompt(agentId);
    ElMessage.success(
      response.message || "Personal agent prompts updated successfully!"
    );
    await fetchUserAgent(selectedUser.value); // ✅ 更新 agent 信息
  } catch (error) {
    console.error("Failed to update personal prompts:", error);
    ElMessage.error("Failed to update personal prompts.");
  }
};

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

.bot-name {
  font-weight: bold;
  color: #fff;
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
  width: 150px;
  border-radius: 8px;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  transition: background 0.3s ease;
}

.user-select {
  width: 130px;
  margin-left: -4%;
}

.main-content {
  display: flex;
  flex: 1;
  padding: 20px;
}

.left-panel {
  flex: 1;
  margin-right: 15px;
  background: #ffffff;
  border-radius: 10px;
  padding: 15px;
  box-shadow: 0px 3px 8px rgba(0, 0, 0, 0.08);
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
