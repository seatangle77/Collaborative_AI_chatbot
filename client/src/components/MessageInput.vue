<template>
  <div class="input-container">
    <!-- 用户选择下拉框 -->
    <el-select
      v-model="selectedUser"
      placeholder="选择用户"
      class="user-select"
      size="large"
    >
      <el-option
        v-for="(name, userId) in users"
        :key="userId"
        :label="name"
        :value="userId"
      />
    </el-select>

    <!-- 消息输入框 -->
    <el-input
      v-model="message"
      placeholder=" Please input your message..."
      @keyup.enter="handleSend"
      class="message-input"
      size="large"
    />

    <!-- 发送按钮 -->
    <el-button type="primary" @click="handleSend" size="large" class="send-btn">
      Send
    </el-button>
  </div>
</template>

<script setup>
import { ref, watch } from "vue";

const props = defineProps({
  users: {
    type: Object,
    default: () => ({}),
  },
  groupId: String,
});

const message = ref("");
const selectedUser = ref(null);

watch(
  () => props.users,
  (newUsers) => {
    if (newUsers && Object.keys(newUsers).length > 0) {
      selectedUser.value = Object.keys(newUsers)[0] || null;
    }
  },
  { immediate: true }
);

const emit = defineEmits(["send-message"]);

const handleSend = () => {
  if (message.value.trim() && selectedUser.value) {
    emit("send-message", {
      group_id: props.groupId,
      user_id: selectedUser.value,
      message: message.value,
    });
    message.value = "";
  }
};
</script>

<style scoped>
/* 🔹 输入框容器 */
.input-container {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: #fff;
  border-top: 1px solid #e0e0e0;
  box-shadow: 0 -2px 6px rgba(0, 0, 0, 0.05);
  border-radius: 0 0 12px 12px;
}

/* 🔹 用户选择框 */
.user-select {
  width: 140px;
  margin-right: 12px;
}

/* 🔹 消息输入框 */
.message-input {
  flex: 1;
  border-radius: 8px;
  transition: all 0.3s ease-in-out;
}

.message-input:focus-within {
  box-shadow: 0 0 6px rgba(64, 158, 255, 0.6);
}

/* 🔹 发送按钮 */
.send-btn {
  padding: 10px 20px;
  font-size: 16px;
  font-weight: bold;
  border-radius: 8px;
  background: linear-gradient(to right, #409eff, #187bcd);
  transition: all 0.3s ease-in-out;
  margin-left: 12px;
}

.send-btn:hover {
  background: linear-gradient(to right, #5aafff, #1b89e5);
}
</style>
