/* Web Crypto primitives only. Experimental protocol v1; independent review required. */
const utf8 = new TextEncoder();
const subtle = globalThis.crypto.subtle;
const random = (size) => crypto.getRandomValues(new Uint8Array(size));
export function encode(bytes) {
  let value = "";
  for (let i = 0; i < bytes.length; i += 8192)
    value += String.fromCharCode(...bytes.subarray(i, i + 8192));
  return btoa(value);
}
function decode(value) {
  return Uint8Array.from(atob(value), (c) => c.charCodeAt(0));
}
function context(user, vault, purpose) {
  if (!Number.isSafeInteger(user) || user < 1 || !/^[0-9a-f-]{36}$/.test(vault)) throw Error("Invalid key context");
  return utf8.encode(`mawj:v1:user:${user}:vault:${vault}:${purpose}`);
}
async function aes(raw) {
  return subtle.importKey("raw", raw, "AES-GCM", false, ["encrypt", "decrypt"]);
}
export async function managedKey(value) {
  const raw = decode(value);
  if (raw.length !== 32) throw Error("Invalid managed key");
  try { return await aes(raw); } finally { raw.fill(0); }
}
export async function encryptDocument(document, key, user, vault, entry) {
  if (!/^[0-9a-f-]{36}$/.test(entry)) throw Error("Invalid entry context");
  const raw = utf8.encode(JSON.stringify(document));
  if (raw.length > 240000) throw Error("Entry is too large");
  const iv = random(12);
  return {version: 1, iv: encode(iv), ciphertext: encode(new Uint8Array(await subtle.encrypt({name: "AES-GCM", iv, additionalData: context(user, vault, `entry:${entry}`), tagLength: 128}, key, raw)))};
}
export async function decryptDocument(payload, key, user, vault, entry) {
  if (payload.version !== 1 || decode(payload.iv).length !== 12 || !/^[0-9a-f-]{36}$/.test(entry)) throw Error("Invalid entry envelope");
  const raw = await subtle.decrypt({name: "AES-GCM", iv: decode(payload.iv), additionalData: context(user, vault, `entry:${entry}`), tagLength: 128}, key, decode(payload.ciphertext));
  return JSON.parse(new TextDecoder("utf-8", {fatal: true}).decode(raw));
}
