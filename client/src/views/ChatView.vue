<template>
  <el-container class="chat-container">
    <!-- 📌 头部优化 -->
    <el-header class="chat-header">
      <!-- ✅ 小组选择器 -->
      <el-select
        v-model="selectedGroupId"
        class="group-select"
        popper-class="custom-dropdown"
        @change="selectGroup"
      >
        <el-option
          v-for="group in groups"
          :key="group.id"
          :label="group.name"
          :value="group.id"
        />
      </el-select>

      <!-- ✅ 标题 -->
      <div class="header-title">
        {{ selectedSessionTitle || "No Active Session" }}
      </div>

      <!-- ✅ AI 供应商选择器 -->
      <el-select
        v-model="selectedAiProvider"
        class="ai-provider-select"
        popper-class="custom-dropdown"
        @change="changeAiProvider"
      >
        <el-option label="Grok-2" value="xai" />
        <el-option label="GPT-4o" value="hkust_gz" />
        <el-option label="Genmini-2.5-pro" value="gemini" />
      </el-select>
    </el-header>

    <!-- 📌 主体 -->
    <el-container class="main-content">
      <!-- 📌 左侧议程 -->
      <el-aside class="agenda-panel">
        <AgendaDisplay
          :agendas="chatAgendas"
          :groupName="selectedGroupName"
          :groupGoal="
            groups.find((g) => g.id === selectedGroupId)?.group_goal || ''
          "
        />
      </el-aside>

      <!-- ✅ 聊天窗口 & AI 实时总结 -->
      <el-main class="chat-area">
        <ChatWindow
          :messages="messages"
          :users="users"
          :aiBots="aiBots"
          :groupId="selectedGroupId"
          :sessionId="selectedSessionId"
          :userId="selectedUser"
          :aiProvider="selectedAiProvider"
        />
        <MessageInput
          :users="filteredUsers"
          :groupId="selectedGroupId"
          @send-message="sendMessage"
        />
      </el-main>

      <!-- ✅ AI 实时会议总结 -->
      <el-aside class="realtime-summary">
        <RealTimeSummary
          :discussion_summary="chatSummaries"
          :groupId="selectedGroupId"
        />
      </el-aside>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from "vue";
import axios from "axios";
import ChatWindow from "../components/ChatWindow.vue";
import MessageInput from "../components/MessageInput.vue";
import AgendaDisplay from "../components/AgendaDisplay.vue";
import RealTimeSummary from "../components/RealTimeSummary.vue";
import {
  createWebSocket,
  sendMessage as sendWebSocketMessage,
  onMessageReceived,
  closeWebSocket,
  changeAiProviderAndTriggerSummary as triggerWebSocketAiSummary,
} from "../services/websocketService";

// ✅ **存储状态**
const messages = ref([]);
const users = ref({});
const chatAgendas = ref([]);
const chatSummaries = ref([]); // ✅ 改名 `chatSummaries`
const selectedGroupName = ref("");
const selectedGroupId = ref(null);
const selectedSessionId = ref(null); // ✅ 存储当前 Session ID
const selectedSessionTitle = ref("");
const selectedUser = ref(null);
const groupMembers = ref([]);
const groups = ref([]);
const aiBots = ref([]);
const selectedAiProvider = ref("xai"); // ✅ 默认使用 xAI

// ✅ **切换 AI 供应商时自动触发 AI 会议总结**
const changeAiProvider = () => {
  if (!selectedGroupId.value) return;
  console.log(`🔄 AI 供应商切换: ${selectedAiProvider.value}，触发 AI 总结`);
  triggerWebSocketAiSummary(selectedGroupId.value, selectedAiProvider.value);
};

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

// ✅ **监听小组变化，自动更新数据**
watch(selectedGroupId, async (newGroupId) => {
  if (newGroupId) {
    fetchSessionAndData(newGroupId);
  }
});

