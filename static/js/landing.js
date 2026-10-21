/**
 * DataForge Content Crew - Landing Page Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  // Update the backend connectivity indicator
  if (window.DataForgeAPI && window.DataForgeAPI.updateHealthIndicator) {
    window.DataForgeAPI.updateHealthIndicator('landing-health-indicator');
  }

  // Smooth scroll for in-page anchors
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (targetId && targetId !== '#') {
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
          e.preventDefault();
          targetElement.scrollIntoView({ behavior: 'smooth' });
        }
      }
    });
  });
});
