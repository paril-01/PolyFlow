// BUG: event listeners never removed
function init() {
  document.addEventListener('click', heavyHandler);
}
