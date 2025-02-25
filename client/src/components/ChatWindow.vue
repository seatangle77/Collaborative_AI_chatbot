<template>
  <el-scrollbar ref="chatWindow" class="chat-window">
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
</template>

<script setup>
import { ref, nextTick, watch } from "vue";

const props = defineProps({
  messages: Array,
  users: Object,
  aiBots: { type: Array, default: () => [] },
  groupId: String,
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
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
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
</style>
