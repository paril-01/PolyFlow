// BUG: unhandled promise rejection
async function fetchData() {
  const res = await fetch('/api/data');
  return res.json();
  // no error handling
}
