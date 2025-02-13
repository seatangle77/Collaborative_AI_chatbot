import { createRouter, createWebHistory } from "vue-router";
import ChatView from "../views/ChatView.vue"; // 确保 `views/ChatView.vue` 存在

const routes = [
  {
    path: "/",
    name: "Chat",
    component: ChatView,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;