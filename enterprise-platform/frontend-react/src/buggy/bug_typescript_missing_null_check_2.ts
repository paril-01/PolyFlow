// BUG: optional chaining missing
export function getUsername(user: User | null): string {
  return user.profile.username;
}
