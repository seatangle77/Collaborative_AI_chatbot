<template>
  <el-header class="chat-header">
    <!-- 小组选择器 -->
    <el-select
      v-model="localSelectedGroupId"
      class="group-select"
      popper-class="custom-dropdown"
      @change="emit('selectGroup', localSelectedGroupId)"
    >
      <el-option
        v-for="group in groups"
        :key="group.id"
        :label="group.name"
        :value="group.id"
      />
    </el-select>

    <el-button
      type="success"
      @click="emit('updatePrompt')"
      :disabled="!localSelectedGroupId"
    >
      Update GroupBot Prompt
    </el-button>

    <!-- 会话标题 -->
    <div class="header-title">
      {{ selectedSessionTitle || "No Active Session" }}
    </div>

    <el-button link @click="emit('toggleDrawer')">
      <span v-if="selectedGroupBot" class="bot-name">
        🤖 {{ selectedGroupBot.name }}
      </span>
      <el-icon style="color: white; margin-left: 5px"><InfoFilled /></el-icon>
    </el-button>

    <!-- AI供应商选择 -->
    <el-select
      v-model="localSelectedAiProvider"
      class="ai-provider-select"
      popper-class="custom-dropdown"
      @change="handleModelChange"
    >
      <el-option
        v-for="(label, value) in aiModelOptions"
        :key="value"
        :label="label"
        :value="value"
      />
    </el-select>
  </el-header>
</template>

<script setup>
import { ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { InfoFilled } from "@element-plus/icons-vue";
import { aiModelOptions } from "../utils/constants";
import api from "../services/apiService";

const props = defineProps({
  groups: Array,
  selectedGroupId: String,
  selectedAiProvider: String,
  selectedGroupBot: Object,
  selectedSessionTitle: String,
});

const emit = defineEmits([
  "selectGroup",
  "changeAiProvider",
  "updatePrompt",
  "toggleDrawer",
]);

const localSelectedGroupId = ref(props.selectedGroupId);
const localSelectedAiProvider = ref(props.selectedAiProvider);

const handleModelChange = async (newModel) => {
  if (props.selectedGroupBot?.id) {
    try {
      await api.updateBotModel(props.selectedGroupBot.id, newModel);
      ElMessage.success("AI 模型已更新！");
    } catch (error) {
      console.error("更新 AI 模型失败:", error);
    }
  }
  emit("changeAiProvider", newModel);
};

watch(
  () => props.selectedGroupId,
  (val) => {
    localSelectedGroupId.value = val;
  }
);
watch(
  () => props.selectedAiProvider,
  (val) => {
    localSelectedAiProvider.value = val;
  }
);
watch(
  () => props.selectedGroupBot,
  (newBot) => {
    if (newBot?.model) {
      localSelectedAiProvider.value = newBot.model;
      emit("changeAiProvider", newBot.model);
    }
  },
  { immediate: true }
);
</script>

<style scoped>
.chat-header {
  background: linear-gradient(135deg, #409eff, #2878ff);
  color: white;
  padding: 16px 20px;
  font-size: 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
.group-select {
  width: 220px;
  border-radius: 8px;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
}
.ai-provider-select {
  width: 150px;
  border-radius: 8px;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
}
.custom-dropdown {
  border-radius: 10px;
  box-shadow: 0px 6px 12px rgba(0, 0, 0, 0.15);
}
.header-title {
  flex-grow: 1;
  text-align: center;
  font-size: 22px;
  font-weight: 600;
  text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.2);
}
.bot-name {
  color: #fff;
  font-weight: 500;
  margin-left: 5px;
  font-size: 16px;
}
</style>
