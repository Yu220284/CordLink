document.getElementById('testBtn').addEventListener('click', async () => {
  const btn = document.getElementById('testBtn');
  btn.textContent = 'Testing...';
  btn.disabled = true;
  
  try {
    const response = await fetch('http://localhost:8002/health');
    if (response.ok) {
      btn.textContent = '✅ Connection OK';
      btn.style.backgroundColor = '#28a745';
    } else {
      btn.textContent = '❌ Connection Failed';
      btn.style.backgroundColor = '#dc3545';
    }
  } catch (error) {
    btn.textContent = '❌ CordLink Not Running';
    btn.style.backgroundColor = '#dc3545';
  }
  
  setTimeout(() => {
    btn.textContent = 'Test Connection';
    btn.style.backgroundColor = '#0073b1';
    btn.disabled = false;
  }, 3000);
});
