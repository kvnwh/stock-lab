$(document).ready(function () {
  function localizeDateTime(root) {
    const base = root || document;

    const fmtDate = new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium'
    });
    const fmtDateTime = new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short'
    });

    for (const el of base.querySelectorAll('time.js-localize-date[datetime]')) {
      const raw = el.getAttribute('datetime');
      const d = new Date(raw);
      if (!Number.isFinite(d.getTime())) continue;
      el.textContent = fmtDate.format(d);
    }

    for (const el of base.querySelectorAll('time.js-localize-datetime[datetime]')) {
      const raw = el.getAttribute('datetime');
      const d = new Date(raw);
      if (!Number.isFinite(d.getTime())) continue;
      el.textContent = fmtDateTime.format(d);
    }
  }

  $('#profitTable').DataTable({
    pageLength: 25,
    order: [[1, 'desc']],
    lengthChange: false
  });

  const optionDt = $('#optionTable').DataTable({
    pageLength: 50,
    order: [[5, 'desc']],
    lengthMenu: [25, 50, 100, 250],
    deferRender: true
  });

  localizeDateTime(document);
  optionDt.on('draw', function () {
    localizeDateTime(document);
  });
});
