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
    </el-header>

    <!-- 📌 主体 -->
    <el-container class="main-content">
      <!-- 📌 左侧议程 -->
      <el-aside class="agenda-panel">
        <AgendaDisplay :agendas="chatAgendas" />
      </el-aside>

      <!-- ✅ 聊天窗口 & AI 见解 -->
      <el-main class="chat-area">
        <ChatWindow
          :messages="messages"
          :users="users"
          :aiBots="aiBots"
          :groupId="selectedGroupId"
        />
        <MessageInput
          :users="filteredUsers"
          :groupId="selectedGroupId"
          @send-message="sendMessage"
        />
      </el-main>

      <!-- ✅ AI 讨论见解 -->
      <el-aside class="insights-panel">
        <InsightsPanel :insights="discussionInsights" />
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
import InsightsPanel from "../components/InsightsPanel.vue";
import {
  createWebSocket,
  sendMessage as sendWebSocketMessage,
  onMessageReceived,
  closeWebSocket,
} from "../services/websocketService";

// ✅ **存储状态**
const messages = ref([]);
const users = ref({});
const chatAgendas = ref([]);
const discussionInsights = ref([]);
const selectedGroupName = ref("");
const selectedGroupId = ref(null);
const selectedSessionId = ref(null); // ✅ 存储当前 Session ID
const selectedSessionTitle = ref("");
const groupMembers = ref([]);
const groups = ref([]);
const aiBots = ref([]); // ✅ 避免 undefined 访问错误

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

// ✅ **获取讨论见解**
const fetchDiscussionInsights = async (groupId) => {
  if (!groupId) return;
  try {
    const response = await axios.get(
      `http://localhost:8000/api/discussion/insights/${groupId}`
    );
    discussionInsights.value = response.data;
  } catch (error) {
    console.error("获取讨论见解失败:", error);
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

// ✅ **发送消息**
const sendMessage = async (payload) => {
  try {
    const response = await axios.post("http://localhost:8000/api/chat/send", {
      group_id: payload.group_id,
      user_id: payload.user_id,
      message: payload.message,
      role: "user",
    });

    console.log("📤 发送消息到数据库:", response.data);

    // ❌ **不需要再手动推送 WebSocket，数据库插入后 WebSocket 会自动触发**
    // sendWebSocketMessage(payload.group_id, response.data);
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
        parsedData = data; // 直接使用对象
      }

      console.log("✅ 解析后数据:", parsedData);

      // 🔹 统一处理 WebSocket 消息类型
      if (parsedData.message) {
        let newMessage = parsedData.message;

        if (Array.isArray(newMessage)) {
          newMessage = newMessage[0]; // 只取数组的第一条消息
        }

        messages.value.push(newMessage);
        scrollToBottom();
      }
      if (parsedData.agenda) {
        chatAgendas.value = parsedData.agenda;
      }
      if (parsedData.ai_analysis) {
        discussionInsights.value = parsedData.ai_analysis;
      }

      // ✅ **处理 AI 见解**
      if (parsedData.type === "ai_insight") {
        console.log("🤖 AI 见解收到:", parsedData.insight_text);
        discussionInsights.value.push({
          insight_text: parsedData.insight_text,
        });
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
  await fetchDiscussionInsights(groupId);
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
.agenda-display {
  width: 96%;
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
  flex: 2.5;
  background: white;
  padding: 15px;
  border-radius: 10px;
  box-shadow: 0px 3px 8px rgba(0, 0, 0, 0.08);
  overflow-y: auto;
  min-height: 400px; /* 确保聊天窗口不会因为议程太长而变得太小 */
}

/* 📌 AI 见解面板 */
.insights-panel {
  flex: 1;
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
