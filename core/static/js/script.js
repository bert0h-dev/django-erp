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
}

if (userMenuButton && userMenuDropdown) {
  userMenuButton.addEventListener('click', (event) => {
    const isExpanded = userMenuButton.getAttribute('aria-expanded') === 'true';
    userMenuButton.setAttribute('aria-expanded', String(!isExpanded));
    userMenuDropdown.classList.toggle('hidden', isExpanded);
    event.stopPropagation();
  });
}

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
