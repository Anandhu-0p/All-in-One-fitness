/* Restore the desktop sidebar before the page becomes interactive. */
(function () {
  if (window.matchMedia('(min-width: 992px)').matches && localStorage.getItem('sidebar-collapsed') === 'true') {
    document.querySelector('.app-shell')?.classList.add('sidebar-collapsed');
  }
})();

document.addEventListener('DOMContentLoaded', function () {
  var shell = document.querySelector('.app-shell');
  var sidebarToggle = document.querySelector('.sidebar-toggle');

  if (shell && sidebarToggle) {
    var updateSidebarToggle = function () {
      var collapsed = shell.classList.contains('sidebar-collapsed');
      sidebarToggle.setAttribute('aria-expanded', String(!collapsed));
      sidebarToggle.setAttribute('aria-label', collapsed ? 'Expand sidebar' : 'Collapse sidebar');
      sidebarToggle.setAttribute('title', collapsed ? 'Expand sidebar' : 'Collapse sidebar');
      sidebarToggle.querySelector('i').className = collapsed
        ? 'bi bi-layout-sidebar-inset-reverse'
        : 'bi bi-layout-sidebar-inset';
    };

    sidebarToggle.addEventListener('click', function () {
      shell.classList.toggle('sidebar-collapsed');
      localStorage.setItem('sidebar-collapsed', String(shell.classList.contains('sidebar-collapsed')));
      updateSidebarToggle();
    });
    updateSidebarToggle();
  }

  // Auto-dismiss alerts after 6 seconds
  document.querySelectorAll('.alert-dismissible').forEach(function (alert) {
    setTimeout(function () {
      var close = alert.querySelector('.btn-close');
      if (close) close.click();
    }, 6000);
  });

  // Confirm destructive actions on forms/links with data-confirm
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      var message = el.getAttribute('data-confirm') || 'Are you sure?';
      if (!window.confirm(message)) {
        e.preventDefault();
      }
    });
  });

  // Highlight the active sidebar link based on current path
  var path = window.location.pathname;
  document.querySelectorAll('.sidebar-nav a.nav-link').forEach(function (link) {
    var href = link.getAttribute('href');
    if (href && href !== '#' && path === href) {
      link.classList.add('active');
    }
  });

  var desktopNav = document.querySelector('.app-sidebar .sidebar-nav');
  var activeLink = desktopNav && desktopNav.querySelector('.nav-link.active');
  if (activeLink) {
    activeLink.scrollIntoView({ block: 'nearest' });
  }
});