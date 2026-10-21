/**
 * DataForge Content Crew - Blog Workspace Logic
 * Phase 3: LangGraph Agent & Gemini Integration
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const chatMessages = document.getElementById('chat-messages');
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const wordCountEl = document.getElementById('word-count');
  const readTimeEl = document.getElementById('read-time');
  const draftStatusBadge = document.getElementById('draft-status-badge');
  const articleBody = document.getElementById('article-body');
  const rawEditor = document.getElementById('raw-editor');
  const draftTitleInput = document.getElementById('draft-title');
  const btnToggleEdit = document.getElementById('btn-toggle-edit');
  const btnSaveDraft = document.getElementById('btn-save-draft');
  const btnRequestRevision = document.getElementById('btn-request-revision');
  const btnApprove = document.getElementById('btn-approve');
  const btnPublish = document.getElementById('btn-publish');
  const btnRegenerate = document.getElementById('btn-regenerate');
  const emptyDraftView = document.getElementById('empty-draft-view');
  const populatedDraftView = document.getElementById('populated-draft-view');
  const btnLoadSample = document.getElementById('btn-load-sample');

  // Regenerate Confirmation Modal
  const regenModal = document.getElementById('regenerate-confirm-modal');
  const btnRegenConfirm = document.getElementById('modal-regen-confirm');
  const btnRegenCancel = document.getElementById('modal-regen-cancel');
  const btnRegenClose = document.getElementById('modal-regen-close');

  // Chat Session & History Controls
  const btnNewChat = document.getElementById('btn-new-chat');
  const btnChatHistory = document.getElementById('btn-chat-history');
  const chatHistoryModal = document.getElementById('chat-history-modal');
  const chatHistoryList = document.getElementById('chat-history-list');
  const modalHistoryClose = document.getElementById('modal-history-close');
  const modalHistoryDismiss = document.getElementById('modal-history-dismiss');
  const btnModalNewChat = document.getElementById('btn-modal-new-chat');
  const chatSessionBadge = document.querySelector('.chat-session-badge');

  // Customize Workspace Modal
  const btnCustomizeWorkspace = document.getElementById('btn-customize-workspace');
  const customizeModal = document.getElementById('customize-workspace-modal');
  const btnCustomizeClose = document.getElementById('modal-customize-close');
  const btnCustomizeSave = document.getElementById('modal-customize-save');
  const prefShowSidebar = document.getElementById('pref-show-sidebar');
  const prefShowDraft = document.getElementById('pref-show-draft');
  const prefDensityComfortable = document.getElementById('pref-density-comfortable');
  const prefDensityCompact = document.getElementById('pref-density-compact');
  const btnResetLayout = document.getElementById('btn-reset-layout');

  // Workspace Panels & Resize Dividers
  const panelSidebar = document.getElementById('panel-sidebar');
  const panelChat = document.getElementById('panel-chat');
  const panelEditor = document.getElementById('panel-editor');
  const resizeHandleLeft = document.getElementById('resize-handle-left');
  const resizeHandleRight = document.getElementById('resize-handle-right');
  const btnCollapseSidebar = document.getElementById('btn-collapse-sidebar');
  const btnExpandSidebar = document.getElementById('btn-expand-sidebar');

  // Sidebar Elements
  const sidebarProfileContent = document.getElementById('sidebar-profile-content');
  const sidebarCompetitorsList = document.getElementById('sidebar-competitors-list');
  const linkEditProfile = document.getElementById('link-edit-profile');

  // Blog Side Panel Controls
  const btnToggleDraftPanel = document.getElementById('btn-toggle-draft-panel');
  const draftPanelBtnLabel = document.getElementById('draft-panel-btn-label');
  const headerDraftPill = document.getElementById('header-draft-pill');
  const btnCloseDraftPanel = document.getElementById('btn-close-draft-panel');
  const btnExpandDraft = document.getElementById('btn-expand-draft');

  // Demo Library Modal Elements
  const btnDemoLibrary = document.getElementById('btn-demo-library');
  const demoLibraryModal = document.getElementById('demo-library-modal');
  const demoLibraryList = document.getElementById('demo-library-list');
  const modalLibraryClose = document.getElementById('modal-library-close');
  const modalLibraryDismiss = document.getElementById('modal-library-dismiss');

  // Profile Modal Elements
  const profileModal = document.getElementById('profile-modal');
  const profileEditForm = document.getElementById('profile-edit-form');
  const btnCloseProfileModal = document.getElementById('modal-profile-close');
  const btnCancelProfileModal = document.getElementById('modal-profile-cancel');

  // Competitor Modal Elements
  const competitorModal = document.getElementById('competitor-modal');
  const competitorForm = document.getElementById('competitor-form');
  const btnOpenCompModal = document.getElementById('btn-open-competitor-modal');
  const btnCloseCompModal = document.getElementById('modal-comp-close');
  const btnCancelCompModal = document.getElementById('modal-comp-cancel');
  const modalCompTitle = document.getElementById('modal-comp-title');
  const compIdInput = document.getElementById('comp-id');
  const compNameInput = document.getElementById('comp-name');
  const compUrlInput = document.getElementById('comp-url');
  const compNotesInput = document.getElementById('comp-notes');

  // Mobile Tabs
  const mobileTabBtns = document.querySelectorAll('.ws-tab-btn');
  const tabPanels = {
    sidebar: document.getElementById('panel-sidebar'),
    chat: document.getElementById('panel-chat'),
    editor: document.getElementById('panel-editor')
  };

  // State
  let isEditingRaw = false;
  let activeDraftId = null;
  let currentDraftVersion = 1;
  let isDraftApproved = false;
  let activeSessionId = null;

  // Initialize Backend Health
  if (window.DataForgeAPI && window.DataForgeAPI.updateHealthIndicator) {
    window.DataForgeAPI.updateHealthIndicator('ws-health-indicator');
  }

  // -------------------------------------------------------------------------
  // 1. Company Profile Loading (SQLite) & In-Workspace Modal
  // -------------------------------------------------------------------------
  async function loadCompanyProfile() {
    try {
      const res = await fetch('/api/company-profile');
      if (!res.ok) return;
      const data = await res.json();

      if (data.profile) {
        const p = data.profile;
        if (linkEditProfile) linkEditProfile.textContent = 'Edit';
        if (sidebarProfileContent) {
          const webDisplay = p.website ? p.website.replace(/^https?:\/\//i, '') : 'dataforge.ai';
          sidebarProfileContent.innerHTML = `
            <div class="profile-field">
              <div class="profile-label">Organization</div>
              <div class="profile-value"><strong>${escapeHtml(p.company_name)}</strong></div>
            </div>
            <div class="profile-field">
              <div class="profile-label">Website</div>
              <a href="${escapeHtml(p.website || '#')}" target="_blank" rel="noopener noreferrer" class="competitor-url" style="color:var(--color-orange); font-weight:600; text-decoration:none;">
                ${escapeHtml(webDisplay)}
              </a>
            </div>
            <div class="profile-field">
              <div class="profile-label">Industry</div>
              <div class="profile-value">${escapeHtml(p.industry)}</div>
            </div>
            <div class="profile-field">
              <div class="profile-label">Target Audience</div>
              <div class="profile-value">${escapeHtml(p.target_audience)}</div>
            </div>
            <div class="profile-field">
              <div class="profile-label">Brand Voice</div>
              <div class="profile-value">${escapeHtml(p.tone)}</div>
            </div>
          `;
        }
      } else {
        if (linkEditProfile) linkEditProfile.textContent = 'Configure';
        if (sidebarProfileContent) {
          sidebarProfileContent.innerHTML = `
            <div class="empty-sidebar-note">
              No company profile configured yet.<br>
              <button type="button" id="btn-empty-conf-profile" style="color:var(--color-orange); font-weight:600; display:inline-block; margin-top:0.35rem; background:none; border:none; padding:0; cursor:pointer;">Configure DataForge Profile &rarr;</button>
            </div>
          `;
          const emptyBtn = document.getElementById('btn-empty-conf-profile');
          if (emptyBtn) emptyBtn.addEventListener('click', openProfileModal);
        }
      }
    } catch (err) {
      console.error('Failed to load company profile:', err);
    }
  }

  async function openProfileModal() {
    if (!profileModal) return;
    clearProfileErrors();

    try {
      const res = await fetch('/api/company-profile');
      if (res.ok) {
        const data = await res.json();
        const p = data.profile || {};
        document.getElementById('edit-prof-company-name').value = p.company_name || 'DataForge';
        document.getElementById('edit-prof-website').value = p.website || 'https://dataforge.ai';
        document.getElementById('edit-prof-industry').value = p.industry || 'Enterprise AI & Content Marketing';
        document.getElementById('edit-prof-target-audience').value = p.target_audience || 'B2B Marketing Leaders, Technical Directors';
        document.getElementById('edit-prof-description').value = p.description || 'Autonomous AI Content Crew for B2B tech and enterprise SaaS. Automates deep competitor research, SEO intelligence, and high-impact technical blog generation.';
        document.getElementById('edit-prof-products').value = p.products_services || 'DataForge Content Crew, Competitor SERP Intelligence Engine, AI Technical Blog Synthesizer';
        document.getElementById('edit-prof-usp').value = p.usp || 'Conducts genuine competitor and SEO research before producing authoritative, publication-ready technical content with autonomous multi-agent verification.';
        if (p.tone) {
          const toneSelect = document.getElementById('edit-prof-tone');
          if (toneSelect) toneSelect.value = p.tone;
        }
        document.getElementById('edit-prof-goals').value = p.content_goals || 'Drive organic search dominance, thought leadership, and developer-focused product adoption';
      }
    } catch (err) {
      console.warn('Could not prefetch profile for modal:', err);
    }

    profileModal.classList.add('active');
    document.getElementById('edit-prof-company-name').focus();
  }

  function closeProfileModal() {
    if (profileModal) {
      profileModal.classList.remove('active');
      clearProfileErrors();
    }
  }

  function clearProfileErrors() {
    if (!profileEditForm) return;
    profileEditForm.querySelectorAll('.form-input, .form-textarea, .form-select').forEach(el => el.classList.remove('is-invalid'));
    profileEditForm.querySelectorAll('.field-error').forEach(el => { el.textContent = ''; el.classList.remove('visible'); });
  }

  async function handleProfileSubmit(e) {
    e.preventDefault();
    clearProfileErrors();

    const payload = {
      company_name: document.getElementById('edit-prof-company-name').value.trim(),
      website: document.getElementById('edit-prof-website').value.trim(),
      industry: document.getElementById('edit-prof-industry').value.trim(),
      target_audience: document.getElementById('edit-prof-target-audience').value.trim(),
      description: document.getElementById('edit-prof-description').value.trim(),
      products_services: document.getElementById('edit-prof-products').value.trim(),
      usp: document.getElementById('edit-prof-usp').value.trim(),
      tone: document.getElementById('edit-prof-tone').value.trim(),
      content_goals: document.getElementById('edit-prof-goals').value.trim()
    };

    try {
      const res = await fetch('/api/company-profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (!res.ok) {
        if (data.details) {
          Object.entries(data.details).forEach(([field, msg]) => {
            const fieldId = 'edit-prof-' + (field === 'company_name' ? 'company-name' : field === 'target_audience' ? 'target-audience' : field === 'products_services' ? 'products' : field === 'content_goals' ? 'goals' : field);
            const errId = 'err-edit-' + (field === 'company_name' ? 'company-name' : field === 'target_audience' ? 'target-audience' : field === 'products_services' ? 'products' : field === 'content_goals' ? 'goals' : field);
            const input = document.getElementById(fieldId);
            const errSpan = document.getElementById(errId);
            if (input) input.classList.add('is-invalid');
            if (errSpan) { errSpan.textContent = msg; errSpan.classList.add('visible'); }
          });
        }
        window.DataForgeAPI.showToast(data.error || 'Failed to update company profile.', 'warning');
        return;
      }

      window.DataForgeAPI.showToast('DataForge company profile saved successfully.', 'info');
      closeProfileModal();
      loadCompanyProfile();
    } catch (err) {
      window.DataForgeAPI.showToast('Network error: ' + err.message, 'warning');
    }
  }

  if (linkEditProfile) {
    linkEditProfile.addEventListener('click', (e) => {
      e.preventDefault();
      openProfileModal();
    });
  }
  if (btnCloseProfileModal) btnCloseProfileModal.addEventListener('click', closeProfileModal);
  if (btnCancelProfileModal) btnCancelProfileModal.addEventListener('click', closeProfileModal);
  if (profileEditForm) profileEditForm.addEventListener('submit', handleProfileSubmit);

  // -------------------------------------------------------------------------
  // Resizable Panels & Layout Persistence
  // -------------------------------------------------------------------------
  const STORAGE_KEY = 'dataforge_workspace_layout_prefs';
  let layoutPrefs = {
    leftWidth: 270,
    rightWidth: 480,
    leftCollapsed: false,
    rightCollapsed: false
  };

  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      layoutPrefs = { ...layoutPrefs, ...JSON.parse(saved) };
    }
  } catch (e) {
    console.warn('Could not read layout preferences from localStorage:', e);
  }

  function saveLayoutPrefs() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(layoutPrefs));
    } catch (e) {
      // Ignore quota errors
    }
  }

  function updateDraftPanelButtonState(isOpen, draft = null) {
    if (draftPanelBtnLabel) {
      draftPanelBtnLabel.textContent = isOpen ? 'Hide Draft Sidebar' : 'View Blog Draft';
    }
    if (headerDraftPill) {
      if (draft || activeDraftId) {
        headerDraftPill.style.display = 'inline-block';
        const text = isEditingRaw && rawEditor ? rawEditor.value : (articleBody ? articleBody.innerText || '' : '');
        const count = calculateWordCount(text);
        headerDraftPill.textContent = count > 0 ? `${count}w` : 'Draft';
      } else {
        headerDraftPill.style.display = 'none';
      }
    }
  }

  function applyLayoutPrefs() {
    if (window.innerWidth <= 900) return; // Responsive tablet/mobile layout takes precedence

    // Left Panel Restoration
    if (panelSidebar) {
      if (layoutPrefs.leftCollapsed) {
        panelSidebar.classList.add('collapsed');
        if (resizeHandleLeft) resizeHandleLeft.classList.add('hidden-handle');
        if (btnExpandSidebar) btnExpandSidebar.style.display = 'inline-flex';
      } else {
        panelSidebar.classList.remove('collapsed');
        if (resizeHandleLeft) resizeHandleLeft.classList.remove('hidden-handle');
        if (btnExpandSidebar) btnExpandSidebar.style.display = 'none';
        const lw = Math.min(Math.max(layoutPrefs.leftWidth || 270, 210), 450);
        panelSidebar.style.width = `${lw}px`;
        if (resizeHandleLeft) resizeHandleLeft.setAttribute('aria-valuenow', lw);
      }
    }

    // Right Panel Restoration
    if (panelEditor) {
      if (layoutPrefs.rightCollapsed) {
        panelEditor.classList.add('collapsed');
        if (resizeHandleRight) resizeHandleRight.classList.add('hidden-handle');
        updateDraftPanelButtonState(false);
      } else {
        panelEditor.classList.remove('collapsed');
        if (resizeHandleRight) resizeHandleRight.classList.remove('hidden-handle');
        const rw = Math.min(Math.max(layoutPrefs.rightWidth || 480, 320), 850);
        panelEditor.style.width = `${rw}px`;
        if (resizeHandleRight) resizeHandleRight.setAttribute('aria-valuenow', rw);
        updateDraftPanelButtonState(true);
      }
    }
  }

  // Left Panel Resize Dragging
  if (resizeHandleLeft && panelSidebar) {
    let startX = 0;
    let startWidth = 270;

    const onLeftMove = (e) => {
      const delta = e.clientX - startX;
      const wsWidth = document.querySelector('.ws-main')?.getBoundingClientRect().width || window.innerWidth;
      const rightW = (!panelEditor || panelEditor.classList.contains('collapsed')) ? 0 : panelEditor.getBoundingClientRect().width;
      const maxAllowed = Math.max(250, wsWidth - rightW - 340); // Keep at least 340px for chat
      const newWidth = Math.min(Math.max(startWidth + delta, 210), Math.min(450, maxAllowed));

      panelSidebar.style.width = `${newWidth}px`;
      layoutPrefs.leftWidth = newWidth;
      resizeHandleLeft.setAttribute('aria-valuenow', Math.round(newWidth));
    };

    const onLeftUp = () => {
      document.body.classList.remove('resizing-active');
      resizeHandleLeft.classList.remove('active-resizing');
      window.removeEventListener('pointermove', onLeftMove);
      window.removeEventListener('pointerup', onLeftUp);
      saveLayoutPrefs();
    };

    resizeHandleLeft.addEventListener('pointerdown', (e) => {
      if (e.button !== 0) return;
      startX = e.clientX;
      startWidth = panelSidebar.getBoundingClientRect().width;
      document.body.classList.add('resizing-active');
      resizeHandleLeft.classList.add('active-resizing');
      window.addEventListener('pointermove', onLeftMove);
      window.addEventListener('pointerup', onLeftUp);
    });

    // Keyboard support for Left Handle
    resizeHandleLeft.addEventListener('keydown', (e) => {
      const step = e.shiftKey ? 30 : 15;
      let curr = panelSidebar.getBoundingClientRect().width;
      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        const next = Math.max(210, curr - step);
        panelSidebar.style.width = `${next}px`;
        layoutPrefs.leftWidth = next;
        resizeHandleLeft.setAttribute('aria-valuenow', Math.round(next));
        saveLayoutPrefs();
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        const next = Math.min(450, curr + step);
        panelSidebar.style.width = `${next}px`;
        layoutPrefs.leftWidth = next;
        resizeHandleLeft.setAttribute('aria-valuenow', Math.round(next));
        saveLayoutPrefs();
      }
    });
  }

  // Right Panel Resize Dragging
  if (resizeHandleRight && panelEditor) {
    let startX = 0;
    let startWidth = 480;

    const onRightMove = (e) => {
      const delta = startX - e.clientX; // Dragging left widens the right panel
      const wsWidth = document.querySelector('.ws-main')?.getBoundingClientRect().width || window.innerWidth;
      const leftW = (!panelSidebar || panelSidebar.classList.contains('collapsed')) ? 0 : panelSidebar.getBoundingClientRect().width;
      const maxAllowed = Math.max(320, wsWidth - leftW - 340); // Keep at least 340px for chat
      const newWidth = Math.min(Math.max(startWidth + delta, 320), Math.min(850, maxAllowed));

      panelEditor.style.width = `${newWidth}px`;
      layoutPrefs.rightWidth = newWidth;
      resizeHandleRight.setAttribute('aria-valuenow', Math.round(newWidth));
    };

    const onRightUp = () => {
      document.body.classList.remove('resizing-active');
      resizeHandleRight.classList.remove('active-resizing');
      window.removeEventListener('pointermove', onRightMove);
      window.removeEventListener('pointerup', onRightUp);
      saveLayoutPrefs();
    };

    resizeHandleRight.addEventListener('pointerdown', (e) => {
      if (e.button !== 0) return;
      startX = e.clientX;
      startWidth = panelEditor.getBoundingClientRect().width;
      document.body.classList.add('resizing-active');
      resizeHandleRight.classList.add('active-resizing');
      window.addEventListener('pointermove', onRightMove);
      window.addEventListener('pointerup', onRightUp);
    });

    // Keyboard support for Right Handle
    resizeHandleRight.addEventListener('keydown', (e) => {
      const step = e.shiftKey ? 30 : 15;
      let curr = panelEditor.getBoundingClientRect().width;
      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        const next = Math.min(850, curr + step);
        panelEditor.style.width = `${next}px`;
        layoutPrefs.rightWidth = next;
        resizeHandleRight.setAttribute('aria-valuenow', Math.round(next));
        saveLayoutPrefs();
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        const next = Math.max(320, curr - step);
        panelEditor.style.width = `${next}px`;
        layoutPrefs.rightWidth = next;
        resizeHandleRight.setAttribute('aria-valuenow', Math.round(next));
        saveLayoutPrefs();
      }
    });
  }

  // Sidebar Collapse / Expand Actions
  if (btnCollapseSidebar && panelSidebar) {
    btnCollapseSidebar.addEventListener('click', () => {
      panelSidebar.classList.add('collapsed');
      if (resizeHandleLeft) resizeHandleLeft.classList.add('hidden-handle');
      if (btnExpandSidebar) btnExpandSidebar.style.display = 'inline-flex';
      layoutPrefs.leftCollapsed = true;
      saveLayoutPrefs();
    });
  }

  if (btnExpandSidebar && panelSidebar) {
    btnExpandSidebar.addEventListener('click', () => {
      panelSidebar.classList.remove('collapsed');
      if (resizeHandleLeft) resizeHandleLeft.classList.remove('hidden-handle');
      btnExpandSidebar.style.display = 'none';
      const lw = Math.min(Math.max(layoutPrefs.leftWidth || 270, 210), 450);
      panelSidebar.style.width = `${lw}px`;
      layoutPrefs.leftCollapsed = false;
      saveLayoutPrefs();
    });
  }

  // Right Draft Panel Collapse / Expand Actions
  if (btnToggleDraftPanel && panelEditor) {
    btnToggleDraftPanel.addEventListener('click', () => {
      const isNowCollapsed = panelEditor.classList.toggle('collapsed');
      if (resizeHandleRight) {
        if (isNowCollapsed) resizeHandleRight.classList.add('hidden-handle');
        else resizeHandleRight.classList.remove('hidden-handle');
      }
      if (!isNowCollapsed) {
        const rw = Math.min(Math.max(layoutPrefs.rightWidth || 480, 320), 850);
        panelEditor.style.width = `${rw}px`;
      }
      layoutPrefs.rightCollapsed = isNowCollapsed;
      updateDraftPanelButtonState(!isNowCollapsed);
      saveLayoutPrefs();
    });
  }

  if (btnCloseDraftPanel && panelEditor) {
    btnCloseDraftPanel.addEventListener('click', () => {
      panelEditor.classList.add('collapsed');
      if (resizeHandleRight) resizeHandleRight.classList.add('hidden-handle');
      layoutPrefs.rightCollapsed = true;
      updateDraftPanelButtonState(false);
      saveLayoutPrefs();
    });
  }

  if (btnExpandDraft && panelEditor) {
    btnExpandDraft.addEventListener('click', () => {
      const isExpanded = panelEditor.classList.toggle('expanded');
      btnExpandDraft.title = isExpanded ? 'Standard side view' : 'Toggle wide view';
      btnExpandDraft.setAttribute('aria-label', isExpanded ? 'Standard side view' : 'Toggle wide view');
      if (isExpanded) {
        panelEditor.style.width = '700px';
        layoutPrefs.rightWidth = 700;
      } else {
        panelEditor.style.width = '480px';
        layoutPrefs.rightWidth = 480;
      }
      saveLayoutPrefs();
    });
  }

  // -------------------------------------------------------------------------
  // Demo Library Modal & Retrieval
  // -------------------------------------------------------------------------
  async function openDemoLibraryModal() {
    if (!demoLibraryModal) return;
    demoLibraryModal.classList.add('active');
    if (demoLibraryList) demoLibraryList.innerHTML = '<div class="empty-sidebar-note" style="padding:1rem;">Loading saved drafts...</div>';

    try {
      const res = await fetch('/api/drafts');
      if (!res.ok) throw new Error('Could not load demo library');
      const data = await res.json();
      const drafts = data.drafts || [];

      if (drafts.length === 0) {
        demoLibraryList.innerHTML = `
          <div class="empty-sidebar-note" style="padding: 2rem 1rem; text-align: center;">
            No drafts have been saved to your demo library yet.<br>
            Generate an article in chat, approve it, and click <strong>Save to Demo Library</strong>.
          </div>
        `;
        return;
      }

      demoLibraryList.innerHTML = '';
      drafts.forEach(d => {
        const item = document.createElement('div');
        item.className = 'library-item';
        const isPub = d.status === 'published';
        const updatedDate = d.updated_at ? new Date(d.updated_at).toLocaleDateString() : 'Recent';
        item.innerHTML = `
          <div class="library-item-content">
            <div class="library-item-title" title="${escapeHtml(d.title)}">${escapeHtml(d.title || 'Untitled Draft')}</div>
            <div class="library-item-meta">
              <span>${d.word_count || 0} words</span>
              <span>Updated: ${updatedDate}</span>
              <span class="library-badge ${isPub ? 'published' : 'draft'}">
                ${isPub ? 'Demo Library' : 'Draft'}
              </span>
            </div>
          </div>
          <div class="library-item-action">
            <button type="button" class="btn btn-secondary btn-sm" style="padding: 0.35rem 0.75rem;">Load &rarr;</button>
          </div>
        `;

        item.addEventListener('click', async () => {
          try {
            const draftRes = await fetch(`/api/draft/${d.id}`);
            if (draftRes.ok) {
              const draftData = await draftRes.json();
              if (draftData.draft) {
                renderDraftData(draftData.draft);
                if (panelEditor) {
                  panelEditor.classList.remove('collapsed');
                  if (resizeHandleRight) resizeHandleRight.classList.remove('hidden-handle');
                  layoutPrefs.rightCollapsed = false;
                  updateDraftPanelButtonState(true, draftData.draft);
                  saveLayoutPrefs();
                }
                closeDemoLibraryModal();
                window.DataForgeAPI.showToast(`Loaded '${d.title}' into editor.`, 'info');
              }
            }
          } catch (err) {
            window.DataForgeAPI.showToast('Could not load draft: ' + err.message, 'warning');
          }
        });

        demoLibraryList.appendChild(item);
      });
    } catch (err) {
      if (demoLibraryList) demoLibraryList.innerHTML = `<div class="field-error visible" style="padding:1rem;">Error loading demo library: ${escapeHtml(err.message)}</div>`;
    }
  }

  function closeDemoLibraryModal() {
    if (demoLibraryModal) demoLibraryModal.classList.remove('active');
  }

  if (btnDemoLibrary) btnDemoLibrary.addEventListener('click', openDemoLibraryModal);
  if (modalLibraryClose) modalLibraryClose.addEventListener('click', closeDemoLibraryModal);
  if (modalLibraryDismiss) modalLibraryDismiss.addEventListener('click', closeDemoLibraryModal);

  // Apply layout preferences on page load
  applyLayoutPrefs();

  // -------------------------------------------------------------------------
  // 2. Competitors Management (SQLite)
  // -------------------------------------------------------------------------
  async function loadCompetitors() {
    try {
      const res = await fetch('/api/competitors');
      if (!res.ok) return;
      const data = await res.json();

      if (sidebarCompetitorsList) {
        if (!data.competitors || data.competitors.length === 0) {
          sidebarCompetitorsList.innerHTML = `
            <li class="empty-sidebar-note">
              No competitors added yet. Click <strong>+ Add</strong> above to track competitor URLs.
            </li>
          `;
          return;
        }

        sidebarCompetitorsList.innerHTML = '';
        data.competitors.forEach(comp => {
          const li = document.createElement('li');
          li.className = 'competitor-item';
          li.innerHTML = `
            <div>
              <div class="competitor-name">${escapeHtml(comp.name)}</div>
              <a href="${escapeHtml(comp.website_url)}" target="_blank" rel="noopener noreferrer" class="competitor-url" title="${escapeHtml(comp.website_url)}">
                ${escapeHtml(comp.website_url.replace(/^https?:\/\//i, ''))}
              </a>
            </div>
            <div class="competitor-actions">
              <button type="button" class="comp-btn edit" data-id="${comp.id}" title="Edit competitor">
                <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path></svg>
              </button>
              <button type="button" class="comp-btn delete" data-id="${comp.id}" title="Delete competitor">
                <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
              </button>
            </div>
          `;
          sidebarCompetitorsList.appendChild(li);
        });

        // Event listeners
        sidebarCompetitorsList.querySelectorAll('.comp-btn.edit').forEach(btn => {
          btn.addEventListener('click', () => {
            const id = btn.getAttribute('data-id');
            const comp = data.competitors.find(c => String(c.id) === String(id));
            if (comp) openCompetitorModal(comp);
          });
        });

        sidebarCompetitorsList.querySelectorAll('.comp-btn.delete').forEach(btn => {
          btn.addEventListener('click', async () => {
            const id = btn.getAttribute('data-id');
            if (confirm('Are you sure you want to remove this competitor?')) {
              await deleteCompetitor(id);
            }
          });
        });
      }
    } catch (err) {
      console.error('Failed to load competitors:', err);
    }
  }

  function openCompetitorModal(comp = null) {
    if (!competitorModal) return;
    competitorForm.reset();
    clearCompErrors();

    if (comp) {
      modalCompTitle.textContent = 'Edit Competitor';
      compIdInput.value = comp.id;
      compNameInput.value = comp.name;
      compUrlInput.value = comp.website_url;
      compNotesInput.value = comp.notes || '';
    } else {
      modalCompTitle.textContent = 'Add Competitor';
      compIdInput.value = '';
    }

    competitorModal.classList.add('active');
    compNameInput.focus();
  }

  function closeCompetitorModal() {
    if (competitorModal) {
      competitorModal.classList.remove('active');
      competitorForm.reset();
      clearCompErrors();
    }
  }

  function clearCompErrors() {
    compNameInput.classList.remove('is-invalid');
    compUrlInput.classList.remove('is-invalid');
    const errName = document.getElementById('err-comp-name');
    const errUrl = document.getElementById('err-comp-url');
    if (errName) { errName.textContent = ''; errName.classList.remove('visible'); }
    if (errUrl) { errUrl.textContent = ''; errUrl.classList.remove('visible'); }
  }

  async function handleCompetitorSubmit(e) {
    e.preventDefault();
    clearCompErrors();

    const id = compIdInput.value;
    const payload = {
      name: compNameInput.value.trim(),
      website_url: compUrlInput.value.trim(),
      notes: compNotesInput.value.trim()
    };

    const isEdit = Boolean(id);
    const url = isEdit ? `/api/competitors/${id}` : '/api/competitors';
    const method = isEdit ? 'PUT' : 'POST';

    try {
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (!res.ok) {
        if (data.details) {
          if (data.details.name) {
            compNameInput.classList.add('is-invalid');
            const el = document.getElementById('err-comp-name');
            if (el) { el.textContent = data.details.name; el.classList.add('visible'); }
          }
          if (data.details.website_url) {
            compUrlInput.classList.add('is-invalid');
            const el = document.getElementById('err-comp-url');
            if (el) { el.textContent = data.details.website_url; el.classList.add('visible'); }
          }
        }
        window.DataForgeAPI.showToast(data.error || 'Failed to save competitor', 'warning');
        return;
      }

      window.DataForgeAPI.showToast(isEdit ? 'Competitor updated successfully.' : 'Competitor added successfully.', 'info');
      closeCompetitorModal();
      loadCompetitors();
    } catch (err) {
      window.DataForgeAPI.showToast('Network error: ' + err.message, 'warning');
    }
  }

  async function deleteCompetitor(id) {
    try {
      const res = await fetch(`/api/competitors/${id}`, { method: 'DELETE' });
      if (res.ok) {
        window.DataForgeAPI.showToast('Competitor removed.', 'info');
        loadCompetitors();
      } else {
        window.DataForgeAPI.showToast('Failed to remove competitor.', 'warning');
      }
    } catch (err) {
      window.DataForgeAPI.showToast('Error removing competitor: ' + err.message, 'warning');
    }
  }

  if (btnOpenCompModal) btnOpenCompModal.addEventListener('click', () => openCompetitorModal());
  if (btnCloseCompModal) btnCloseCompModal.addEventListener('click', closeCompetitorModal);
  if (btnCancelCompModal) btnCancelCompModal.addEventListener('click', closeCompetitorModal);
  if (competitorForm) competitorForm.addEventListener('submit', handleCompetitorSubmit);

  // -------------------------------------------------------------------------
  // 3. Draft Rendering & Metrics
  // -------------------------------------------------------------------------
  function calculateWordCount(text) {
    const clean = text.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
    return clean ? clean.split(' ').filter(Boolean).length : 0;
  }

  function updateMetrics() {
    let text = isEditingRaw && rawEditor ? rawEditor.value : (articleBody ? articleBody.innerText || '' : '');
    const words = calculateWordCount(text);
    const mins = Math.max(1, Math.ceil(words / 200));

    if (wordCountEl) wordCountEl.textContent = words.toLocaleString();
    if (readTimeEl) readTimeEl.textContent = `${mins} min read`;
  }

  function renderDraftData(draft) {
    if (!draft) return;
    activeDraftId = draft.id;
    currentDraftVersion = draft.version || 1;

    if (draftTitleInput) draftTitleInput.value = draft.title || '';
    if (articleBody) {
      if (window.DataForgeAPI && window.DataForgeAPI.renderMarkdown) {
        articleBody.innerHTML = window.DataForgeAPI.renderMarkdown(draft.content_markdown || '', draft.title || '');
      } else {
        articleBody.innerHTML = draft.content_markdown || '';
      }
    }
    if (rawEditor) rawEditor.value = draft.content_markdown || '';

    // Update status badge
    updateDraftStatusBadge(draft.status, draft.version);
    showDraftView();

    // Ensure blog side panel is open and visible
    if (panelEditor) {
      panelEditor.classList.remove('collapsed');
    }
    updateDraftPanelButtonState(true, draft);
  }

  function updateDraftStatusBadge(status, version) {
    if (!draftStatusBadge) return;
    const s = (status || 'draft').toLowerCase();
    const ver = version || currentDraftVersion || 1;

    if (s === 'approved') {
      isDraftApproved = true;
      draftStatusBadge.style.background = '#D1FAE5';
      draftStatusBadge.style.color = '#065F46';
      draftStatusBadge.textContent = `Approved (v${ver})`;
      draftStatusBadge.title = `Draft version ${ver} approved. Ready to publish to Content Crew Blogs library.`;
      if (btnPublish) {
        btnPublish.classList.remove('disabled');
        btnPublish.removeAttribute('aria-disabled');
        btnPublish.textContent = 'Publish';
        btnPublish.title = 'Publish approved draft to your Content Crew Blogs library';
      }
    } else if (s === 'published') {
      isDraftApproved = true;
      draftStatusBadge.style.background = '#DBEAFE';
      draftStatusBadge.style.color = '#1E40AF';
      draftStatusBadge.textContent = `Published (v${ver})`;
      draftStatusBadge.title = 'Published to your Content Crew Blogs library.';
      if (btnPublish) {
        btnPublish.classList.add('disabled');
        btnPublish.setAttribute('aria-disabled', 'true');
        btnPublish.textContent = 'Published';
        btnPublish.title = 'Article is published in Content Crew Blogs library';
      }
    } else {
      isDraftApproved = false;
      draftStatusBadge.style.background = '#E2F3EB';
      draftStatusBadge.style.color = '#0F6938';
      draftStatusBadge.textContent = `Draft (v${ver})`;
      draftStatusBadge.title = `Draft version ${ver}. Requires editorial approval before publishing.`;
      if (btnPublish) {
        btnPublish.classList.add('disabled');
        btnPublish.setAttribute('aria-disabled', 'true');
        btnPublish.textContent = 'Publish';
        btnPublish.title = 'Approval required before publishing';
      }
    }
  }

  async function loadDraft() {
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const reqDraftId = urlParams.get('draft_id');
      const targetUrl = reqDraftId ? `/api/draft/${reqDraftId}` : '/api/draft';

      const res = await fetch(targetUrl);
      if (!res.ok) return;
      const data = await res.json();
      if (data.draft) {
        renderDraftData(data.draft);
      } else {
        hideDraftView();
        updateDraftPanelButtonState(false, null);
      }
    } catch (err) {
      console.error('Failed to load draft:', err);
    }
  }

  async function saveDraftToBackend(status = 'draft') {
    const title = draftTitleInput ? draftTitleInput.value.trim() : 'Untitled Draft';
    const content = isEditingRaw && rawEditor ? rawEditor.value : (articleBody ? articleBody.innerHTML : '');

    try {
      const res = await fetch('/api/draft', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: activeDraftId,
          title,
          content_markdown: content,
          status
        })
      });

      const data = await res.json();
      if (res.ok && data.draft) {
        activeDraftId = data.draft.id;
        updateDraftStatusBadge(data.draft.status);
        window.DataForgeAPI.showToast('Draft saved successfully.', 'info');
        updateMetrics();
      }
    } catch (err) {
      window.DataForgeAPI.showToast('Network error saving draft: ' + err.message, 'warning');
    }
  }

  function showDraftView() {
    if (emptyDraftView) emptyDraftView.style.display = 'none';
    if (populatedDraftView) populatedDraftView.classList.add('active');
    updateMetrics();
  }

  function hideDraftView() {
    if (populatedDraftView) populatedDraftView.classList.remove('active');
    if (emptyDraftView) emptyDraftView.style.display = 'flex';
  }

  if (btnLoadSample) {
    btnLoadSample.addEventListener('click', () => {
      showDraftView();
      saveDraftToBackend('draft');
    });
  }

  if (btnToggleEdit && rawEditor && articleBody) {
    btnToggleEdit.addEventListener('click', () => {
      isEditingRaw = !isEditingRaw;
      if (isEditingRaw) {
        articleBody.style.display = 'none';
        rawEditor.style.display = 'block';
        btnToggleEdit.textContent = 'Preview Mode';
        btnToggleEdit.classList.remove('btn-secondary');
        btnToggleEdit.classList.add('btn-dark');
        rawEditor.focus();
      } else {
        if (window.DataForgeAPI && window.DataForgeAPI.renderMarkdown) {
          articleBody.innerHTML = window.DataForgeAPI.renderMarkdown(rawEditor.value, draftTitleInput ? draftTitleInput.value : '');
        } else {
          articleBody.innerHTML = rawEditor.value;
        }
        rawEditor.style.display = 'none';
        articleBody.style.display = 'block';
        btnToggleEdit.textContent = 'Edit Mode';
        btnToggleEdit.classList.remove('btn-dark');
        btnToggleEdit.classList.add('btn-secondary');
        // Manual edit invalidates previous approval
        saveDraftToBackend('draft');
      }
      updateMetrics();
    });

    rawEditor.addEventListener('input', updateMetrics);
    articleBody.addEventListener('input', updateMetrics);
  }

  if (btnSaveDraft) {
    btnSaveDraft.addEventListener('click', () => saveDraftToBackend('draft'));
  }

  // -------------------------------------------------------------------------
  // 4. Approval & Publishing Actions (In-App Blogs Library)
  // -------------------------------------------------------------------------
  if (btnApprove) {
    btnApprove.addEventListener('click', async () => {
      const sess = activeSessionId || 'default';
      try {
        const res = await fetch(`/api/workflow/${encodeURIComponent(sess)}/approve`, { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
          updateDraftStatusBadge('approved', data.approval.version);
          window.DataForgeAPI.showToast(`Draft version ${data.approval.version} approved! Ready to publish to Content Crew Blogs library.`, 'info');
        } else {
          window.DataForgeAPI.showToast(data.error || 'Approval failed.', 'warning');
        }
      } catch (err) {
        window.DataForgeAPI.showToast('Approval error: ' + err.message, 'warning');
      }
    });
  }

  if (btnPublish) {
    btnPublish.addEventListener('click', async (e) => {
      e.preventDefault();
      if (!isDraftApproved) {
        window.DataForgeAPI.showToast('Please approve the current draft version before publishing.', 'warning');
        return;
      }

      const sess = activeSessionId || 'default';
      try {
        const res = await fetch(`/api/workflow/${encodeURIComponent(sess)}/publish`, { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
          updateDraftStatusBadge('published');
          window.DataForgeAPI.showToast(data.message || 'Published to your Content Crew Blogs library.', 'info');
        } else {
          window.DataForgeAPI.showToast(data.error || 'Could not publish draft.', 'warning');
        }
      } catch (err) {
        window.DataForgeAPI.showToast('Error publishing draft: ' + err.message, 'warning');
      }
    });
  }

  // -------------------------------------------------------------------------
  // Regenerate Article Feature
  // -------------------------------------------------------------------------
  if (btnRegenerate) {
    btnRegenerate.addEventListener('click', () => {
      if (regenModal) regenModal.classList.add('active');
    });
  }

  function closeRegenModal() {
    if (regenModal) regenModal.classList.remove('active');
  }

  if (btnRegenCancel) btnRegenCancel.addEventListener('click', closeRegenModal);
  if (btnRegenClose) btnRegenClose.addEventListener('click', closeRegenModal);
  if (regenModal) {
    regenModal.addEventListener('click', (e) => {
      if (e.target === regenModal) closeRegenModal();
    });
  }

  if (btnRegenConfirm) {
    btnRegenConfirm.addEventListener('click', async () => {
      closeRegenModal();
      appendChatMessage('user', 'Regenerate Article: Produce fresh version using current context and approved research.');
      const tempId = 'regen_' + Date.now();
      const progressBubble = createWorkflowProgressBubble(tempId, 'Regenerating Article');

      const sess = activeSessionId || 'default';
      try {
        const res = await fetch(`/api/workflow/${encodeURIComponent(sess)}/regenerate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();

        if (res.ok && data.workflow && data.workflow.draft) {
          if (progressBubble) {
            updateWorkflowTimelineUI(tempId, data.events || [], true, false);
          }
          renderDraftData(data.workflow.draft);
          appendChatMessage('assistant', `Draft regenerated to Version ${data.workflow.draft.version}. Previous approvals invalidated. Ready for review.`);
          window.DataForgeAPI.showToast(`Draft regenerated to Version ${data.workflow.draft.version}.`, 'info');
        } else {
          if (progressBubble) progressBubble.remove();
          appendChatMessage('assistant', data.error || 'Regeneration could not be completed.');
          window.DataForgeAPI.showToast(data.error || 'Regeneration failed.', 'warning');
        }
      } catch (err) {
        if (progressBubble) progressBubble.remove();
        appendChatMessage('assistant', 'Regeneration network notice: ' + err.message);
      }
    });
  }

  // -------------------------------------------------------------------------
  // Customize Workspace Logic & Density Preferences
  // -------------------------------------------------------------------------
  const PREFS_STORAGE_KEY = 'dataforge_workspace_layout_prefs';

  function applyDensity(density) {
    if (density === 'compact') {
      document.body.classList.add('workspace-density-compact');
    } else {
      document.body.classList.remove('workspace-density-compact');
    }
  }

  function loadWorkspacePreferences() {
    try {
      const saved = localStorage.getItem(PREFS_STORAGE_KEY);
      if (!saved) return;
      const prefs = JSON.parse(saved);

      if (prefs.sidebarCollapsed !== undefined) {
        if (panelSidebar) {
          panelSidebar.classList.toggle('collapsed', prefs.sidebarCollapsed);
          if (btnExpandSidebar) btnExpandSidebar.style.display = prefs.sidebarCollapsed ? 'inline-flex' : 'none';
        }
        if (prefShowSidebar) prefShowSidebar.checked = !prefs.sidebarCollapsed;
      }

      if (prefs.editorCollapsed !== undefined) {
        if (panelEditor) panelEditor.classList.toggle('collapsed', prefs.editorCollapsed);
        if (prefShowDraft) prefShowDraft.checked = !prefs.editorCollapsed;
      }

      if (prefs.sidebarWidth && panelSidebar) {
        panelSidebar.style.width = `${prefs.sidebarWidth}px`;
      }
      if (prefs.editorWidth && panelEditor) {
        panelEditor.style.width = `${prefs.editorWidth}px`;
      }

      if (prefs.density) {
        applyDensity(prefs.density);
        if (prefs.density === 'compact') {
          if (prefDensityCompact) prefDensityCompact.checked = true;
        } else {
          if (prefDensityComfortable) prefDensityComfortable.checked = true;
        }
      }
    } catch (e) {
      console.warn('Could not load layout preferences:', e);
    }
  }

  function saveWorkspacePreferences() {
    try {
      const density = prefDensityCompact && prefDensityCompact.checked ? 'compact' : 'comfortable';
      applyDensity(density);

      const prefs = {
        sidebarCollapsed: panelSidebar ? panelSidebar.classList.contains('collapsed') : false,
        editorCollapsed: panelEditor ? panelEditor.classList.contains('collapsed') : false,
        sidebarWidth: panelSidebar ? parseInt(panelSidebar.style.width, 10) || 270 : 270,
        editorWidth: panelEditor ? parseInt(panelEditor.style.width, 10) || 460 : 460,
        density
      };
      localStorage.setItem(PREFS_STORAGE_KEY, JSON.stringify(prefs));
    } catch (e) {
      console.warn('Could not save workspace preferences:', e);
    }
  }

  if (btnCustomizeWorkspace) {
    btnCustomizeWorkspace.addEventListener('click', () => {
      if (prefShowSidebar && panelSidebar) {
        prefShowSidebar.checked = !panelSidebar.classList.contains('collapsed');
      }
      if (prefShowDraft && panelEditor) {
        prefShowDraft.checked = !panelEditor.classList.contains('collapsed');
      }
      if (customizeModal) customizeModal.classList.add('active');
    });
  }

  function closeCustomizeModal() {
    if (customizeModal) customizeModal.classList.remove('active');
  }

  if (btnCustomizeClose) btnCustomizeClose.addEventListener('click', closeCustomizeModal);
  if (btnCustomizeSave) {
    btnCustomizeSave.addEventListener('click', () => {
      if (panelSidebar && prefShowSidebar) {
        const shouldShow = prefShowSidebar.checked;
        panelSidebar.classList.toggle('collapsed', !shouldShow);
        if (btnExpandSidebar) btnExpandSidebar.style.display = shouldShow ? 'none' : 'inline-flex';
      }
      if (panelEditor && prefShowDraft) {
        const shouldShow = prefShowDraft.checked;
        panelEditor.classList.toggle('collapsed', !shouldShow);
        updateDraftPanelButtonState(shouldShow, null);
      }
      saveWorkspacePreferences();
      closeCustomizeModal();
      window.DataForgeAPI.showToast('Workspace preferences saved.', 'info');
    });
  }

  if (btnResetLayout) {
    btnResetLayout.addEventListener('click', () => {
      if (panelSidebar) {
        panelSidebar.classList.remove('collapsed');
        panelSidebar.style.width = '270px';
      }
      if (panelEditor) {
        panelEditor.classList.remove('collapsed');
        panelEditor.style.width = '460px';
      }
      if (btnExpandSidebar) btnExpandSidebar.style.display = 'none';
      if (prefShowSidebar) prefShowSidebar.checked = true;
      if (prefShowDraft) prefShowDraft.checked = true;
      if (prefDensityComfortable) prefDensityComfortable.checked = true;
      applyDensity('comfortable');
      saveWorkspacePreferences();
      closeCustomizeModal();
      window.DataForgeAPI.showToast('Workspace layout reset to defaults.', 'info');
    });
  }

  // -------------------------------------------------------------------------
  // 5. Chat & LangGraph Multi-Agent Pipeline with Real-time Event Tracking
  // -------------------------------------------------------------------------
  function appendChatMessage(role, content) {
    if (!chatMessages) return null;

    const bubble = document.createElement('div');
    bubble.className = `message-bubble ${role === 'user' ? 'user' : 'assistant'}`;

    const header = document.createElement('div');
    header.className = 'message-header';
    header.textContent = role === 'user' ? 'You' : 'Content Crew';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;

    bubble.appendChild(header);
    bubble.appendChild(contentDiv);
    chatMessages.appendChild(bubble);

    chatMessages.scrollTop = chatMessages.scrollHeight;
    return bubble;
  }

  function createWorkflowProgressBubble(runId, userRequestText) {
    if (!chatMessages) return null;

    const bubble = document.createElement('div');
    bubble.className = 'workflow-progress-bubble';
    bubble.id = `workflow-run-${runId}`;

    bubble.innerHTML = `
      <div class="workflow-progress-header">
        <div class="workflow-progress-title-box">
          <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
          </svg>
          <span class="workflow-progress-title">Agent Workflow Progress</span>
        </div>
        <span class="workflow-status-badge running" id="wf-badge-${runId}">Running</span>
      </div>
      <div class="workflow-stages-list" id="wf-stages-${runId}">
        <div style="font-size:0.775rem; color:var(--color-muted-gray);">Initializing pipeline stages...</div>
      </div>
    `;

    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return bubble;
  }

  function updateWorkflowTimelineUI(runId, events, isCompleted, isFailed) {
    const listEl = document.getElementById(`wf-stages-${runId}`);
    const badgeEl = document.getElementById(`wf-badge-${runId}`);

    if (badgeEl) {
      if (isCompleted) {
        badgeEl.className = 'workflow-status-badge completed';
        badgeEl.textContent = 'Completed';
      } else if (isFailed) {
        badgeEl.className = 'workflow-status-badge failed';
        badgeEl.textContent = 'Failed';
      } else {
        badgeEl.className = 'workflow-status-badge running';
        badgeEl.textContent = 'Running';
      }
    }

    if (!listEl || !events || events.length === 0) return;

    listEl.innerHTML = '';
    events.forEach(ev => {
      const item = document.createElement('div');
      item.className = 'stage-item';

      let iconHtml = '';
      if (ev.status === 'completed') {
        iconHtml = `<svg class="stage-icon completed" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"></path></svg>`;
      } else if (ev.status === 'in_progress') {
        iconHtml = `<svg class="stage-icon in_progress" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-linecap="round"></circle></svg>`;
      } else if (ev.status === 'failed') {
        iconHtml = `<svg class="stage-icon failed" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`;
      } else {
        iconHtml = `<svg class="stage-icon pending" width="14" height="14" fill="currentColor" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"></circle></svg>`;
      }

      const durText = ev.duration_ms ? `${(ev.duration_ms / 1000).toFixed(1)}s` : '';

      // Stage details formatting (specifically Stage 3 & 4 Search / Evidence)
      let detailsHtml = '';
      const d = ev.details || {};
      if (ev.stage_id === 'stage_3_search') {
        if (d.sources && d.sources.length > 0) {
          detailsHtml = `
            <div class="search-activity-box">
              <div class="search-query-line">
                <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                <span>Query: "${escapeHtml(d.query || '')}"</span> &bull; 
                <span>${d.count || d.sources.length} sources retrieved</span>
              </div>
              <div class="search-results-list">
                ${d.sources.map(s => `
                  <div class="search-source-item">
                    <span class="search-source-title">
                      <a href="${escapeHtml(s.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(s.title || 'Source Citation')}</a>
                    </span>
                    <span class="search-source-snippet">${escapeHtml(s.snippet || '')}</span>
                  </div>
                `).join('')}
              </div>
            </div>
          `;
        } else if (d.notice) {
          detailsHtml = `
            <div class="search-unconfigured-notice">
              ${escapeHtml(d.notice)}
            </div>
          `;
        }
      }

      item.innerHTML = `
        <div class="stage-icon-box">${iconHtml}</div>
        <div class="stage-content">
          <div class="stage-header-line">
            <span class="stage-label">${escapeHtml(ev.label)}</span>
            <span class="stage-duration">${durText}</span>
          </div>
          <div class="stage-desc">${escapeHtml(ev.description)}</div>
          ${detailsHtml}
        </div>
      `;

      listEl.appendChild(item);
    });

    if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // -------------------------------------------------------------------------
  // Welcome Screen, Session Isolation & History Controls
  // -------------------------------------------------------------------------
  function renderWelcomeScreen() {
    if (!chatMessages) return;
    chatMessages.innerHTML = `
      <div class="welcome-screen-card" id="welcome-screen-card">
        <div class="welcome-header-box">
          <div class="welcome-icon" aria-hidden="true">
            <svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15"></path>
            </svg>
          </div>
          <h2 class="welcome-title">What would you like to write about?</h2>
        </div>
        <p class="welcome-desc">
          Enter a topic, ask a question, or pick an industry angle below. The DataForge Content Crew will research competitor gaps, build a structured outline, and generate a publication-ready draft.
        </p>

        <div class="prompt-chips-container" id="prompt-chips-box">
          <div class="chips-label">Suggested topics to explore:</div>
          <div class="prompt-chips">
            <button type="button" class="prompt-chip" data-prompt="Explain how agentic AI is changing customer support">
              &ldquo;Explain how agentic AI is changing customer support&rdquo;
            </button>
            <button type="button" class="prompt-chip" data-prompt="Enterprise guide to LLM evaluation and observability">
              &ldquo;Enterprise guide to LLM evaluation and observability&rdquo;
            </button>
            <button type="button" class="prompt-chip" data-prompt="Autonomous multi-agent workflows for B2B SaaS">
              &ldquo;Autonomous multi-agent workflows for B2B SaaS&rdquo;
            </button>
            <button type="button" class="prompt-chip" data-prompt="Comparing open-source and proprietary foundation models">
              &ldquo;Comparing open-source and proprietary foundation models&rdquo;
            </button>
          </div>
        </div>
      </div>
    `;
    bindPromptChips();
    if (chatInput) {
      chatInput.placeholder = "e.g. Explain how agentic AI is changing customer support";
    }
    if (chatSessionBadge) {
      chatSessionBadge.textContent = "New conversation";
    }
  }

  function bindPromptChips() {
    const chips = document.querySelectorAll('.prompt-chip');
    chips.forEach(chip => {
      chip.addEventListener('click', () => {
        const promptText = chip.getAttribute('data-prompt') || chip.textContent.trim().replace(/^“|”$/g, '');
        if (chatInput && promptText) {
          chatInput.value = promptText;
          chatInput.focus();
        }
      });
    });
  }

  function startNewChatSession() {
    activeSessionId = 'sess_' + Date.now().toString(36) + '_' + Math.random().toString(36).substring(2, 6);
    try {
      const url = new URL(window.location);
      url.searchParams.delete('session_id');
      url.searchParams.delete('new');
      window.history.replaceState({}, '', url.pathname);
    } catch (e) {}

    renderWelcomeScreen();
    hideDraftView();
    updateDraftPanelButtonState(false, null);
    activeDraftId = null;
    isDraftApproved = false;
    currentApprovedVersion = null;
    serverApprovalToken = null;

    closeHistoryModal();
    if (chatInput) {
      chatInput.value = '';
      chatInput.focus();
    }
    if (window.DataForgeAPI && window.DataForgeAPI.showToast) {
      window.DataForgeAPI.showToast('Started a fresh chat conversation.', 'info');
    }
  }

  async function openHistoryModal() {
    if (!chatHistoryModal) return;
    chatHistoryModal.classList.add('active');
    if (chatHistoryList) chatHistoryList.innerHTML = '<div class="empty-sidebar-note">Loading conversation history...</div>';

    try {
      const res = await fetch('/api/chat/sessions');
      if (!res.ok) throw new Error('Could not load chat sessions');
      const data = await res.json();
      const sessions = data.sessions || [];

      if (sessions.length === 0) {
        chatHistoryList.innerHTML = `
          <div class="empty-sidebar-note" style="padding: 1.5rem; text-align: center;">
            No past conversations recorded yet.<br>
            Send a message to start your first session.
          </div>
        `;
        return;
      }

      chatHistoryList.innerHTML = '';
      sessions.forEach(sess => {
        const item = document.createElement('div');
        item.className = 'history-item';
        const updatedDate = sess.updated_at ? new Date(sess.updated_at).toLocaleDateString(undefined, {
          month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
        }) : 'Recently';

        item.innerHTML = `
          <div class="history-item-content">
            <div class="history-item-title">${escapeHtml(sess.title || 'Conversation ' + sess.id.slice(0, 8))}</div>
            <div class="history-item-meta">Last updated: ${updatedDate}</div>
          </div>
          <button type="button" class="btn btn-secondary btn-sm" style="padding: 0.3rem 0.65rem;">
            Load &rarr;
          </button>
        `;

        item.addEventListener('click', () => {
          switchSession(sess.id, sess.title);
        });

        chatHistoryList.appendChild(item);
      });
    } catch (err) {
      if (chatHistoryList) chatHistoryList.innerHTML = `<div class="empty-sidebar-note">Error loading history: ${escapeHtml(err.message)}</div>`;
    }
  }

  function closeHistoryModal() {
    if (chatHistoryModal) chatHistoryModal.classList.remove('active');
  }

  async function switchSession(sessionId, title) {
    activeSessionId = sessionId;
    try {
      const url = new URL(window.location);
      url.searchParams.set('session_id', sessionId);
      window.history.pushState({}, '', url.toString());
    } catch (e) {}

    closeHistoryModal();
    if (chatSessionBadge) chatSessionBadge.textContent = title ? title.slice(0, 24) : 'Session ' + sessionId.slice(0, 8);
    await loadChatMessages();
    await loadDraft();
    if (window.DataForgeAPI && window.DataForgeAPI.showToast) {
      window.DataForgeAPI.showToast(`Loaded conversation: ${title || sessionId.slice(0, 8)}`, 'info');
    }
  }

  if (btnNewChat) btnNewChat.addEventListener('click', startNewChatSession);
  if (btnModalNewChat) btnModalNewChat.addEventListener('click', startNewChatSession);
  if (btnChatHistory) btnChatHistory.addEventListener('click', openHistoryModal);
  if (modalHistoryClose) modalHistoryClose.addEventListener('click', closeHistoryModal);
  if (modalHistoryDismiss) modalHistoryDismiss.addEventListener('click', closeHistoryModal);
  if (chatHistoryModal) {
    chatHistoryModal.addEventListener('click', (e) => {
      if (e.target === chatHistoryModal) closeHistoryModal();
    });
  }

  async function loadChatMessages() {
    if (!activeSessionId) return;
    try {
      const res = await fetch(`/api/chat/sessions/${encodeURIComponent(activeSessionId)}/messages`);
      if (!res.ok) return;
      const data = await res.json();

      if (data.messages && data.messages.length > 0) {
        if (chatMessages) chatMessages.innerHTML = '';
        data.messages.forEach(msg => {
          appendChatMessage(msg.role, msg.content);
        });
        if (chatSessionBadge) chatSessionBadge.textContent = "Conversation saved";
      } else {
        renderWelcomeScreen();
      }
    } catch (err) {
      console.error('Failed to load chat history:', err);
      renderWelcomeScreen();
    }
  }

  async function handleChatSubmit(messageText) {
    const text = messageText.trim();
    if (!text) return;

    // Remove welcome card if present
    const welcomeCard = document.getElementById('welcome-screen-card');
    if (welcomeCard) welcomeCard.remove();

    appendChatMessage('user', text);
    if (chatInput) chatInput.value = '';

    const tempRunId = 'run_' + Date.now();
    const progressBubble = createWorkflowProgressBubble(tempRunId, text);
    const sess = activeSessionId || 'default';

    try {
      const res = await fetch(`/api/chat/sessions/${encodeURIComponent(sess)}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, async: true })
      });
      const data = await res.json();

      if (res.status === 202 && data.run_id) {
        // Active background run started -> poll for genuine live events!
        if (progressBubble) progressBubble.id = `workflow-run-${data.run_id}`;
        const activeRunId = data.run_id;

        let pollInterval = setInterval(async () => {
          try {
            const statusRes = await fetch(`/api/workflow/${encodeURIComponent(sess)}/status?run_id=${encodeURIComponent(activeRunId)}`);
            if (!statusRes.ok) return;
            const statusData = await statusRes.json();
            const events = statusData.events || [];
            const isComplete = statusData.workflow && (statusData.workflow.status === 'review_pending' || statusData.workflow.status === 'completed');
            const isError = statusData.workflow && statusData.workflow.status === 'error';

            updateWorkflowTimelineUI(activeRunId, events, isComplete, isError);

            if (isComplete) {
              clearInterval(pollInterval);
              if (statusData.workflow.draft) {
                renderDraftData(statusData.workflow.draft);
                appendChatMessage('assistant', `Workflow complete! Initial draft generated for '${statusData.workflow.draft.title}' (${statusData.workflow.draft.word_count} words). Loaded in workspace editor.`);
                window.DataForgeAPI.showToast('New draft generated and loaded in editor.', 'info');
              }
            } else if (isError) {
              clearInterval(pollInterval);
              appendChatMessage('assistant', statusData.workflow.error || 'Workflow execution error.');
            }
          } catch (pollErr) {
            console.warn('Polling error:', pollErr);
          }
        }, 450);

        // Max poll limit 60 seconds
        setTimeout(() => clearInterval(pollInterval), 60000);

      } else if (res.ok && data.workflow) {
        // Synchronous completion
        if (progressBubble) {
          updateWorkflowTimelineUI(tempRunId, data.events || [], true, false);
        }
        if (data.assistant_message) {
          appendChatMessage('assistant', data.assistant_message.content);
        }
        if (data.workflow.draft) {
          renderDraftData(data.workflow.draft);
          window.DataForgeAPI.showToast('New draft generated and loaded in editor.', 'info');
        }
      } else {
        if (progressBubble) progressBubble.remove();
        appendChatMessage('assistant', data.error || 'Notice: Could not start workflow.');
      }
    } catch (err) {
      if (progressBubble) progressBubble.remove();
      appendChatMessage('assistant', 'Network notice: ' + err.message);
    }
  }

  if (chatForm && chatInput) {
    chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      handleChatSubmit(chatInput.value);
    });

    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
      }
    });
  }

  bindPromptChips();

  if (btnRequestRevision) {
    btnRequestRevision.addEventListener('click', async () => {
      const notes = prompt(
        'Enter revision instructions for your blog draft:',
        'Emphasize actionable multi-agent benefits and add concrete integration examples.'
      );
      if (!notes || !notes.trim()) return;

      appendChatMessage('user', `Revision request: ${notes}`);
      const prog = appendChatMessage('assistant', 'Applying targeted revisions to the draft...');
      const sess = activeSessionId || 'default';

      try {
        const res = await fetch(`/api/workflow/${encodeURIComponent(sess)}/revise`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ revision_notes: notes.trim() })
        });
        const data = await res.json();
        if (prog) prog.remove();

        if (res.ok && data.workflow && data.workflow.draft) {
          renderDraftData(data.workflow.draft);
          appendChatMessage('assistant', `Revision completed! Draft updated to Version ${data.workflow.draft.version}. Previous approvals invalidated.`);
          window.DataForgeAPI.showToast(`Draft revised to Version ${data.workflow.draft.version}.`, 'info');
        } else {
          appendChatMessage('assistant', data.error || 'Revision failed.');
        }
      } catch (err) {
        if (prog) prog.remove();
        appendChatMessage('assistant', 'Error applying revision: ' + err.message);
      }
    });
  }

  // -------------------------------------------------------------------------
  // 6. Mobile Tab Switcher
  // -------------------------------------------------------------------------
  mobileTabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.getAttribute('data-tab');
      mobileTabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      Object.entries(tabPanels).forEach(([name, el]) => {
        if (!el) return;
        if (name === target) {
          el.classList.add('active-tab-panel');
        } else {
          el.classList.remove('active-tab-panel');
        }
      });
    });
  });

  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Initial Session & Workspace Load
  const urlParams = new URLSearchParams(window.location.search);
  const isExplicitNew = urlParams.get('new') === '1';
  const paramSessionId = urlParams.get('session_id');
  const reqDraftId = urlParams.get('draft_id');

  if (paramSessionId && !isExplicitNew) {
    activeSessionId = paramSessionId;
  } else {
    activeSessionId = 'sess_' + Date.now().toString(36) + '_' + Math.random().toString(36).substring(2, 6);
  }

  loadWorkspacePreferences();
  loadCompanyProfile();
  loadCompetitors();

  if (paramSessionId && !isExplicitNew) {
    loadChatMessages();
    loadDraft();
  } else {
    renderWelcomeScreen();
    if (reqDraftId) {
      loadDraft();
    } else {
      hideDraftView();
      updateDraftPanelButtonState(false, null);
    }
  }
});
