<template>
  <el-container class="dashboard-container">
    <div class="dashboard-header-fixed">
      <PersonalDashboardHeader
        :groups="groups"
        :selectedGroupId="selectedGroupId"
        :selectedUser="selectedUser"
        :users="users"
        :filteredUsersInfo="filteredUsersInfo"
        :selectedSessionTitle="selectedSessionTitle"
        :agentName="agentName"
        :selectedAiProvider="selectedAiProvider"
        :agentInfo="agentInfoObject"
        @selectGroup="selectGroup"
        @selectUser="(val) => (selectedUser = val)"
        @updatePrompt="handleUpdatePersonalPrompt"
        @changeAiProvider="changeAiProvider"
        @toggleDrawer="showDrawer = true"
      />
    </div>

    <!-- 📌 主体 -->
    <el-container class="main-content">
      <div style="display: flex; align-items: center; margin-right: 10px">
        <el-button
          @click="showUserCard = !showUserCard"
          size="default"
          class="toggle-user-card-button"
        >
          <el-icon style="font-size: 20px">
            <component :is="showUserCard ? DArrowLeft : DArrowRight" />
          </el-icon>
        </el-button>
      </div>
      <el-aside
        class="left-user-card"
        :class="showUserCard ? 'user-card-expanded' : 'user-card-collapsed'"
      >
        <UserProfileCard
          v-show="showUserCard"
          :user="filteredUsersInfo[selectedUser]"
        />
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
          :agentModel="agentModel"
          :promptVersion="promptVersion_term_explanation"
          @closeQueryDialog="handleCloseQueryDialog"
        />
      </el-main>

      <!-- ✅ 右侧 AI 助手 -->
      <el-aside class="side-panel">
        <TerminologyHelper
          v-if="selectedGroupId && agentId"
          :groupId="selectedGroupId"
          :agentId="agentId"
          :refreshSignal="refreshSignal"
          @insightsResponse="handleInsightsResponse"
          @onCloseQueryDialog="handleCloseQueryDialog"
        />
        <!--<ReminderPanel />-->
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
import { InfoFilled, DArrowLeft, DArrowRight } from "@element-plus/icons-vue";
import api from "../services/apiService";
import ChatWindow from "../components/ChatWindow.vue";
import TerminologyHelper from "../personal_device/TerminologyHelper.vue";
import ReminderPanel from "../personal_device/ReminderPanel.vue";
import UserProfileCard from "../components/UserProfileCard.vue";
import PersonalAgentDrawer from "../components/PersonalAgentDrawer.vue";
import PersonalDashboardHeader from "../components/PersonalDashboardHeader.vue";
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
const agentModel = ref(null);
const showDrawer = ref(false);
const personalPromptVersions = ref({});
const agentInfoObject = ref({}); // Added
const userCardActiveNames = ref([]); // Added
const showUserCard = ref(false); // 默认收起
const refreshSignal = ref(Date.now()); // Added

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
    agentModel.value = response.agent_model || "xai";
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

const promptVersion_term_explanation = computed(() => {
  return (
    personalPromptVersions.value.term_explanation?.find((p) => p.is_current)
      ?.template_version || null
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
  async (newUserId) => {
    if (newUserId && users.value[newUserId]) {
      currentUserName.value = users.value[newUserId];
      await fetchUserAgent(newUserId);
      const agentInfo = await api.getAgentModel(agentId.value);
      if (agentInfo && agentInfo.model) {
        selectedAiProvider.value = agentInfo.model;
        agentInfoObject.value = agentInfo; // Added
      }
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

// ✅ **监听 selectedAiProvider 变化**
watch(selectedAiProvider, (newVal, oldVal) => {
  console.log(`🎯 AI 供应商变化: ${oldVal} → ${newVal}`);
  // 可以在此添加其他逻辑，如根据新的 AI 提供商刷新数据等
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

const handleInsightsResponse = (insights) => {
  console.log("📥 从 TerminologyHelper 回调回来的 insights：", insights);
  // 你可以在这里存储或处理这些术语解释结果
};

const handleCloseQueryDialog = () => {
  console.log("📪 ChatWindow 关闭查询弹窗，通知 TerminologyHelper 刷新");
  refreshSignal.value = Date.now(); // 触发刷新
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
.dashboard-header-fixed {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  will-change: transform;
  backface-visibility: hidden;
  transform: translateZ(0);
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
  margin-top: 80px;
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

.left-user-card {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  height: 100%;
  background: #ffffff;
  border-radius: 10px;
  padding: 15px;
  box-shadow: 0px 3px 8px rgba(0, 0, 0, 0.1);
  margin-right: 15px;
}

.toggle-user-card-button {
  position: fixed;
  top: 120px;
  left: 0;
  z-index: 999;
  background-color: #ffffff;
  border: 1px solid #dcdfe6;
  padding: 50px 5px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  border-radius: 0 6px 6px 0;
}

.user-card-expanded {
  width: 240px;
  padding: 15px;
  transition: width 0.3s ease, padding 0.3s ease;
}

.user-card-collapsed {
  width: 0;
  padding: 0;
  transition: width 0.3s ease, padding 0.3s ease;
  overflow: hidden;
}
</style>
