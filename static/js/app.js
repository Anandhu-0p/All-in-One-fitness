document.addEventListener('DOMContentLoaded', function () {
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
});