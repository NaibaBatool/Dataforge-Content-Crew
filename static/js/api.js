/**
 * DataForge Content Crew - Frontend API Helper
 * Phase 1: Minimal Flask connectivity & Future API Contract Specifications
 */

(function (window) {
  'use strict';

  // API Contracts for Phase 2 (Persistence) & Phase 3 (LangGraph Agents)
  const API_CONTRACTS = {
    health: {
      endpoint: '/api/health',
      method: 'GET',
      response: {
        status: 'string ("healthy")',
        service: 'string',
        version: 'string',
        phase: 'number'
      }
    },
    chat: {
      endpoint: '/api/chat',
      method: 'POST',
      request: {
        message: 'string (Required: user query/instruction)',
        session_id: 'string (Optional: UUID for session continuity)',
        context: 'object (Optional: competitor_ids, keywords)'
      },
      response: {
        reply: 'string (Assistant response)',
        citations: 'array of objects [{ title, url, snippet }]',
        suggested_actions: 'array of strings'
      }
    },
    companyProfile: {
      endpoint: '/api/company-profile',
      methods: ['GET', 'PUT'],
      request: {
        company_name: 'string',
        industry: 'string',
        target_audience: 'string',
        brand_voice: 'string',
        competitors: 'array of objects'
      }
    },
    draft: {
      endpoint: '/api/draft',
      methods: ['GET', 'POST', 'PUT'],
      request: {
        title: 'string',
        content_markdown: 'string',
        status: 'draft | review | approved | published'
      }
    }
  };

  /**
   * Safe fetch with timeout
   */
  async function fetchWithTimeout(url, options = {}, timeoutMs = 6000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          ...(options.headers || {})
        }
      });
      clearTimeout(timeoutId);
      return response;
    } catch (err) {
      clearTimeout(timeoutId);
      throw err;
    }
  }

  /**
   * Health Check helper
   * Calls GET /api/health to confirm backend is reachable
   */
  async function checkBackendHealth() {
    const startTime = performance.now();
    try {
      const res = await fetchWithTimeout('/api/health', { method: 'GET' });
      const latencyMs = Math.round(performance.now() - startTime);

      if (!res.ok) {
        return {
          isHealthy: false,
          error: `HTTP ${res.status}: ${res.statusText}`,
          latencyMs
        };
      }

      const data = await res.json();
      return {
        isHealthy: true,
        data,
        latencyMs
      };
    } catch (err) {
      const latencyMs = Math.round(performance.now() - startTime);
      return {
        isHealthy: false,
        error: err.name === 'AbortError' ? 'Connection timed out' : err.message,
        latencyMs
      };
    }
  }

  /**
   * Updates health indicator pill element in DOM
   */
  async function updateHealthIndicator(elementId = 'health-indicator') {
    const el = document.getElementById(elementId);
    if (!el) return;

    el.className = 'health-indicator checking';
    el.title = 'Verifying Flask backend connection...';
    const textSpan = el.querySelector('.health-text') || el;
    textSpan.textContent = 'Connecting...';

    const result = await checkBackendHealth();

    if (result.isHealthy) {
      el.className = 'health-indicator healthy';
      textSpan.textContent = 'Connected';
      el.title = `Connected • ${result.latencyMs}ms response time`;
    } else {
      el.className = 'health-indicator unreachable';
      textSpan.textContent = 'Offline';
      el.title = `Unable to connect: ${result.error}`;
    }

    return result;
  }

  /**
   * Sends a message to the demo /api/chat endpoint
   */
  async function sendChatMessage(message) {
    try {
      const res = await fetchWithTimeout('/api/chat', {
        method: 'POST',
        body: JSON.stringify({ message })
      });
      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }
      return await res.json();
    } catch (err) {
      return {
        status: 'error',
        reply: `Network notice: Could not reach backend (${err.message}). Verify Flask server is running.`
      };
    }
  }

  /**
   * Toast notification helper
   */
  function showToast(message, type = 'info', duration = 3500) {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 200ms ease';
      setTimeout(() => toast.remove(), 200);
    }, duration);
  }

  // -------------------------------------------------------------------------
  // Theme Management (Light / Dark)
  // -------------------------------------------------------------------------
  const THEME_STORAGE_KEY = 'dataforge_theme';

  function getPreferredTheme() {
    const saved = localStorage.getItem(THEME_STORAGE_KEY);
    if (saved) return saved;
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    return 'light';
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try {
      localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch (e) {
      // Ignore storage restrictions
    }
    const toggleBtns = document.querySelectorAll('.btn-theme-toggle, #theme-toggle');
    toggleBtns.forEach(btn => {
      const nextTheme = theme === 'dark' ? 'light' : 'dark';
      btn.setAttribute('aria-label', `Switch to ${nextTheme} theme`);
      btn.setAttribute('title', `Switch to ${nextTheme} theme`);
    });
  }

  function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    showToast(`Switched to ${next} theme.`, 'info', 2000);
    return next;
  }

  // Apply initial theme immediately
  applyTheme(getPreferredTheme());

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.btn-theme-toggle, #theme-toggle').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        toggleTheme();
      });
    });
  });

  // -------------------------------------------------------------------------
  // Markdown Sanitizer & Renderer
  // -------------------------------------------------------------------------
  function renderMarkdown(md, title = '') {
    if (!md) return '<p><em>No content generated yet.</em></p>';

    // 1. Sanitize HTML tags to prevent XSS
    let text = md
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // 2. Strip redundant top duplicate H1 if it matches title
    if (title) {
      const escapedTitle = title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const h1Regex = new RegExp(`^#\\s+${escapedTitle}\\s*\\n*`, 'i');
      text = text.replace(h1Regex, '');
    } else {
      text = text.replace(/^#\s+.+\n*/i, '');
    }

    // 3. Render Headings
    text = text.replace(/^###\s+(.+)$/gm, '<h3>$1</h3>');
    text = text.replace(/^##\s+(.+)$/gm, '<h2>$1</h2>');
    text = text.replace(/^#\s+(.+)$/gm, '<h1>$1</h1>');

    // 4. Render Blockquotes
    text = text.replace(/^>\s+(.+)$/gm, '<blockquote>$1</blockquote>');

    // 5. Render Bold & Italic
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/__(.+?)__/g, '<strong>$1</strong>');
    text = text.replace(/\*([^\*\n]+)\*/g, '<em>$1</em>');
    text = text.replace(/_([^_\n]+)_/g, '<em>$1</em>');

    // 6. Render Inline Code and Code Blocks
    text = text.replace(/```([a-z]*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    text = text.replace(/`([^`\n]+)`/g, '<code>$1</code>');

    // 7. Render Links safely
    text = text.replace(/\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

    // 8. Render Bullet Lists
    text = text.replace(/^\*\s+(.+)$/gm, '<li>$1</li>');
    text = text.replace(/^-\s+(.+)$/gm, '<li>$1</li>');
    text = text.replace(/((?:<li>.*<\/li>\s*)+)/g, '<ul>$1</ul>');

    // Ensure structural block elements are isolated
    text = text.replace(/(<\/?(?:h[1-6]|ul|ol|blockquote|pre)[^>]*>)/gi, '\n\n$1\n\n');

    // 9. Render Paragraphs
    const blocks = text.split(/\n{2,}/);
    const htmlBlocks = blocks.map(block => {
      const trimmed = block.trim();
      if (!trimmed) return '';
      if (trimmed.startsWith('<h') || trimmed.startsWith('<ul') || trimmed.startsWith('<ol') || trimmed.startsWith('<blockquote') || trimmed.startsWith('<pre')) {
        return trimmed;
      }
      return `<p>${trimmed.replace(/\n/g, '<br>')}</p>`;
    });

    return htmlBlocks.join('\n');
  }

  // Export to global window namespace
  window.DataForgeAPI = {
    contracts: API_CONTRACTS,
    checkBackendHealth,
    updateHealthIndicator,
    sendChatMessage,
    showToast,
    toggleTheme,
    applyTheme,
    renderMarkdown
  };

})(window);
