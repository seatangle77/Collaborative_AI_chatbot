<template>
  <el-header class="dashboard-header">
    <!-- 小组选择 -->
    <el-select
      v-model="localGroupId"
      class="group-select"
      @change="emit('selectGroup', localGroupId)"
    >
      <el-option
        v-for="group in groups"
        :key="group.id"
        :label="group.name"
        :value="group.id"
      />
    </el-select>

    <!-- 用户选择 -->
    <el-select
      v-model="localUserId"
      placeholder="选择用户"
      class="user-select"
      @change="emit('selectUser', localUserId)"
    >
      <el-option
        v-for="(user, userId) in filteredUsersInfo"
        :key="userId"
        :label="user.name"
        :value="userId"
      />
    </el-select>

    <!-- 更新按钮 -->
    <el-button
      type="success"
      @click="emit('updatePrompt')"
      :disabled="!localUserId"
    >
      Update PersonalAgent Prompt
    </el-button>

    <!-- 用户名 + Agent名 + Session名 -->
    <div class="header-title">
      <span v-if="localUserId && users[localUserId]">
        {{ users[localUserId].name }}
      </span>
      <span
        class="agent-name"
        @click="emit('toggleDrawer')"
        style="cursor: pointer"
      >
        🤖 {{ agentName }}
        <el-icon style="color: white; margin-left: 5px"><InfoFilled /></el-icon>
      </span>
      - {{ selectedSessionTitle || "No Active Session" }}
    </div>

    <!-- AI提供者选择器 -->
    <el-select
      v-model="agentModel"
      class="ai-provider-select"
      @change="handleProviderChange"
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
import { InfoFilled } from "@element-plus/icons-vue";
import { aiModelOptions } from "../utils/constants";
import api from "../services/apiService";
import { ElMessage } from "element-plus";

const props = defineProps({
  groups: Array,
  selectedGroupId: String,
  selectedUser: String,
  agentInfo: Object,
  users: Object,
  filteredUsersInfo: Object,
  selectedSessionTitle: String,
  agentName: String,
  selectedAiProvider: String,
});

const emit = defineEmits([
  "selectGroup",
  "selectUser",
  "updatePrompt",
  "changeAiProvider",
  "toggleDrawer",
]);

const localGroupId = ref(props.selectedGroupId);
const localUserId = ref(props.selectedUser);
const agentModel = ref(props.agentInfo?.model);

watch(
  () => props.selectedGroupId,
  (val) => (localGroupId.value = val)
);
watch(
  () => props.selectedUser,
  (val) => (localUserId.value = val)
);
watch(
  () => props.agentInfo?.model,
  (val) => (agentModel.value = val)
);

const updateModelInDatabase = async (model) => {
  console.log("props.agentInfo.id", props.agentInfo.id);
  if (!props.agentInfo?.id) return;
  try {
    await api.updateAgentModel(props.agentInfo.id, model);
    ElMessage.success("AI 模型已更新");
  } catch (error) {
    console.error("更新模型失败:", error);
    ElMessage.error("更新模型失败");
  }
};

const handleProviderChange = async (newModel) => {
  agentModel.value = newModel;
  await updateModelInDatabase(newModel);
};
</script>

<style scoped>
.dashboard-header {
  background: linear-gradient(135deg, #409eff, #2878ff);
  color: white;
  padding: 16px 20px;
  font-size: 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
.group-select,
.user-select,
.ai-provider-select {
  width: 150px;
  border-radius: 8px;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
}
.header-title {
  flex-grow: 1;
  text-align: center;
  font-size: 20px;
  font-weight: 600;
  text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.2);
}
.agent-name {
  color: #fff;
  font-weight: 500;
  margin-left: 5px;
  font-size: 16px;
}
</style>
