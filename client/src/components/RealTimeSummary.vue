<template>
  <el-card class="summary-panel">
    <div class="summary-header">
      <span class="summary-title">✨ AI Real-Time Summary</span>
      <el-tag type="info" class="summary-status" v-if="!parsedSummary"
        >Processing...</el-tag
      >
    </div>

    <!-- 🔹 AI 处理中 -->
    <p v-if="!parsedSummary" class="loading-text">
      AI is analyzing the discussion...
    </p>

    <!-- 🔹 展示最新 AI 总结 -->
    <div v-if="parsedSummary">
      <p><strong>🔹 Topic: </strong> {{ parsedSummary.current_topic }}</p>
      <p><strong>📌 Key Points:</strong></p>
      <ul class="summary-list">
        <li
          v-for="(point, index) in parsedSummary.key_points.split('。')"
          :key="'point-' + index"
        >
          {{ point }}
        </li>
      </ul>
      <p v-if="parsedSummary.unresolved_issues">
        <strong>❓ Unresolved Issues: </strong>
        {{ parsedSummary.unresolved_issues }}
      </p>
    </div>
  </el-card>
</template>

<script setup>
import { ref, watch, onMounted } from "vue";
import axios from "axios";

const props = defineProps({
  discussion_summary: Array, // 通过 REST API 和 WebSocket 获取
  groupId: String, // ✅ 从 ChatView.vue 传入 groupId
});

const parsedSummary = ref(null);

// ✅ **解析 AI 会议总结**
const parseAiSummary = (insightText) => {
  if (!insightText) return;
  try {
    const jsonTextMatch = insightText.match(/```json\n([\s\S]*?)\n```/);
    if (jsonTextMatch) {
      parsedSummary.value = JSON.parse(jsonTextMatch[1]).summary;
    } else {
      console.warn("⚠️ AI response format incorrect:", insightText);
    }
  } catch (error) {
    console.error("❌ Failed to parse AI JSON response:", error);
  }
};

// ✅ **RESTful API 获取最新 AI Summary**
const fetchLatestSummary = async (groupId) => {
  if (!groupId) return;
  try {
    const response = await axios.get(
      `http://localhost:8000/api/chat_summaries/${groupId}`
    );
    if (response.data.length > 0) {
      parseAiSummary(response.data[0].summary_text);
    }
  } catch (error) {
    console.error("❌ Failed to fetch AI summary:", error);
  }
};

watch(
  () => props.discussion_summary,
  (newSummary) => {
    if (!newSummary || newSummary.length === 0) {
      console.warn("⚠️ No AI summary data available.");
      parsedSummary.value = null;
      return;
    }

    try {
      let latestSummary = null;

      // ✅ 处理数据库返回的数据：newSummary[newSummary.length - 1][0]
      if (Array.isArray(newSummary[newSummary.length - 1])) {
        latestSummary = newSummary[newSummary.length - 1][0];
      } else {
        // ✅ 处理 WebSocket 返回的数据：newSummary[newSummary.length - 1]
        latestSummary = newSummary[newSummary.length - 1];
      }

      // ✅ 检查 latestSummary 是否存在
      if (
        !latestSummary ||
        !latestSummary.summary_text ||
        typeof latestSummary.summary_text !== "string"
      ) {
        console.warn(
          "⚠️ summary_text is empty or not a string:",
          latestSummary
        );
        parsedSummary.value = null;
        return;
      }

      // ✅ 解析 JSON 格式的 AI 总结
      const jsonText = latestSummary.summary_text.match(
        /```json\n([\s\S]*?)\n```/
      );

      if (!jsonText) {
        console.warn(
          "⚠️ AI response format is incorrect:",
          latestSummary.summary_text
        );
        parsedSummary.value = null;
        return;
      }

      // ✅ 解析 JSON 并存入 parsedSummary
      parsedSummary.value = JSON.parse(jsonText[1]).summary;
    } catch (error) {
      console.error("❌ Failed to parse AI JSON response:", error);
      parsedSummary.value = null;
    }
  },
  { deep: true, immediate: true }
);

// ✅ **组件初始化时加载最新 AI Summary**
onMounted(() => {
  fetchLatestSummary(props.groupId);
});
</script>

<style scoped>
/* 🔹 主体容器 */
.summary-panel {
  width: 100%;
  height: 100%;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.08);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

/* 🔹 头部 */
.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 20px;
}

.summary-title {
  font-size: 20px;
  font-weight: 700;
  color: #2878ff;
}

/* 🔹 AI 处理中 */
.loading-text {
  font-size: 14px;
  color: #aaa;
  text-align: center;
  padding: 10px 0;
}

/* 🔹 AI 总结列表 */
.summary-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-left: 20px;
}

.summary-list li {
  list-style-type: disc;
  font-size: 14px;
  color: #333;
  line-height: 1.6;
}
</style>
