/**
 * DataForge Content Crew - Blogs Page Catalog Logic
 * Shared Application Shell, Live SQLite Integration & Modal Reader
 */

document.addEventListener('DOMContentLoaded', () => {
  const blogsGrid = document.getElementById('blogs-grid');
  const blogsEmpty = document.getElementById('blogs-empty');
  const blogsEmptyHeading = document.getElementById('blogs-empty-heading');
  const blogsEmptyText = document.getElementById('blogs-empty-text');
  const searchInput = document.getElementById('blogs-search');
  const statusFilter = document.getElementById('status-filter');

  // Sidebar Elements
  const sidebarProfileContent = document.getElementById('sidebar-profile-content');
  const sidebarCompetitorsList = document.getElementById('sidebar-competitors-list');

  // Modal Elements
  const readModal = document.getElementById('article-read-modal');
  const readModalTitle = document.getElementById('read-modal-title');
  const readModalContent = document.getElementById('read-modal-content');
  const readMetaCompany = document.getElementById('read-meta-company');
  const readMetaDate = document.getElementById('read-meta-date');
  const readMetaWords = document.getElementById('read-meta-words');
  const readModalClose = document.getElementById('read-modal-close');
  const readModalDismiss = document.getElementById('read-modal-dismiss');
  const readModalWorkspaceLink = document.getElementById('read-modal-workspace-link');

  // Theme Toggle Button
  const themeToggleBtn = document.getElementById('theme-toggle');
  if (themeToggleBtn && window.DataForgeAPI && window.DataForgeAPI.toggleTheme) {
    themeToggleBtn.addEventListener('click', () => {
      window.DataForgeAPI.toggleTheme();
    });
  }

  let allArticles = [];

  // -------------------------------------------------------------------------
  // 1. Sidebar Brand Context Loading
  // -------------------------------------------------------------------------
  async function loadSidebarContext() {
    // Load Company Profile
    try {
      const res = await fetch('/api/company-profile');
      if (res.ok) {
        const data = await res.json();
        if (data.profile && sidebarProfileContent) {
          const p = data.profile;
          const webDisplay = p.website ? p.website.replace(/^https?:\/\//i, '') : 'dataforge.ai';
          sidebarProfileContent.innerHTML = `
            <div class="profile-field" style="margin-bottom:0.4rem;">
              <div class="profile-label" style="font-size:0.7rem; color:var(--color-muted-gray);">Organization</div>
              <div class="profile-value" style="font-size:0.825rem; font-weight:700; color:var(--color-deep-teal);">${escapeHtml(p.company_name)}</div>
            </div>
            <div class="profile-field" style="margin-bottom:0.4rem;">
              <div class="profile-label" style="font-size:0.7rem; color:var(--color-muted-gray);">Industry</div>
              <div class="profile-value" style="font-size:0.8rem; color:var(--color-text-main);">${escapeHtml(p.industry)}</div>
            </div>
            <div class="profile-field" style="margin-bottom:0.4rem;">
              <div class="profile-label" style="font-size:0.7rem; color:var(--color-muted-gray);">Brand Voice</div>
              <div class="profile-value" style="font-size:0.8rem; color:var(--color-text-main);">${escapeHtml(p.tone)}</div>
            </div>
          `;
        }
      }
    } catch (e) {
      console.warn('Could not load profile for sidebar', e);
    }

    // Load Competitors
    try {
      const compRes = await fetch('/api/competitors');
      if (compRes.ok) {
        const compData = await compRes.json();
        const comps = compData.competitors || [];
        if (sidebarCompetitorsList) {
          if (comps.length === 0) {
            sidebarCompetitorsList.innerHTML = '<li class="empty-sidebar-note" style="font-size:0.775rem; color:var(--color-muted-gray);">No competitors added yet.</li>';
          } else {
            sidebarCompetitorsList.innerHTML = comps.map(c => `
              <li style="padding:0.35rem 0; border-bottom:1px solid var(--color-border-subtle); display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:0.8rem; font-weight:600; color:var(--color-deep-teal);">${escapeHtml(c.name)}</span>
                <span style="font-size:0.7rem; color:var(--color-muted-gray);">${escapeHtml((c.website_url || '').replace(/^https?:\/\//, '').slice(0, 16))}</span>
              </li>
            `).join('');
          }
        }
      }
    } catch (e) {
      console.warn('Could not load competitors for sidebar', e);
    }
  }

  // -------------------------------------------------------------------------
  // 2. Fetch and Render Articles
  // -------------------------------------------------------------------------
  async function loadArticles() {
    const status = statusFilter ? statusFilter.value : 'published';
    const query = searchInput ? searchInput.value.trim() : '';

    if (blogsGrid) {
      blogsGrid.innerHTML = `
        <div class="blogs-loading">
          <div class="spinner"></div>
          <p>Loading articles library...</p>
        </div>
      `;
    }
    if (blogsEmpty) blogsEmpty.style.display = 'none';

    try {
      const url = new URL('/api/blogs', window.location.origin);
      if (status && status !== 'all') url.searchParams.set('status', status);
      if (query) url.searchParams.set('q', query);

      const res = await fetch(url.toString());
      const data = await res.json();

      if (res.ok && data.blogs) {
        allArticles = data.blogs;
        renderArticlesList(allArticles);
      } else {
        showEmptyState(
          'No articles published yet',
          'Your published articles will appear here. Start by researching a topic and creating your first blog.'
        );
      }
    } catch (err) {
      showEmptyState(
        'Unable to load articles',
        'Network error connecting to backend: ' + err.message
      );
    }
  }

  function renderArticlesList(articles) {
    if (!blogsGrid) return;
    blogsGrid.innerHTML = '';

    if (!articles || articles.length === 0) {
      showEmptyState(
        'No articles published yet',
        'Your published articles will appear here. Start by researching a topic and creating your first blog.'
      );
      return;
    }

    if (blogsEmpty) blogsEmpty.style.display = 'none';

    articles.forEach(article => {
      const card = document.createElement('article');
      card.className = 'blog-card';

      const readTime = Math.max(1, Math.ceil((article.word_count || 1) / 200));
      const formattedDate = formatDate(article.published_at || article.updated_at || article.created_at);
      const company = article.company_name || 'DataForge Context';
      const statusClass = getStatusBadgeClass(article.status);
      const statusLabel = (article.status || 'Draft').toUpperCase();

      card.innerHTML = `
        <div class="card-top">
          <div class="card-header-row">
            <div class="card-icon-box" title="Article Document" aria-hidden="true">
              <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"></path>
              </svg>
            </div>
            <span class="badge ${statusClass}">${escapeHtml(statusLabel)}</span>
          </div>

          <span class="card-company-label">${escapeHtml(company)}</span>
          <h2 class="card-title">${escapeHtml(article.title || 'Untitled Article')}</h2>
          <p class="card-snippet">${escapeHtml(getSnippet(article.content_markdown))}</p>
        </div>

        <div class="card-bottom">
          <div class="card-stats">
            <div><strong>${article.word_count || 0}</strong> words &bull; ${readTime} min read</div>
            <div style="font-size:0.7rem; color:var(--color-muted-gray); margin-top:2px;">${formattedDate}</div>
          </div>
          <div class="card-actions">
            <button type="button" class="btn btn-secondary btn-sm btn-read-article" data-id="${article.id}" title="Open article in reader modal">
              Open Article
            </button>
            <a href="/workspace?draft_id=${article.id}" class="btn btn-outline btn-sm" title="Edit in Workspace">
              Edit in Workspace
            </a>
          </div>
        </div>
      `;

      // Bind Open Article button
      const btnRead = card.querySelector('.btn-read-article');
      if (btnRead) {
        btnRead.addEventListener('click', () => openArticleModal(article));
      }

      blogsGrid.appendChild(card);
    });
  }

  function showEmptyState(heading, desc) {
    if (blogsGrid) blogsGrid.innerHTML = '';
    if (blogsEmpty) {
      blogsEmpty.style.display = 'block';
      if (blogsEmptyHeading) blogsEmptyHeading.textContent = heading || 'No articles published yet';
      if (blogsEmptyText) blogsEmptyText.textContent = desc || 'Your published articles will appear here. Start by researching a topic and creating your first blog.';
    }
  }

  function getStatusBadgeClass(status) {
    const s = (status || '').toLowerCase();
    if (s === 'published') return 'badge-published';
    if (s === 'approved') return 'badge-approved';
    return 'badge-draft';
  }

  function getSnippet(markdown) {
    if (!markdown) return 'No content preview available.';
    return markdown
      .replace(/^#+\s+/gm, '')
      .replace(/\*\*|__/g, '')
      .replace(/\*|_/g, '')
      .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')
      .replace(/`{1,3}[^`]*`{1,3}/g, '')
      .trim();
  }

  function formatDate(isoStr) {
    if (!isoStr) return 'Recently';
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return isoStr.substring(0, 10);
    }
  }

  // -------------------------------------------------------------------------
  // 3. Article Reading Modal
  // -------------------------------------------------------------------------
  function openArticleModal(article) {
    if (!readModal) return;
    const readTime = Math.max(1, Math.ceil((article.word_count || 1) / 200));

    if (readModalTitle) readModalTitle.textContent = article.title || 'Untitled Article';
    if (readMetaCompany) readMetaCompany.textContent = article.company_name || 'DataForge Context';
    if (readMetaDate) readMetaDate.textContent = formatDate(article.published_at || article.updated_at);
    if (readMetaWords) readMetaWords.textContent = `${article.word_count || 0} words (${readTime} min read)`;

    if (readModalContent) {
      if (window.DataForgeAPI && window.DataForgeAPI.renderMarkdown) {
        readModalContent.innerHTML = window.DataForgeAPI.renderMarkdown(article.content_markdown || '', article.title);
      } else {
        readModalContent.innerHTML = renderMarkdownFallback(article.content_markdown || '', article.title);
      }
    }

    if (readModalWorkspaceLink) {
      readModalWorkspaceLink.href = `/workspace?draft_id=${article.id}`;
    }

    readModal.classList.add('active');
  }

  function closeArticleModal() {
    if (readModal) readModal.classList.remove('active');
  }

  if (readModalClose) readModalClose.addEventListener('click', closeArticleModal);
  if (readModalDismiss) readModalDismiss.addEventListener('click', closeArticleModal);
  if (readModal) {
    readModal.addEventListener('click', (e) => {
      if (e.target === readModal) closeArticleModal();
    });
  }

  // -------------------------------------------------------------------------
  // 4. Search & Filter Listeners (Debounced)
  // -------------------------------------------------------------------------
  let searchTimer;
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(loadArticles, 250);
    });
  }

  if (statusFilter) {
    statusFilter.addEventListener('change', loadArticles);
  }

  // Fallback Markdown Renderer
  function renderMarkdownFallback(md, title) {
    if (!md) return '<p><em>No content available.</em></p>';
    let text = md.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    text = text.replace(/^###\s+(.+)$/gm, '<h3>$1</h3>');
    text = text.replace(/^##\s+(.+)$/gm, '<h2>$1</h2>');
    text = text.replace(/^#\s+(.+)$/gm, '<h1>$1</h1>');
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    return text.split(/\n{2,}/).map(p => `<p>${p.trim()}</p>`).join('');
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Initial load
  loadSidebarContext();
  loadArticles();
});
