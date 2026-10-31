// Mostrar u ocultar la contraseña
const passwordInput = document.querySelector('[data-password-input]');
const passwordToggle = document.querySelector('[data-password-toggle]');

if (passwordInput && passwordToggle) {
  const eyeOpen = passwordToggle.querySelector('[data-eye-open]');
  const eyeClosed = passwordToggle.querySelector('[data-eye-closed]');

  passwordToggle.addEventListener('click', () => {
    const isVisible = passwordInput.type === 'text';
    passwordInput.type = isVisible ? 'password' : 'text';
    passwordToggle.setAttribute('aria-pressed', String(!isVisible));
    passwordToggle.setAttribute('aria-label', isVisible ? 'Mostrar contraseña' : 'Ocultar contraseña');
    eyeOpen.hidden = !isVisible;
    eyeClosed.hidden = isVisible;
    passwordInput.focus();
  });

  // Ocultarla otra vez antes de enviar para que el navegador no la guarde como texto
  passwordInput.form.addEventListener('submit', () => {
    passwordInput.type = 'password';
  });
}

// Aviso de Bloq Mayús
const capsHint = document.querySelector('[data-caps-hint]');

if (passwordInput && capsHint) {
  const updateCapsHint = (event) => {
    if (typeof event.getModifierState === 'function') {
      capsHint.hidden = !event.getModifierState('CapsLock');
    }
  };
  passwordInput.addEventListener('keydown', updateCapsHint);
  passwordInput.addEventListener('keyup', updateCapsHint);
  passwordInput.addEventListener('blur', () => {
    capsHint.hidden = true;
  });
}
