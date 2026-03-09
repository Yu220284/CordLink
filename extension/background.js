// Background service worker
chrome.runtime.onInstalled.addListener(() => {
  console.log('LinkedIn Auto Reply Extension installed');
});

// メッセージリスナー
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'newMessage') {
    console.log('New message detected:', request.data);
    sendResponse({status: 'received'});
  }
});
