/**
 * Shared helpers for invite PINs.
 *
 * Invite codes are short, human-typable PINs using an unambiguous
 * uppercase base32 alphabet (no `0 O 1 I L`). Mirrors the backend
 * `app.services.invite` definitions.
 */

export const INVITE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
export const INVITE_LENGTH = 6

const ALPHABET_SET = new Set(INVITE_ALPHABET)

/** Canonicalize user input: strip separators, uppercase, keep only
 * in-alphabet characters, and cap at the PIN length. */
export function normalizePin(raw: string): string {
  return [...raw.toUpperCase()]
    .filter((ch) => ALPHABET_SET.has(ch))
    .slice(0, INVITE_LENGTH)
    .join('')
}

/** True if `value` is a complete, in-alphabet PIN. */
export function isValidPin(value: string): boolean {
  return (
    value.length === INVITE_LENGTH &&
    [...value].every((ch) => ALPHABET_SET.has(ch))
  )
}
