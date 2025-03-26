<template>
  <el-scrollbar
    ref="chatWindow"
    class="chat-window"
    @mouseup="handleTextSelection"
  >
    <div class="chat-list">
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="chat-message"
        :class="{ 'ai-message': msg.chatbot_id }"
      >
        <span class="sender">{{ getSenderName(msg) }}:</span>
        <span class="message-content">{{ msg.message }}</span>
        <span class="timestamp">{{ formatTimestamp(msg.created_at) }}</span>
      </div>
    </div>
  </el-scrollbar>

  <!-- 🔍 查询按钮（悬浮在选中文本附近） -->
  <el-button
    v-if="showQueryButton"
    class="query-btn"
    @click="querySelectedText"
    :style="{ top: buttonPosition.y + 'px', left: buttonPosition.x + 'px' }"
  >
    🔍 查询
  </el-button>

  <!-- 📌 查询结果浮窗 -->
  <el-dialog v-model="showQueryDialog" title="查询结果" width="50%">
    <div v-if="parsedQueryResult">
      <h3>📖 术语定义</h3>
      <p>{{ parsedQueryResult.definition }}</p>

      <h3 v-if="parsedQueryResult.cross_discipline_insights.length > 0">
        🔍 跨学科洞见
      </h3>
      <ul v-if="parsedQueryResult.cross_discipline_insights.length > 0">
        <li
          v-for="(
            insight, index
          ) in parsedQueryResult.cross_discipline_insights"
          :key="'insight-' + index"
        >
          {{ insight }}
        </li>
      </ul>

      <h3 v-if="parsedQueryResult.application_examples.length > 0">
        💡 应用示例
      </h3>
      <ul v-if="parsedQueryResult.application_examples.length > 0">
        <li
          v-for="(example, index) in parsedQueryResult.application_examples"
          :key="'example-' + index"
        >
          {{ example }}
        </li>
      </ul>
    </div>
    <p v-else>正在查询...</p>
  </el-dialog>
</template>

<script setup>
import { ref, nextTick, watch, computed } from "vue";
import axios from "axios";

const props = defineProps({
  messages: Array,
  users: Object,
  aiBots: { type: Array, default: () => [] },
  groupId: String,
  sessionId: String, // ✅ 新增 sessionId
  userId: String, // ✅ 新增 userId
  aiProvider: String, // ✅ 新增 aiProvider
});

// ✅ 选中的文本
const selectedText = ref("");
const showQueryButton = ref(false);
const buttonPosition = ref({ x: 0, y: 0 });
const showQueryDialog = ref(false);
const queryResult = ref("");

// ✅ 解析 `queryResult` 并转换成易读的格式
const parsedQueryResult = computed(() => {
  if (!queryResult.value || queryResult.value.trim() === "") {
    return null; // ✅ 避免解析空字符串
  }
  try {
    const data = JSON.parse(queryResult.value);
    if (!data || !data.term_explanation) return null;
    return {
      definition: data.term_explanation.definition || "暂无定义。",
      cross_discipline_insights:
        data.term_explanation.cross_discipline_insights || [],
      application_examples: data.term_explanation.application_examples || [],
    };
  } catch (error) {
    console.error("解析查询结果失败:", error);
    return null; // ✅ 解析失败时返回 null，避免页面崩溃
  }
});

// ✅ 获取消息发送者名称
const getSenderName = (msg) => {
  if (msg.chatbot_id) {
    const bot = props.aiBots.find((bot) => bot.id === msg.chatbot_id);
    return bot ? `🤖 ${bot.name}` : "🤖 AI 机器人";
  }
  return props.users?.[msg.user_id]
    ? `${props.users[msg.user_id]}`
    : "👤 未知用户";
};

// ✅ 格式化时间
const formatTimestamp = (timestamp) => {
  if (!timestamp) return "";
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
};

// ✅ 绑定滚动条
const chatWindow = ref(null);

// ✅ 自动滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (chatWindow.value?.setScrollTop) {
      const wrapRef = chatWindow.value.wrapRef;
      if (wrapRef) {
        chatWindow.value.setScrollTop(wrapRef.scrollHeight);
      }
    }
  });
};

// ✅ 监听消息变化
watch(
  () => props.messages.length,
  () => {
    scrollToBottom();
  },
  { deep: true }
);

// ✅ 监听文本选择
const handleTextSelection = (event) => {
  const selection = window.getSelection().toString().trim();

  if (selection) {
    selectedText.value = selection;
    showQueryButton.value = true;

    // 📌 设置查询按钮位置
    buttonPosition.value = {
      x: event.pageX + 10,
      y: event.pageY - 30,
    };
  } else {
    showQueryButton.value = false;
  }
};

const querySelectedText = async () => {
  if (
    !selectedText.value ||
    !props.groupId ||
    !props.userId ||
    !props.sessionId
  )
    return;

  showQueryDialog.value = true;
  queryResult.value = ""; // 清空旧数据

  try {
    const response = await axios.post(
      "http://localhost:8000/api/discussion_insights",
      {
        group_id: props.groupId,
        session_id: props.sessionId,
        user_id: props.userId,
        message_text: selectedText.value,
        ai_provider: props.aiProvider || "xai", // 默认使用 xAI
      }
    );

    queryResult.value = response.data.insight_text; // 获取 AI 解释的术语
  } catch (error) {
    queryResult.value = "查询失败，请稍后重试。";
    console.error("查询失败:", error);
  }

  showQueryButton.value = false; // 关闭查询按钮
};
</script>

<style scoped>
/* 🔹 Chat Window 样式 */
.chat-window {
  height: calc(100vh - 200px);
  background: #f9f9f9;
  padding: 10px 15px;
  overflow-y: auto;
  border-radius: 12px;
  border: 1px solid #ddd;
}

/* 🔹 消息列表 */
.chat-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

/* 🔹 单条消息 */
.chat-message {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 14px;
  color: #333;
  padding: 6px 12px;
  border-radius: 8px;
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease-in-out;
}

/* 🔹 AI 机器人消息（突出显示） */
.ai-message {
  background: #e3f2fd; /* 轻柔蓝色背景 */
  border-left: 4px solid #409eff; /* 左侧强调色 */
}

/* 🔹 发送者名字 */
.sender {
  font-weight: bold;
  color: #409eff;
}

/* 🔹 AI 机器人名字（更亮眼） */
.ai-message .sender {
  color: #1565c0; /* 深蓝色 */
}

/* 🔹 消息内容 */
.message-content {
  flex: 1;
  word-break: break-word;
}

/* 🔹 时间戳 */
.timestamp {
  font-size: 12px;
  color: #aaa;
}
/* 🔍 查询按钮 */
.query-btn {
  position: absolute;
  background: #409eff;
  color: white;
  padding: 6px 12px;
  font-size: 14px;
  border-radius: 6px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  transition: all 0.2s ease-in-out;
}

.query-btn:hover {
  background: #55a2ef;
}
</style>
