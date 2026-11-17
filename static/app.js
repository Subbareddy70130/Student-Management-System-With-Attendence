(function () {
  // ---- Broken photo links: fall back to initials ----
  document.querySelectorAll('img[data-avatar]').forEach(function (img) {
    img.addEventListener('error', function () { img.remove(); });
  });

  // ---- Search + status filter on the list page ----
  var rows = document.querySelectorAll('#rows tr');
  if (rows.length) {
    var search = document.getElementById('search');
    var buttons = document.querySelectorAll('#status-filter button');
    var empty = document.getElementById('no-match');
    var status = 'all';

    function apply() {
      var q = search.value.trim().toLowerCase();
      var shown = 0;
      rows.forEach(function (row) {
        var ok = row.dataset.search.indexOf(q) !== -1 &&
                 (status === 'all' || row.dataset.status === status);
        row.hidden = !ok;
        if (ok) shown++;
      });
      empty.hidden = shown !== 0;
    }
    search.addEventListener('input', apply);
    buttons.forEach(function (b) {
      b.addEventListener('click', function () {
        status = b.dataset.status;
        buttons.forEach(function (x) { x.setAttribute('aria-pressed', x === b); });
        apply();
      });
    });
  }

  // ---- Delete confirmation dialog ----
  var dialog = document.getElementById('confirm-dialog');
  var pending = null;
  document.querySelectorAll('form[data-confirm]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      pending = form;
      document.getElementById('confirm-title').textContent = form.dataset.confirm;
      document.getElementById('confirm-text').textContent = form.dataset.confirmText || '';
      dialog.showModal();
    });
  });
  document.getElementById('confirm-cancel').addEventListener('click', function () { dialog.close(); });
  document.getElementById('confirm-ok').addEventListener('click', function () {
    if (pending) pending.submit();
  });

  // ---- Live photo + initials preview on the form ----
  var nameInput = document.getElementById('name');
  var imageInput = document.getElementById('image');
  if (nameInput && imageInput) {
    var initials = document.getElementById('photo-initials');
    var img = document.getElementById('photo-img');
    function updateInitials() {
      var parts = nameInput.value.trim().split(/\s+/).filter(Boolean);
      initials.textContent = parts.slice(0, 2).map(function (p) { return p[0]; }).join('').toUpperCase() || '?';
    }
    function updateImage() {
      var url = imageInput.value.trim();
      if (url) { img.src = url; img.hidden = false; } else { img.hidden = true; }
    }
    img.addEventListener('error', function () { img.hidden = true; });
    nameInput.addEventListener('input', updateInitials);
    imageInput.addEventListener('input', updateImage);
  }
})();
