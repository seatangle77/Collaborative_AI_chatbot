<template>
  <el-card class="terminology-helper">
    <h3>术语助手</h3>
    <p v-if="term">{{ term.definition }}</p>
    <p v-else>点击讨论中的术语查看解释</p>
  </el-card>
</template>
<script setup>
import { ref } from "vue";
import apiService from "@/services/apiService";
const term = ref(null);
const fetchTerm = async (word) => {
  term.value = await apiService.getTerm(word);
};
</script>
