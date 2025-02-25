<template>
  <el-card class="agenda-display">
    <!-- 📌 议程标题 -->
    <div class="agenda-header">
      <span class="agenda-title">📌 Current Agenda</span>
      <el-tag type="info" class="agenda-count"
        >{{ agendas.length }} items</el-tag
      >
    </div>

    <!-- 📌 议程列表 -->
    <div class="agenda-list">
      <div
        v-for="agenda in agendas"
        :key="agenda.id"
        class="agenda-item"
        :class="getStatusClass(agenda.status)"
      >
        <div class="agenda-main">
          <div class="agenda-content">
            <span class="agenda-topic">{{ agenda.agenda_title }}</span>
          </div>

          <!-- 🔹 状态 Emoji -->
          <div class="status-indicator" @click="toggleAgendaStatus(agenda)">
            {{ getStatusEmoji(agenda.status) }}
          </div>
        </div>

        <!-- 🔹 议程详情 -->
        <p class="agenda-description">{{ agenda.agenda_description }}</p>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, watch } from "vue";

const props = defineProps({
  agendas: Array,
});

// ✅ **切换议程状态**
const toggleAgendaStatus = (agenda) => {
  if (agenda.status === "not_started") {
    agenda.status = "in_progress"; // ⚡ 第一次点击 -> 进行中
  } else if (agenda.status === "in_progress") {
    agenda.status = "completed"; // ✅ 第二次点击 -> 已完成
  } else {
    agenda.status = "not_started"; // 🔄 第三次点击 -> 未开始
  }

  console.log(
    `📌 Agenda "${agenda.agenda_title}" updated to: ${getStatusLabel(
      agenda.status
    )}`
  );
};

// ✅ **状态映射**
const getStatusLabel = (status) => {
  const statusMap = {
    not_started: "Not Started",
    in_progress: "In Progress",
    completed: "Completed",
  };
  return statusMap[status] || "Unknown";
};

// ✅ **状态 Emoji**
const getStatusEmoji = (status) => {
  const emojiMap = {
    not_started: "⏳",
    in_progress: "🚀",
    completed: "✅",
  };
  return emojiMap[status] || "❓";
};

// ✅ **状态样式**
const getStatusClass = (status) => {
  return {
    "agenda-not-started": status === "not_started",
    "agenda-in-progress": status === "in_progress",
    "agenda-completed": status === "completed",
  };
};
</script>

<style scoped>
/* 🔹 议程整体 */
.agenda-display {
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

/* 🔹 标题栏 */
.agenda-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 20px;
}

.agenda-title {
  font-size: 20px;
  font-weight: 700;
  color: #2878ff;
}

/* 🔹 议程列表 */
.agenda-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
  flex: 1;
}

/* 🔹 议程项 - 不同状态的颜色 */
.agenda-item {
  border-radius: 12px;
  padding: 15px;
  transition: background 0.3s ease;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 🟡 未开始 (Not Started) */
.agenda-not-started {
  background: linear-gradient(135deg, #fff7e1, #ffebcc);
  border-left: 5px solid #ff9800;
}

/* 🔵 进行中 (In Progress) */
.agenda-in-progress {
  background: linear-gradient(135deg, #e1f2ff, #cce7ff);
  border-left: 5px solid #007bff;
}

/* 🟢 已完成 (Completed) */
.agenda-completed {
  background: linear-gradient(135deg, #e1ffe1, #ccffcc);
  border-left: 5px solid #00a000;
}

/* 🔹 议程主行 */
.agenda-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 🔹 议程标题 */
.agenda-content {
  display: flex;
  flex-direction: column;
}

.agenda-topic {
  font-size: 16px;
  font-weight: 700;
  color: #333;
}

/* 🔹 议程详情 */
.agenda-description {
  font-size: 14px;
  color: #555;
  line-height: 1.5;
}

/* 🔹 状态指示器 */
.status-indicator {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  font-size: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 3px 5px rgba(0, 0, 0, 0.1);
  background: white;
}

.status-indicator:hover {
  transform: scale(1.1);
  opacity: 0.8;
}
</style>
