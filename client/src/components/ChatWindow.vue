<template>
  <el-scrollbar class="chat-window">
    <el-card v-for="msg in messages" :key="msg.id" class="chat-message">
      <strong>{{ getUsername(msg.user_id) }}:</strong> {{ msg.message }}
    </el-card>
  </el-scrollbar>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  messages: Array,
  users: Object, // user_id -> name 映射
});

// **获取用户名**
const getUsername = (userId) => {
  return props.users?.[userId] || "未知用户";
};
</script>

<style scoped>
.chat-window {
  height: calc(100vh - 180px);
  background: #f4f4f4;
  padding: 0; /* 确保内边距为0 */
  margin: 0; /* 确保外边距为0 */
}

.chat-message {
  margin-bottom: 10px;
}
</style>
