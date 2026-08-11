// Anonymous profile identity.
//
// The token is generated in the browser and never leaves local storage except
// as a request header. There is no account, no email and no password — which
// means there is nothing to breach beyond a list of skills the user typed in
// themselves, and "delete my data" is a single DELETE request.

const KEY = 'helloworld.profile-token'

function generate(): string {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID()
  const bytes = new Uint8Array(16)
  globalThis.crypto.getRandomValues(bytes)
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('')
}

export function getProfileToken(): string {
  try {
    const existing = localStorage.getItem(KEY)
    if (existing && existing.length >= 8) return existing
    const fresh = generate()
    localStorage.setItem(KEY, fresh)
    return fresh
  } catch {
    // Private browsing with storage disabled: fall back to a per-session token
    // so the app still works, it just will not persist across reloads.
    return generate()
  }
}

export function clearProfileToken(): void {
  try {
    localStorage.removeItem(KEY)
  } catch {
    /* nothing we can do, and nothing that needs doing */
  }
}
