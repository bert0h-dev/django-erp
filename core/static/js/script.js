const hamburgerBtn = document.getElementById('hamburger-btn');
const mobileMenu = document.getElementById('mobile-menu');
const userMenuButton = document.getElementById('user-menu-button');
const userMenuDropdown = document.getElementById('user-menu-dropdown');

if (hamburgerBtn && mobileMenu) {
  hamburgerBtn.addEventListener('click', () => {
    const isExpanded = hamburgerBtn.getAttribute('aria-expanded') === 'true';
    hamburgerBtn.setAttribute('aria-expanded', String(!isExpanded));
    hamburgerBtn.setAttribute('aria-label', isExpanded ? 'Abrir menú' : 'Cerrar menú');
    mobileMenu.classList.toggle('hidden', isExpanded);
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && hamburgerBtn.getAttribute('aria-expanded') === 'true') {
      mobileMenu.classList.add('hidden');
      hamburgerBtn.setAttribute('aria-expanded', 'false');
      hamburgerBtn.setAttribute('aria-label', 'Abrir menú');
      hamburgerBtn.focus();
    }
  });
}

if (userMenuButton && userMenuDropdown) {
  userMenuButton.addEventListener('click', (event) => {
    const isExpanded = userMenuButton.getAttribute('aria-expanded') === 'true';
    userMenuButton.setAttribute('aria-expanded', String(!isExpanded));
    userMenuDropdown.classList.toggle('hidden', isExpanded);
    event.stopPropagation();
  });
}

if (userMenuButton && userMenuDropdown) {
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !userMenuDropdown.classList.contains('hidden')) {
      userMenuDropdown.classList.add('hidden');
      userMenuButton.setAttribute('aria-expanded', 'false');
      userMenuButton.focus();
    }
  });
}

document.querySelectorAll('form[data-loading-form]').forEach((form) => {
  form.addEventListener('submit', () => {
    const submitButton = form.querySelector('button[type="submit"]:not(:disabled)');
    if (!submitButton) {
      return;
    }

    const label = submitButton.querySelector('[data-submit-label]');
    const spinner = submitButton.querySelector('.ui-loading-spinner');
    submitButton.disabled = true;
    form.setAttribute('aria-busy', 'true');

    if (label) {
      label.textContent = submitButton.dataset.loadingLabel || 'Procesando...';
    }
    if (spinner) {
      spinner.hidden = false;
    }
  });
});

document.addEventListener('click', (event) => {
  if (userMenuButton && userMenuDropdown) {
    if (
      !userMenuButton.contains(event.target) &&
      !userMenuDropdown.contains(event.target)
    ) {
      userMenuDropdown.classList.add('hidden');
      userMenuButton.setAttribute('aria-expanded', 'false');
    }
  }
});
