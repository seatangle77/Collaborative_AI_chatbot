<template>
  <el-menu
    class="sidebar"
    :default-active="activeGroupId"
    @select="selectGroup"
  >
    <!-- 小组列表 -->
    <el-menu-item v-for="group in groups" :key="group.id" :index="group.id">
      {{ group.name }}
    </el-menu-item>
  </el-menu>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";

// 小组数据
const groups = ref([]);
const activeGroupId = ref(null); // 当前选中小组

const emit = defineEmits(["select-group"]);

const selectGroup = (groupId) => {
  activeGroupId.value = groupId; // 设置高亮
  emit("select-group", groupId);
};

const fetchGroups = async () => {
  try {
    const response = await axios.get("http://localhost:8000/api/groups");
    groups.value = response.data;
    if (groups.value.length > 0) {
      activeGroupId.value = groups.value[0].id;
      emit("select-group", activeGroupId.value);
    }
  } catch (error) {
    console.error("获取群组失败:", error);
  }
};

onMounted(fetchGroups);
</script>

<style scoped>
.sidebar {
  background: #34495e;
  color: white;
  height: 100%;
  padding-top: 60px;
  padding-bottom: 100px;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}

.el-menu-item {
  color: white;
  font-size: 20px;
  font-weight: 600;
  padding: 15px 20px;
  border-radius: 8px;
  transition: background-color 0.3s;
}

.el-menu-item.is-active {
  background-color: #2980b9;
  color: white;
}

.el-menu-item:hover {
  background-color: #69b9ee;
}
</style>
