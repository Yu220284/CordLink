const puppeteer = require('puppeteer');
const fetch = require('node-fetch');
require('dotenv').config();

const CORDLINK_WEBHOOK = process.env.CORDLINK_WEBHOOK || 'https://cordlink.onrender.com/webhook/linkedin';
const CHECK_INTERVAL = 60000; // 1分ごと
const processedMessages = new Set();

async function loginToLinkedIn(page) {
  console.log('Logging in to LinkedIn...');
  await page.goto('https://www.linkedin.com/login');
  
  await page.type('#username', process.env.LINKEDIN_EMAIL);
  await page.type('#password', process.env.LINKEDIN_PASSWORD);
  await page.click('button[type="submit"]');
  
  await page.waitForNavigation({ waitUntil: 'networkidle2' });
  console.log('Logged in successfully');
}

async function checkMessages(page) {
  try {
    await page.goto('https://www.linkedin.com/messaging/', { waitUntil: 'networkidle2' });
    
    // メッセージリストを取得
    const messages = await page.evaluate(() => {
      const conversations = document.querySelectorAll('.msg-conversation-listitem');
      const results = [];
      
      conversations.forEach(conv => {
        const nameEl = conv.querySelector('.msg-conversation-listitem__participant-names');
        const messageEl = conv.querySelector('.msg-conversation-listitem__message-snippet');
        const timeEl = conv.querySelector('time');
        const unreadBadge = conv.querySelector('.msg-conversation-listitem__unread-badge');
        
        if (nameEl && messageEl && unreadBadge) {
          results.push({
            sender_name: nameEl.textContent.trim(),
            message: messageEl.textContent.trim(),
            timestamp: timeEl ? timeEl.getAttribute('datetime') : new Date().toISOString(),
            sender_id: conv.getAttribute('data-control-id') || 'unknown'
          });
        }
      });
      
      return results;
    });
    
    // 新着メッセージをCordLinkに送信
    for (const msg of messages) {
      const msgId = `${msg.sender_id}_${msg.timestamp}`;
      
      if (!processedMessages.has(msgId)) {
        console.log(`New message from ${msg.sender_name}`);
        
        await fetch(CORDLINK_WEBHOOK, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sender_name: msg.sender_name,
            sender_role: 'Unknown',
            message: msg.message,
            sender_id: msg.sender_id
          })
        });
        
        processedMessages.add(msgId);
        console.log(`Sent to CordLink: ${msg.sender_name}`);
      }
    }
    
  } catch (error) {
    console.error('Error checking messages:', error);
  }
}

async function main() {
  console.log('Starting LinkedIn Monitor...');
  
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  await loginToLinkedIn(page);
  
  console.log('Monitoring started. Checking every minute...');
  
  // 定期的にメッセージをチェック
  setInterval(async () => {
    await checkMessages(page);
  }, CHECK_INTERVAL);
  
  // 初回チェック
  await checkMessages(page);
}

main().catch(console.error);
