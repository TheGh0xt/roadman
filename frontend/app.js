// ==========================================================================
// Roadman AI - Client Application Logic
// Handles live SSE streaming, RAG citations, Persona switching & Explorer
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
  let activePersona = 'roadman';
  const chatMessages = document.getElementById('chat-messages');
  const chatForm = document.getElementById('chat-form');
  const userInput = document.getElementById('user-input');
  const btnSend = document.getElementById('btn-send');

  // Navigation Panel Switching
  const navChat = document.getElementById('nav-chat');
  const navExplorer = document.getElementById('nav-explorer');
  const navCli = document.getElementById('nav-cli');

  const viewChat = document.getElementById('view-chat-panel');
  const viewExplorer = document.getElementById('view-explorer-panel');
  const viewCli = document.getElementById('view-cli-panel');
  const viewTitle = document.getElementById('view-title');

  function switchView(targetView, titleText, activeNav) {
    [viewChat, viewExplorer, viewCli].forEach(v => v.classList.remove('active'));
    [navChat, navExplorer, navCli].forEach(n => n.classList.remove('active'));

    targetView.classList.add('active');
    activeNav.classList.add('active');
    viewTitle.textContent = titleText;
  }

  navChat.addEventListener('click', () => switchView(viewChat, 'Traffic Law Assistant', navChat));
  navExplorer.addEventListener('click', () => {
    switchView(viewExplorer, 'Traffic Law Explorer', navExplorer);
    loadExplorerLaws();
  });
  navCli.addEventListener('click', () => switchView(viewCli, 'CLI Integration Guide', navCli));

  // Persona Selection Buttons
  const personaBtns = document.querySelectorAll('.persona-btn');
  personaBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      personaBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activePersona = btn.getAttribute('data-mode');
    });
  });

  // Quick-Prompt Pills
  document.addEventListener('click', (e) => {
    const pill = e.target.closest('.prompt-pill');
    if (pill) {
      const query = pill.getAttribute('data-query');
      if (query) {
        userInput.value = query;
        chatForm.dispatchEvent(new Event('submit'));
      }
    }
  });

  // Clear Chat Button
  document.getElementById('btn-clear-chat').addEventListener('click', () => {
    chatMessages.innerHTML = `
      <div class="message-card system-welcome">
        <div class="avatar roadman-avatar">🧢</div>
        <div class="msg-content">
          <div class="msg-header">
            <span class="author-name">Roadman AI</span>
            <span class="timestamp">Just now</span>
          </div>
          <div class="msg-body">
            <p>History cleared! Ask me anything about traffic laws, speed limits, or penalties.</p>
          </div>
        </div>
      </div>
    `;
  });

  // Handle Form Submission with SSE Streaming
  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = userInput.value.trim();
    if (!query) return;

    // Append User Message Card
    appendUserMessage(query);
    userInput.value = '';
    btnSend.disabled = true;

    // Create Bot Response Container
    const { botMsgBody, citationContainer, cardElement } = createBotMessageCard();

    try {
      // Connect to SSE Endpoint
      const encodedQuery = encodeURIComponent(query);
      const sseUrl = `/api/chat/stream?query=${encodedQuery}&persona_mode=${activePersona}`;
      
      const eventSource = new EventSource(sseUrl);
      let streamText = '';

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'citations') {
            renderCitations(data.citations, citationContainer);
          } else if (data.type === 'token') {
            streamText += data.content;
            botMsgBody.innerHTML = formatMarkdown(streamText);
            scrollToBottom();
          } else if (data.type === 'done') {
            eventSource.close();
            btnSend.disabled = false;
          }
        } catch (err) {
          console.error("SSE JSON parsing error:", err);
        }
      };

      eventSource.onerror = (err) => {
        console.warn("SSE fallback to REST chat endpoint:", err);
        eventSource.close();
        fetchFallbackRestChat(query, botMsgBody, citationContainer);
      };

    } catch (error) {
      console.error("Stream initialization error:", error);
      btnSend.disabled = false;
    }
  });

  // REST Fallback in case SSE drops
  async function fetchFallbackRestChat(query, botMsgBody, citationContainer) {
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query, persona_mode: activePersona })
      });
      const data = await res.json();
      botMsgBody.innerHTML = formatMarkdown(data.answer);
      renderCitations(data.citations, citationContainer);
    } catch (err) {
      botMsgBody.innerHTML = `<p style="color: var(--accent-red)">⚠️ Error communicating with Roadman RAG service.</p>`;
    } finally {
      btnSend.disabled = false;
      scrollToBottom();
    }
  }

  // Helper Functions
  function appendUserMessage(text) {
    const card = document.createElement('div');
    card.className = 'message-card user';
    card.innerHTML = `
      <div class="avatar user-avatar">👤</div>
      <div class="msg-content">
        <div class="msg-header">
          <span class="author-name">You</span>
          <span class="timestamp">${getCurrentTime()}</span>
        </div>
        <div class="msg-body">
          <p>${escapeHtml(text)}</p>
        </div>
      </div>
    `;
    chatMessages.appendChild(card);
    scrollToBottom();
  }

  function createBotMessageCard() {
    const card = document.createElement('div');
    card.className = 'message-card bot';
    
    let avatarIcon = '🧢';
    if (activePersona === 'strict') avatarIcon = '⚖️';
    if (activePersona === 'hyper') avatarIcon = '🚨';

    card.innerHTML = `
      <div class="avatar roadman-avatar">${avatarIcon}</div>
      <div class="msg-content">
        <div class="msg-header">
          <span class="author-name">Roadman AI</span>
          <span class="timestamp">${getCurrentTime()}</span>
        </div>
        <div class="msg-body">
          <span class="typing-indicator">Retrieving RAG law code...</span>
        </div>
        <div class="citation-box-wrapper"></div>
      </div>
    `;
    chatMessages.appendChild(card);
    scrollToBottom();

    return {
      cardElement: card,
      botMsgBody: card.querySelector('.msg-body'),
      citationContainer: card.querySelector('.citation-box-wrapper')
    };
  }

  function renderCitations(citations, container) {
    if (!citations || citations.length === 0) return;
    const top = citations[0];
    
    container.innerHTML = `
      <div class="citation-box">
        <div class="citation-header">
          <i class="ri-book-mark-line"></i> Verified Statutory Citation: Section ${top.section} — ${top.title}
        </div>
        <div class="fine-badge-row">
          ${top.fine ? `<span class="badge-fine"><i class="ri-coins-line"></i> ${top.fine}</span>` : ''}
          ${top.points ? `<span class="badge-points"><i class="ri-error-warning-line"></i> ${top.points}</span>` : ''}
        </div>
      </div>
    `;
  }

  function formatMarkdown(text) {
    let html = escapeHtml(text);
    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Code
    html = html.replace(/`(.*?)`/g, '<code style="background: rgba(250,204,21,0.15); color: #facc15; padding: 2px 6px; border-radius: 4px;">$1</code>');
    // Paragraphs
    return html.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br/>');
  }

  function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // Explorer Tab Population
  async function loadExplorerLaws(query = '') {
    const explorerGrid = document.getElementById('explorer-grid');
    explorerGrid.innerHTML = `<p style="color: var(--text-dim)">Loading traffic laws & FRSC rules database...</p>`;
    
    try {
      const url = query ? `/api/rag/search?q=${encodeURIComponent(query)}&top_k=24` : `/api/rag/search?q=traffic%20rules%20safety%20frsc&top_k=24`;
      const res = await fetch(url);
      const data = await res.json();
      
      if (!data.chunks || data.chunks.length === 0) {
        explorerGrid.innerHTML = `<p style="color: var(--text-dim)">No traffic laws match your query.</p>`;
        return;
      }

      explorerGrid.innerHTML = data.chunks.map(item => `
        <div class="law-card">
          <span class="law-sec">${item.metadata.section_number || 'FRSC Code'} • ${item.metadata.source || item.metadata.jurisdiction || 'FRSC Official Code'}</span>
          <h4 class="law-title">${escapeHtml(item.metadata.title || 'Road Traffic Rule')}</h4>
          <p class="law-text">${escapeHtml(item.text.substring(0, 240))}${item.text.length > 240 ? '...' : ''}</p>
          <div class="fine-badge-row">
            ${item.metadata.fine ? `<span class="badge-fine"><i class="ri-coins-line"></i> ${escapeHtml(item.metadata.fine)}</span>` : ''}
            ${item.metadata.points ? `<span class="badge-points"><i class="ri-error-warning-line"></i> ${escapeHtml(item.metadata.points)}</span>` : ''}
          </div>
        </div>
      `).join('');
    } catch (err) {
      explorerGrid.innerHTML = `<p style="color: var(--accent-red)">Error loading traffic laws database.</p>`;
    }
  }

  const explorerSearch = document.getElementById('explorer-search');
  if (explorerSearch) {
    let debounceTimer;
    explorerSearch.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        loadExplorerLaws(e.target.value.trim());
      }, 300);
    });
  }
});

function copyCliCommand() {
  const code = `python cli/roadman_cli.py`;
  navigator.clipboard.writeText(code);
  alert("CLI command copied to clipboard!");
}
