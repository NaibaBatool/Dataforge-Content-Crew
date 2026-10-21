/**
 * DataForge Content Crew - Onboarding Form Logic
 * Phase 2: Company Profile Management
 */

document.addEventListener('DOMContentLoaded', async () => {
  const form = document.getElementById('onboarding-form');
  const saveBtn = document.getElementById('btn-save-profile');

  // Initialize Health Indicator
  if (window.DataForgeAPI && window.DataForgeAPI.updateHealthIndicator) {
    window.DataForgeAPI.updateHealthIndicator('onboarding-health-indicator');
  }

  // Pre-load existing profile if one is already saved
  try {
    const res = await fetch('/api/company-profile');
    if (res.ok) {
      const data = await res.json();
      if (data.profile) {
        Object.entries(data.profile).forEach(([key, val]) => {
          const input = document.getElementById(key);
          if (input && val !== null && val !== undefined) {
            input.value = val;
          }
        });
        if (saveBtn) {
          saveBtn.textContent = 'Update Company Profile';
        }
      }
    }
  } catch (err) {
    console.error('Error loading existing profile:', err);
  }

  // Clear errors on input
  form.querySelectorAll('.form-input, .form-textarea, .form-select').forEach(input => {
    input.addEventListener('input', () => {
      input.classList.remove('is-invalid');
      const errEl = document.getElementById(`err-${input.id}`);
      if (errEl) {
        errEl.textContent = '';
        errEl.classList.remove('visible');
      }
    });
  });

  // Handle Form Submission
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Collect data
    const formData = new FormData(form);
    const payload = {};
    formData.forEach((val, key) => {
      payload[key] = val.trim();
    });

    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.textContent = 'Saving...';
    }

    try {
      const response = await fetch('/api/company-profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      const result = await response.json();

      if (!response.ok) {
        // Display validation errors
        if (result.details) {
          Object.entries(result.details).forEach(([field, msg]) => {
            const input = document.getElementById(field);
            const errEl = document.getElementById(`err-${field}`);
            if (input) input.classList.add('is-invalid');
            if (errEl) {
              errEl.textContent = msg;
              errEl.classList.add('visible');
            }
          });
        }
        window.DataForgeAPI.showToast(result.error || 'Please correct the highlighted errors.', 'warning');
        return;
      }

      window.DataForgeAPI.showToast('Company profile saved successfully!', 'info');
      setTimeout(() => {
        window.location.href = '/workspace';
      }, 700);

    } catch (err) {
      window.DataForgeAPI.showToast('Failed to save profile: ' + err.message, 'warning');
    } finally {
      if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save Company Profile';
      }
    }
  });
});
