// BUG: excessive use of 'any' defeats type safety
export function processData(data: any): any {
  return data.items.map((x: any) => x.value);
}
