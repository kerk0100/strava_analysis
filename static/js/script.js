let form = document.querySelecter('form');

form.addEventListener('submit', (e) => {
  e.preventDefault();
  return false;
});

var expanded = false;

$(function() {

  $('#chkveg').multiselect({
    includeSelectAllOption: true
  });

  $('#btnget').click(function() {
    alert($('#chkveg').val());
  });
});