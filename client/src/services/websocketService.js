const sockets = {}; // 存储多个 WebSocket 连接

export const createWebSocket = (groupId) => {
  if (sockets[groupId]) {
    console.log(`WebSocket for Group ${groupId} already exists.`);
    return;
  }

  const socket = new WebSocket(`ws://localhost:8000/ws/${groupId}`);
  sockets[groupId] = socket;

  socket.onopen = () => {
    console.log(`✅ WebSocket 连接成功: Group ${groupId}`);
  };

  socket.onmessage = (event) => {
    let receivedData = event.data;
  
    console.log("📩 WebSocket 收到原始数据:", receivedData);
  
    try {
      // 仅当 receivedData 是字符串时才 JSON.parse()
      if (typeof receivedData === "string") {
        receivedData = JSON.parse(receivedData);
      }
  
      console.log("✅ WebSocket 解析后数据:", receivedData);
  
      // **区分不同类型的 WebSocket 消息**
      switch (receivedData.type) {
        case "message":
          console.log("💬 新聊天消息:", receivedData.message);
          break;
        case "agenda":
          console.log("📋 议程更新:", receivedData.agenda);
          break;
        case "ai_analysis":
          console.log("🧠 AI 讨论分析:", receivedData.ai_analysis);
          break;
        case "ai_insight":
          console.log("🤖 AI 见解:", receivedData.insight_text);
          break;
        default:
          console.warn("⚠️ 未知类型的 WebSocket 消息:", receivedData);
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
    delete sockets[groupId]; // 连接关闭时删除存储的 WebSocket
  };

  socket.onerror = (error) => {
    console.error("❌ WebSocket 发生错误:", error);
  };
};

export const sendMessage = (groupId, message) => {
  if (sockets[groupId] && sockets[groupId].readyState === WebSocket.OPEN) {
    const payload = JSON.stringify({ message });
    sockets[groupId].send(payload);
    console.log("📤 发送消息:", payload);
  } else {
    console.error("⚠️ WebSocket 连接未打开，无法发送消息");
  }
};

let onMessageCallback = null;
export const onMessageReceived = (callback) => {
  onMessageCallback = callback;
};

export const closeWebSocket = (groupId) => {
  if (sockets[groupId]) {
    sockets[groupId].close();
    delete sockets[groupId];
  }
};