<template>
  <div class="input-container">
    <el-input
      v-model="message"
      placeholder="输入消息..."
      @keyup.enter="handleSend"
    />
    <el-button type="primary" @click="handleSend">发送</el-button>
  </div>
</template>

<script setup>
import { ref } from "vue";

const message = ref("");
const emit = defineEmits(["send-message"]);

const handleSend = () => {
  if (message.value.trim()) {
    emit("send-message", message.value);
    message.value = "";
  }
};
</script>

<style scoped>
.input-container {
  display: flex;
  padding: 10px;
  background: #fff;
}

.el-input {
  flex: 1;
  margin-right: 10px;
}
</style>
