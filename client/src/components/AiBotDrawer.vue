<template>
  <el-drawer
    :model-value="visible"
    @update:model-value="(val) => emit('update:visible', val)"
    title="🤖 AI Bot Details"
    size="40%"
    direction="ltr"
    :with-header="true"
  >
    <div v-if="bot">
      <h3>{{ bot.name }}</h3>
      <p style="margin-bottom: 10px">
        {{ bot.description || "No description available." }}
      </p>

      <el-divider>🧭 Cognitive Guidance Prompt</el-divider>
      <el-scrollbar class="prompt-box">{{
        bot.cognitive_guidance_systemprompt
      }}</el-scrollbar>

      <el-divider>📄 Real-Time Summary Prompt</el-divider>
      <el-scrollbar class="prompt-box">{{
        bot.real_time_summary_systemprompt
      }}</el-scrollbar>

      <el-divider>📚 Summary to Knowledge Prompt</el-divider>
      <el-scrollbar class="prompt-box">{{
        bot.summary_to_knowledge_systemprompt
      }}</el-scrollbar>
    </div>
    <div v-else>
      <el-empty description="No bot info found." />
    </div>
  </el-drawer>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  groupId: String,
  visible: Boolean,
  aiBots: Array,
});

const emit = defineEmits(["update:visible"]);

const bot = computed(() => {
  return props.aiBots.find((b) => b.group_id === props.groupId);
});
</script>

<style scoped>
.prompt-box {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 8px;
  font-size: 14px;
  white-space: pre-wrap;
  max-height: 200px;
  margin-bottom: 16px;
}
</style>
