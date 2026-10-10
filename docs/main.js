const toggle = document.getElementById('grant-toggle');
const status = document.getElementById('decision-status');
const copyButton = document.getElementById('copy-code');
const sample = document.getElementById('sample-code');

toggle?.addEventListener('click', () => {
  const granted = toggle.getAttribute('aria-pressed') !== 'true';
  toggle.setAttribute('aria-pressed', String(granted));
  status.className = `decision-status ${granted ? 'allowed' : 'denied'}`;
  status.innerHTML = granted
    ? '<span class="decision-symbol" aria-hidden="true">✓</span><div><small>WRITE drafts/reply.txt</small><strong>Allowed</strong><p>Source request and host grant match.</p></div>'
    : '<span class="decision-symbol" aria-hidden="true">×</span><div><small>WRITE drafts/reply.txt</small><strong>Denied</strong><p>No host grant is present.</p></div>';
});

copyButton?.addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(sample.innerText);
    copyButton.textContent = 'Copied';
    window.setTimeout(() => { copyButton.textContent = 'Copy code'; }, 1800);
  } catch {
    copyButton.textContent = 'Select code to copy';
  }
});
