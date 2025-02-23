<template>
  <el-card class="agenda-display">
    <div class="right-title">当前议程</div>
    <div v-for="agenda in agendas" :key="agenda.id">
      <strong>{{ agenda.agenda_title }}</strong>
      <p>{{ agenda.agenda_description }}</p>
    </div>
  </el-card>
</template>

<script setup>
const props = defineProps({
  agendas: Array,
});
</script>

<style scoped>
.el-card__body {
  padding-top: 0px;
}
.agenda-display {
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
