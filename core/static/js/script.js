// Bloque propio para no chocar con las constantes globales de otros scripts (p. ej. users/js/login.js)
{
  // Menú lateral: en pantallas pequeñas se abre como cajón
  const menuButton = document.getElementById('menu-toggle');
  const sidebar = document.getElementById('portal-sidebar');
  const sidebarScrim = document.getElementById('sidebar-scrim');

  if (menuButton && sidebar && sidebarScrim) {
    const setSidebar = (open) => {
      menuButton.setAttribute('aria-expanded', String(open));
      sidebar.classList.toggle('is-open', open);
      sidebarScrim.hidden = !open;
      document.body.style.overflow = open ? 'hidden' : '';
      if (open) {
        sidebar.querySelector('a, button')?.focus();
      }
    };

    menuButton.addEventListener('click', () => setSidebar(true));
    sidebarScrim.addEventListener('click', () => setSidebar(false));
    sidebar.querySelector('[data-sidebar-close]')?.addEventListener('click', () => {
      setSidebar(false);
      menuButton.focus();
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && sidebar.classList.contains('is-open')) {
        setSidebar(false);
        menuButton.focus();
      }
    });
    window.matchMedia('(min-width: 1024px)').addEventListener('change', (event) => {
      if (event.matches && sidebar.classList.contains('is-open')) {
        setSidebar(false);
      }
    });
  }

  // Menú lateral contraído en escritorio (core/_head.html lo aplica antes de pintar)
  const SIDEBAR_KEY = 'erp-sidebar';
  const collapseButton = document.querySelector('[data-sidebar-collapse]');

  if (collapseButton) {
    const markCollapsed = (collapsed) => {
      const label = collapsed ? 'Expandir menú' : 'Contraer menú';
      collapseButton.setAttribute('aria-pressed', String(collapsed));
      collapseButton.setAttribute('aria-label', label);
      collapseButton.dataset.tooltip = label;
    };

    markCollapsed(document.documentElement.dataset.sidebar === 'collapsed');

    collapseButton.addEventListener('click', () => {
      const collapsed = document.documentElement.dataset.sidebar !== 'collapsed';
      if (collapsed) {
        document.documentElement.dataset.sidebar = 'collapsed';
      } else {
        delete document.documentElement.dataset.sidebar;
      }
      markCollapsed(collapsed);
      try {
        localStorage.setItem(SIDEBAR_KEY, collapsed ? 'collapsed' : 'expanded');
      } catch (error) {
        // Sin almacenamiento disponible: la preferencia solo dura esta visita
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
