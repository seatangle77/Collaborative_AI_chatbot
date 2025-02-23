<template>
  <el-card class="agenda-adjust">
    <div class="right-title">调整后的议程</div>
    <div v-if="currentAgenda">
      <strong>{{ currentAgenda.agenda_title }}</strong>
      <p>{{ currentAgenda.agenda_description }}</p>
    </div>
    <div v-else>
      <p>暂无调整的议程</p>
    </div>
  </el-card>
</template>

<script setup>
const props = defineProps({
  currentAgenda: Object,
});
</script>

<style scoped>
.el-card__body {
  padding-top: 0px;
}
.agenda-adjust {
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

strong {
  font-weight: bold;
}

p {
  font-size: 14px;
  color: #333;
}
</style>