// ✅ 在页面加载时获取所有 AI 机器人
const fetchAllAiBots = async () => {
  try {
    const response = await axios.get("http://localhost:8000/api/ai_bots");
    aiBots.value = response.data; // ✅ 存储所有机器人数据
  } catch (error) {
    console.error("获取 AI 机器人失败:", error);
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

// ✅ 监听 `filteredUsers`，确保有默认的 `selectedUser`
watch(
  filteredUsers,
  (newUsers) => {
    if (Object.keys(newUsers).length > 0) {
      selectedUser.value = Object.keys(newUsers)[0];
    }
  },
  { immediate: true }
);

// ✅ **切换小组**
const selectGroup = async (groupId) => {
  if (!groupId || groupId === selectedGroupId.value) return;
  selectedGroupId.value = groupId;
  selectedGroupName.value =
    groups.value.find((group) => group.id === groupId)?.name || "";

  closeWebSocket(); // 关闭旧的 WebSocket 连接
  fetchChatData(groupId);
};

// ✅ **获取聊天记录**
const fetchChatHistory = async (groupId) => {
  if (!groupId) return;
  try {
    const response = await axios.get(
      `http://localhost:8000/api/chat/${groupId}`
    );
    messages.value = response.data.reverse(); // 让最新的消息显示在底部
  } catch (error) {
    console.error("获取聊天记录失败:", error);
  }
};

// ✅ **获取当前小组的最新 Session，并获取该 Session 相关数据**
const fetchSessionAndData = async (groupId) => {
  try {
    const response = await axios.get(
      `http://localhost:8000/api/sessions/${groupId}`
    );

    console.log("fetchSessionAndData", response);
    selectedSessionId.value = response.data.id; // ✅ 记录当前 Session ID
    selectedSessionTitle.value = response.data.session_title;

    fetchChatData(groupId);
    fetchChatAgendas(selectedSessionId.value); // ✅ 用 session_id 获取议程
    fetchChatSummariesBySession(selectedSessionId.value); // ✅ 获取 AI 会议总结
  } catch (error) {
    console.error("获取小组当前 Session 失败:", error);
  }
};

// ✅ **获取议程**
const fetchChatAgendas = async (sessionId) => {
  if (!sessionId) return;
  try {
    const response = await axios.get(
      `http://localhost:8000/api/chat/agenda/session/${sessionId}`
    );
    chatAgendas.value = response.data;
  } catch (error) {
    console.error("获取聊天议程失败:", error);
  }
};

// ✅ **获取所有用户**
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

// ✅ **发送消息（字段补全）**
const sendMessage = async (payload) => {
  try {
    const response = await axios.post(
      "http://localhost:8000/api/chat/send",
      {
        group_id: payload.group_id,
        session_id: selectedSessionId.value, // ✅ 关联 session
        user_id: payload.user_id,
        chatbot_id: payload.chatbot_id || null,
        message: payload.message,
        role: payload.role || "user",
        message_type: payload.message_type || "text",
        sender_type: payload.sender_type || "user",
        speaking_duration: payload.speaking_duration || 0,
      },
      {
        headers: {
          "Content-Type": "application/json", // ✅ 解决 CORS content-type 问题
        },
      }
    );

    console.log("📤 发送消息到数据库:", response.data);
  } catch (error) {
    console.error("❌ 发送消息失败:", error);
  }
};

// ✅ **WebSocket 监听**
const initWebSocket = (groupId) => {
  if (!groupId) return;
  createWebSocket(groupId);

  onMessageReceived((data) => {
    try {
      console.log("📩 WebSocket 收到数据:", data);

      let parsedData;
      if (typeof data === "string") {
        parsedData = JSON.parse(data);
      } else {
        parsedData = data;
      }

      // ✅ **处理 WebSocket 消息类型**
      if (parsedData.message) {
        let newMessage = parsedData.message;
        if (Array.isArray(newMessage)) {
          newMessage = newMessage[0];
        }
        messages.value.push(newMessage);
        scrollToBottom();
      }
      console.log("🪐输出每一条消息", parsedData);

      if (parsedData.type === "ai_summary") {
        console.log("🤖 AI 会议总结收到:", parsedData.summary_text);
        chatSummaries.value.push({ summary_text: parsedData.summary_text });
      }
    } catch (error) {
      console.error("❌ WebSocket 消息解析错误:", error, "原始数据:", data);
    }
  });
};

// ✅ **滚动到底部**
const chatWindow = ref(null);
const scrollToBottom = () => {
  nextTick(() => {
    if (chatWindow.value) {
      chatWindow.value.$el.scrollTop = chatWindow.value.$el.scrollHeight;
    }
  });
};

// ✅ **获取所有聊天数据**
const fetchChatData = async (groupId) => {
  if (!groupId) return;
  await fetchUsers();
  await fetchGroupMembers(groupId);
  await fetchChatHistory(groupId);
  initWebSocket(groupId);
};

// ✅ **监听小组变化，自动更新数据**
watch(selectedGroupId, async (newGroupId) => {
  if (newGroupId) {
    // ✅ 更新聊天室标题
    selectedGroupName.value =
      groups.value.find((group) => group.id === newGroupId)?.name || "未知小组";

    // ✅ 更新聊天数据
    fetchChatData(newGroupId);
  }
});

// ✅ **根据 sessionId 获取 AI 会议总结**
const fetchChatSummariesBySession = async (sessionId) => {
  if (!sessionId) return;
  try {
    const response = await axios.get(
      `http://localhost:8000/api/chat_summaries/session/${sessionId}`
    );
    chatSummaries.value = [response.data]; // ✅ 只存储最新的一条
  } catch (error) {
    console.error("获取 AI 会议总结失败:", error);
  }
};

// ✅ **页面加载时获取小组信息**
onMounted(() => {
  fetchGroups();
  fetchAllAiBots(); // ✅ 这里初始化获取所有机器人
});
</script>

<style scoped>
/* 📌 整体布局 */
.chat-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

/* 📌 头部样式 */
.chat-header {
  background: linear-gradient(135deg, #409eff, #2878ff);
  color: white;
  padding: 16px 20px;
  font-size: 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

/* 📌 小组选择器 */
.group-select {
  width: 220px;
  border-radius: 8px;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  transition: background 0.3s ease;
}

.ai-provider-select {
  width: 150px;
  border-radius: 8px;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  transition: background 0.3s ease;
}

/* ✅ 下拉菜单优化 */
.custom-dropdown {
  border-radius: 10px;
  box-shadow: 0px 6px 12px rgba(0, 0, 0, 0.15);
}

/* 📌 标题 */
.header-title {
  flex-grow: 1;
  text-align: center;
  font-size: 22px;
  font-weight: 600;
  text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.2);
}

/* 📌 议程区域 */
.agenda-panel {
  flex: 1.2;
}
.agenda-display {
  width: 100%;
  padding: 15px;
  padding-left: 0;
  background: white;
  border-radius: 12px;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.08);
}

/* 📌 议程标题 */
.agenda-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 18px;
  font-weight: bold;
}

.agenda-title {
  font-size: 20px;
  font-weight: 700;
  color: #2878ff;
}

/* 📌 议程列表 - 横向滚动 */
.agenda-list {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  justify-content: space-between;
}

/* 📌 议程项 */
.agenda-item {
  flex: 1 1 calc(33.333% - 10px);
  min-width: 250px;
  max-width: 400px;
  padding: 15px;
  border-radius: 10px;
  background: #f8f9fa;
  transition: background 0.3s ease;
}

.agenda-item:hover {
  background: #eef5ff;
}

/* 📌 主内容区域 */
.main-content {
  display: flex;
  flex-direction: row;
  flex: 1;
  padding: 20px;
  margin-top: 10px; /* 确保议程区域有足够的空间 */
}

/* 📌 聊天区域 */
.chat-area {
  flex: 1.5;
  background: white;
  padding: 15px;
  border-radius: 10px;
  box-shadow: 0px 3px 8px rgba(0, 0, 0, 0.08);
  overflow-y: auto;
  min-height: 400px; /* 确保聊天窗口不会因为议程太长而变得太小 */
}

/* 📌 AI 实时总结面板 */
.realtime-summary {
  flex: 1.2;
  padding: 15px;
  background: #f9f9f9;
  border-radius: 10px;
  box-shadow: 0px 3px 8px rgba(0, 0, 0, 0.08);
  margin-left: 15px;
}
</style>
<style>
.el-card__body {
  padding-top: 0px !important;
}
</style>
