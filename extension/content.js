// LinkedIn メッセージを監視して CordLink に送信
let processedMessages = new Set();
const CORDLINK_URL = 'http://localhost:8002/webhook/linkedin';

// メッセージを監視
function checkForNewMessages() {
  const conversations = document.querySelectorAll('[data-test-id="conversation-item"]');
  
  conversations.forEach(conv => {
    try {
      const nameElement = conv.querySelector('[data-test-id="conversation-item-name"]');
      const messageElement = conv.querySelector('[data-test-id="conversation-item-message"]');
      
      if (!nameElement || !messageElement) return;
      
      const senderName = nameElement.textContent.trim();
      const messageText = messageElement.textContent.trim();
      const messageId = `${senderName}_${messageText.substring(0, 20)}`;
      
      // 既に処理済みならスキップ
      if (processedMessages.has(messageId)) return;
      
      // 未読メッセージのみ処理
      const isUnread = conv.querySelector('[data-test-id="unread-indicator"]');
      if (!isUnread) return;
      
      // CordLink に送信
      sendToCordLink({
        sender_name: senderName,
        sender_role: 'LinkedIn User',
        message: messageText,
        sender_id: senderName.replace(/\s+/g, '_')
      });
      
      processedMessages.add(messageId);
      console.log('✅ Message sent to CordLink:', senderName);
      
    } catch (error) {
      console.error('Error processing conversation:', error);
    }
  });
}

// CordLink に送信
async function sendToCordLink(data) {
  try {
    const response = await fetch(CORDLINK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data)
    });
    
    if (response.ok) {
      console.log('✅ Successfully sent to CordLink');
    } else {
      console.error('❌ Failed to send to CordLink:', response.status);
    }
  } catch (error) {
    console.error('❌ Error sending to CordLink:', error);
  }
}

// 5秒ごとにチェック
setInterval(checkForNewMessages, 5000);

// 初回実行
setTimeout(checkForNewMessages, 2000);

console.log('🚀 LinkedIn Auto Reply Extension loaded');
