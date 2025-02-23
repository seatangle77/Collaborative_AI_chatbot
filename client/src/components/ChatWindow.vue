<template>
  <el-scrollbar ref="chatWindow" class="chat-window">
    <el-card v-for="msg in messages" :key="msg.id" class="chat-message">
      <strong>{{ getSenderName(msg) }}:</strong> {{ msg.message }}
    </el-card>
  </el-scrollbar>
</template>

<script setup>
import { ref, nextTick, watch } from "vue";

const props = defineProps({
  messages: Array,
  users: Object, // user_id -> name 映射
  aiBots: { type: Array, default: () => [] }, // ✅ 确保 `aiBots` 默认是空数组
  groupId: String, // ✅ 传入 `groupId`
});

// **获取消息发送者名称**
const getSenderName = (msg) => {
  if (msg.chatbot_id) {
    // ✅ 根据 `chatbot_id` 查找匹配的 AI 机器人名称
    const bot = props.aiBots.find((bot) => bot.id === msg.chatbot_id);
    return bot ? `🤖 ${bot.name}` : "🤖 AI 机器人"; // 默认机器人名称
  }
  // ✅ 查找用户
  return props.users?.[msg.user_id]
    ? `${props.users[msg.user_id]}`
    : "👤 未知用户"; // 默认用户名称
};

// **✅ 绑定 `el-scrollbar` 组件**
const chatWindow = ref(null);

// **✅ 使用 `setScrollTop()` 让 `el-scrollbar` 滚动**
const scrollToBottom = () => {
  nextTick(() => {
    if (chatWindow.value?.setScrollTop) {
      const wrapRef = chatWindow.value.wrapRef; // `el-scrollbar` 的内部滚动容器
      if (wrapRef) {
        chatWindow.value.setScrollTop(wrapRef.scrollHeight);
      }
    }
  });
};

// **✅ 监听 `messages` 变化，自动滚动到底部**
watch(
  () => props.messages.length,
  () => {
    scrollToBottom();
  },
  { deep: true }
);
</script>

<style scoped>
.chat-window {
  height: calc(100vh - 180px);
  background: #f4f4f4;
  padding: 10px;
  overflow-y: auto;
}

.chat-message {
  margin-bottom: 10px;
}
</style>
