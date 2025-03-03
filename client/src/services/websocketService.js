const sockets = {}; // 存储多个 WebSocket 连接
let messageCounter = {}; // 记录每个 group 的消息计数

export const createWebSocket = (groupId) => {
  if (sockets[groupId]) {
    console.log(`⚡ WebSocket for Group ${groupId} already exists.`);
    return;
  }

  const socket = new WebSocket(`ws://localhost:8000/ws/${groupId}`);
  sockets[groupId] = socket;
  messageCounter[groupId] = 0; // ✅ 初始化计数

  socket.onopen = () => {
    console.log(`✅ WebSocket 连接成功: Group ${groupId}`);
  };

  socket.onmessage = (event) => {
    let receivedData = event.data;

    console.log("📩 WebSocket 收到原始数据:", receivedData);

    try {
      // 解析 JSON 数据
      if (typeof receivedData === "string") {
        receivedData = JSON.parse(receivedData);
      }

      console.log("✅ 解析后数据:", receivedData);

      // **区分不同类型的 WebSocket 消息**
      switch (receivedData.type) {
        case "message":
          console.log("💬 新聊天消息:", receivedData.message);
          messageCounter[groupId] += 1; // ✅ 计数 +1
          break;
        case "ai_summary":
          console.log("🤖 AI 会议总结:", receivedData.summary_text);
          messageCounter[groupId] = 0; // ✅ AI 触发后重置计数
          break;
        default:
          console.warn("⚠️ 未知类型的 WebSocket 消息:", receivedData);
      }

      // **每 3 条消息后触发 AI 总结**
      if (messageCounter[groupId] >= 3) {
        console.log(`🚀 触发 AI 会议总结: Group ${groupId}`);
        sendMessage(groupId, { type: "trigger_ai_summary" });
        messageCounter[groupId] = 0; // ✅ 重置计数
      }

      // **通知 Vue 组件更新 UI**
      if (onMessageCallback) {
        onMessageCallback(receivedData);
      }
    } catch (error) {
      console.error("❌ WebSocket 消息解析失败:", error, "原始数据:", event.data);
    }
  };

  socket.onclose = () => {
    console.log(`⚠️ WebSocket 连接关闭: Group ${groupId}`);
    delete sockets[groupId];
    delete messageCounter[groupId];
  };

  socket.onerror = (error) => {
    console.error("❌ WebSocket 发生错误:", error);
  };
};

export const changeAiProviderAndTriggerSummary = (groupId, aiProvider) => {
  if (!groupId || !aiProvider) {
    console.error("⚠️ groupId 或 aiProvider 为空，无法触发 AI 会议总结");
    return;
  }

  if (!sockets[groupId] || sockets[groupId].readyState !== WebSocket.OPEN) {
    console.error("⚠️ WebSocket 连接未打开，无法触发 AI 会议总结");
    return;
  }

  const payload = JSON.stringify({
    type: "trigger_ai_summary",
    aiProvider, // ✅ 传递用户选择的 AI 供应商
  });

  console.log("📤 发送 AI 会议总结请求:", payload);
  sockets[groupId].send(payload);
};

// ✅ **发送消息**
export const sendMessage = (groupId, message) => {
  if (sockets[groupId] && sockets[groupId].readyState === WebSocket.OPEN) {
    const payload = JSON.stringify(message);
    sockets[groupId].send(payload);
    console.log("📤 发送消息:", payload);
  } else {
    console.error("⚠️ WebSocket 连接未打开，无法发送消息");
  }
};

let onMessageCallback = null;

// ✅ **WebSocket 监听消息回调**
export const onMessageReceived = (callback) => {
  onMessageCallback = callback;
};

// ✅ **关闭 WebSocket**
export const closeWebSocket = (groupId) => {
  if (sockets[groupId]) {
    sockets[groupId].close();
    delete sockets[groupId];
    delete messageCounter[groupId];
  }
};