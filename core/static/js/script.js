// Bloque propio para no chocar con las constantes globales de otros scripts (p. ej. users/js/login.js)
{
  // Color de acento elegido por el usuario (lo aplica antes de pintar core/_head.html)
  const ACCENT_KEY = 'erp-accent';
  const accentButtons = document.querySelectorAll('[data-accent-option]');

  const markAccent = (accent) => {
    accentButtons.forEach((button) => {
      button.setAttribute('aria-pressed', String(button.dataset.accentOption === accent));
    });
  };

  markAccent(document.documentElement.dataset.accent || 'tangerine');

  accentButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const accent = button.dataset.accentOption;
      if (accent === 'tangerine') {
        delete document.documentElement.dataset.accent;
      } else {
        document.documentElement.dataset.accent = accent;
      }
      markAccent(accent);
      try {
        localStorage.setItem(ACCENT_KEY, accent);
      } catch (error) {
        // Sin almacenamiento disponible: el acento solo dura esta visita
      }
    });
  });

  // Menú desplegable en pantallas pequeñas
  const menuButton = document.getElementById('menu-toggle');
  const sheet = document.getElementById('portal-sheet');
  const sheetScrim = document.getElementById('sheet-scrim');

  if (menuButton && sheet && sheetScrim) {
    const setSheet = (open) => {
      menuButton.setAttribute('aria-expanded', String(open));
      sheetScrim.hidden = !open;
      document.body.style.overflow = open ? 'hidden' : '';

      if (open) {
        sheet.hidden = false;
        requestAnimationFrame(() => {
          sheet.classList.add('is-open');
          sheet.querySelector('a, button')?.focus();
        });
      } else {
        sheet.classList.remove('is-open');
        sheet.addEventListener('transitionend', () => {
          if (!sheet.classList.contains('is-open')) {
            sheet.hidden = true;
          }
        }, { once: true });
      }
    };

    menuButton.addEventListener('click', () => setSheet(true));
    sheetScrim.addEventListener('click', () => setSheet(false));
    sheet.querySelector('[data-sheet-close]')?.addEventListener('click', () => {
      setSheet(false);
      menuButton.focus();
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && sheet.classList.contains('is-open')) {
        setSheet(false);
        menuButton.focus();
      }
    });
    window.matchMedia('(min-width: 1024px)').addEventListener('change', (event) => {
      if (event.matches && sheet.classList.contains('is-open')) {
        setSheet(false);
      }
    });
  }

  // Confirmación con <dialog id="confirm-dialog"> para formularios con data-confirm="<nombre>"
  const confirmDialog = document.getElementById('confirm-dialog');

  if (confirmDialog && typeof confirmDialog.showModal === 'function') {
    const confirmName = confirmDialog.querySelector('[data-confirm-name]');
    let pendingForm = null;

    document.querySelectorAll('form[data-confirm]').forEach((form) => {
      form.addEventListener('submit', (event) => {
        if (form.dataset.confirmed === 'true') {
          return;
        }
        event.preventDefault();
        pendingForm = form;
        confirmName.textContent = form.dataset.confirm;
        confirmDialog.showModal();
      });
    });

    confirmDialog.addEventListener('close', () => {
      if (confirmDialog.returnValue === 'confirm' && pendingForm) {
        pendingForm.dataset.confirmed = 'true';
        pendingForm.requestSubmit();
      }
      pendingForm = null;
      confirmDialog.returnValue = '';
    });
  }

  // Vista previa en vivo y contador de caracteres del formulario de materiales
  const materialForm = document.querySelector('[data-material-form]');

  if (materialForm) {
    const statusLabels = {
      Active: '<span class="portal-status portal-status--active">Activo</span>',
      Inactive: '<span class="portal-status portal-status--inactive">Inactivo</span>',
    };

    materialForm.querySelectorAll('[data-preview-source]').forEach((field) => {
      const key = field.dataset.previewSource;
      const target = document.querySelector(`[data-preview="${key}"]`);
      if (!target) {
        return;
      }

      const update = () => {
        if (key === 'status') {
          if (field.checked) {
            target.innerHTML = statusLabels[field.value] || '';
          }
          return;
        }
        target.textContent = field.value.trim() || target.dataset.empty;
      };
      field.addEventListener(field.type === 'radio' ? 'change' : 'input', update);
    });

    const description = materialForm.querySelector('textarea[maxlength]');
    const counter = materialForm.querySelector('[data-char-count]');
    if (description && counter) {
      description.addEventListener('input', () => {
        counter.textContent = `${description.value.length}/${description.maxLength}`;
      });
    }
  }

  // Estado de carga en formularios con data-loading-form
  document.querySelectorAll('form[data-loading-form]').forEach((form) => {
    form.addEventListener('submit', (event) => {
      if (event.defaultPrevented) {
        return;
      }
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
}
