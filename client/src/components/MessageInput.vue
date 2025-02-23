<template>
  <div class="input-container">
    <!-- 用户选择下拉框 -->
    <el-select
      v-model="selectedUser"
      placeholder="选择用户"
      class="user-select"
      size="default"
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
      placeholder="输入消息..."
      @keyup.enter="handleSend"
      class="message-input"
      size="default"
    />
    <!-- 发送按钮 -->
    <el-button type="primary" @click="handleSend" size="default"
      >发送</el-button
    >
  </div>
</template>

<script setup>
import { ref, watch } from "vue";

const props = defineProps({
  users: {
    type: Object,
    default: () => ({}), // ✅ 确保 users 有默认值，避免 Vue 警告
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
.input-container {
  display: flex;
  align-items: center;
  padding: 10px;
  background: #fff;
  justify-content: space-between;
}

.user-select {
  width: 120px;
  margin-right: 10px;
}

.message-input {
  flex: 1;
  margin-right: 10px;
}

.el-button {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
