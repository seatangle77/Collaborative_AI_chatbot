<template>
  <el-container class="chat-container">
    <!-- 侧边栏：小组选择 -->
    <el-aside width="250px">
      <Sidebar @select-group="selectGroup" />
    </el-aside>

    <!-- 主要内容 -->
    <el-container>
      <!-- 头部 -->
      <el-header class="chat-header">
        <div>聊天室 - 当前小组: {{ selectedGroupName }}</div>
      </el-header>

      <!-- 主体内容 -->
      <el-container class="main-content">
        <!-- 聊天窗口 -->
        <el-main class="chat-window">
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

        <!-- 右侧功能区域 -->
        <el-aside width="500px" class="chat-sidebar">
          <AgendaDisplay :agendas="chatAgendas" />
          <InsightsPanel :insights="discussionInsights" />
          <AgendaAdjust :currentAgenda="chatAgendas[0]" />
        </el-aside>
      </el-container>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from "vue";
import axios from "axios";
import Sidebar from "../components/Sidebar.vue";
import ChatWindow from "../components/ChatWindow.vue";
import MessageInput from "../components/MessageInput.vue";
import AgendaDisplay from "../components/AgendaDisplay.vue";
import InsightsPanel from "../components/InsightsPanel.vue";
import AgendaAdjust from "../public_device/AgendaAdjust.vue";
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

// ✅ 在页面加载时获取所有 AI 机器人
const fetchAllAiBots = async () => {
  try {
    const response = await axios.get("http://localhost:8000/api/ai_bots");
    aiBots.value = response.data; // ✅ 存储所有机器人数据
    console.log("AIbot", aiBots);
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

// ✅ **获取议程**
const fetchChatAgendas = async (groupId) => {
  if (!groupId) return;
  try {
    const response = await axios.get(
      `http://localhost:8000/api/chat/agenda/${groupId}`
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
  await fetchChatAgendas(groupId);
  await fetchDiscussionInsights(groupId);
  initWebSocket(groupId);
};

// ✅ **监听小组变化，自动更新数据**
watch(selectedGroupId, async (newGroupId) => {
  if (newGroupId) {
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

.message-input {
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

.chat-window {
  padding: 20px;
  background-color: #fff;
  flex: 1;
  overflow-y: auto;
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

.el-menu-item {
  color: white;
  font-size: 16px;
}

.el-menu-item:hover {
  background-color: #2980b9;
}
</style>
