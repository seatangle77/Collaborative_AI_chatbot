<template>
  <el-card class="insights-panel">
    <div class="right-title">AI 讨论见解</div>

    <!-- 🔹 显示 "AI 处理中..." 状态 -->
    <p v-if="insights.length === 0" class="loading-text">🤖 AI 处理中...</p>

    <!-- 🔹 遍历 AI 见解 -->
    <div v-for="insight in insights" :key="insight.id">
      <p>{{ insight.insight_text }}</p>
    </div>
  </el-card>
</template>

<script setup>
import { ref, watch } from "vue";

const props = defineProps({
  insights: Array, // 由 WebSocket 动态更新
});

const insights = ref([...props.insights]); // ✅ 确保响应式
watch(
  () => props.insights.length,
  (newLen, oldLen) => {
    if (newLen > oldLen) {
      insights.value = [...props.insights]; // ✅ 只更新新数据，避免重置
    }
  }
);
</script>

<style scoped>
.insights-panel {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #fff;
  border-radius: 8px;
}

.right-title {
  font-weight: 600;
  padding-bottom: 15px;
  font-size: 18px;
  color: #409eff;
}

.loading-text {
  font-size: 14px;
  color: #aaa;
  text-align: center;
  padding: 10px 0;
}
</style>
