// BUG: prototype pollution
function merge(target, source) {
  for (let key in source) {
    target[key] = source[key];
  }
}
