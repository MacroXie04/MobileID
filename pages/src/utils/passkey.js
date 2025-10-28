/**
 * Converts a base64url-encoded string to an ArrayBuffer.
 * Handles various input types (ArrayBuffer, Uint8Array, Array, string).
 *
 * @param {string|ArrayBuffer|Uint8Array|Array} value - The value to convert
 * @returns {ArrayBuffer} The decoded ArrayBuffer
 */
export function b64urlToArrayBuffer(value) {
  if (value instanceof ArrayBuffer) return value;
  if (value instanceof Uint8Array) return value.buffer;
  if (Array.isArray(value)) return new Uint8Array(value).buffer;
  if (typeof value !== 'string') return new TextEncoder().encode(String(value)).buffer;

  try {
    const padding = '='.repeat((4 - (value.length % 4)) % 4);
    const base64 = (value + padding).replace(/-/g, '+').replace(/_/g, '/');
    const raw = atob(base64);
    const buffer = new ArrayBuffer(raw.length);
    const view = new Uint8Array(buffer);
    for (let i = 0; i < raw.length; ++i) view[i] = raw.charCodeAt(i);
    return buffer;
  } catch (e) {
    return new TextEncoder().encode(value).buffer;
  }
}

/**
 * Converts an ArrayBuffer to a base64url-encoded string.
 *
 * @param {ArrayBuffer} buffer - The ArrayBuffer to convert
 * @returns {string} The base64url-encoded string
 */
export function arrayBufferToB64url(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  const base64 = btoa(binary).replace(/=+$/g, '');
  return base64.replace(/\+/g, '-').replace(/\//g, '_');
}
