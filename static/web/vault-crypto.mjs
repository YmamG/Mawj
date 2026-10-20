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
async function wrapping(secret, envelope, aad, recovery) {
  if (recovery) {
    if (envelope.kdf !== "HKDF-SHA256" || decode(envelope.salt).length !== 32) throw Error("Invalid recovery envelope");
    const code = secret.replace(/[\s-]/g, "").toLowerCase();
    if (!/^[a-f0-9]{64}$/.test(code)) throw Error("Invalid recovery code");
    const bytes = Uint8Array.from(code.match(/../g), (pair) => parseInt(pair, 16));
    const material = await subtle.importKey("raw", bytes, "HKDF", false, ["deriveKey"]);
    bytes.fill(0);
    return subtle.deriveKey({name: "HKDF", hash: "SHA-256", salt: decode(envelope.salt), info: aad}, material, {name: "AES-GCM", length: 256}, false, ["encrypt", "decrypt"]);
  }
  if (envelope.kdf !== "PBKDF2-SHA256" || envelope.iterations !== 600000 || decode(envelope.salt).length !== 16) throw Error("Invalid passphrase envelope");
  const material = await subtle.importKey("raw", utf8.encode(secret), "PBKDF2", false, ["deriveKey"]);
  return subtle.deriveKey({name: "PBKDF2", hash: "SHA-256", salt: decode(envelope.salt), iterations: 600000}, material, {name: "AES-GCM", length: 256}, false, ["encrypt", "decrypt"]);
}
async function wrap(raw, secret, user, vault, recovery = false) {
  const aad = context(user, vault, recovery ? "recovery" : "passphrase");
  const info = recovery ? {kdf: "HKDF-SHA256", salt: encode(random(32))} : {kdf: "PBKDF2-SHA256", salt: encode(random(16)), iterations: 600000};
  const key = await wrapping(secret, info, aad, recovery);
  const iv = random(12);
  return {...info, iv: encode(iv), ciphertext: encode(new Uint8Array(await subtle.encrypt({name: "AES-GCM", iv, additionalData: aad, tagLength: 128}, key, raw)))};
}
async function unwrap(secret, info, user, vault, recovery = false) {
  if (decode(info.iv).length !== 12 || decode(info.ciphertext).length !== 48) throw Error("Invalid envelope");
  const aad = context(user, vault, recovery ? "recovery" : "passphrase");
  const key = await wrapping(secret, info, aad, recovery);
  return new Uint8Array(await subtle.decrypt({name: "AES-GCM", iv: decode(info.iv), additionalData: aad, tagLength: 128}, key, decode(info.ciphertext)));
}
export async function createVault(passphrase, user) {
  if (passphrase.length < 12) throw Error("Use at least 12 characters");
  const id = crypto.randomUUID(), raw = random(32);
  const recoveryCode = Array.from(random(32), (byte) => byte.toString(16).padStart(2, "0")).join("");
  try {
    return {id, key: await aes(raw), recoveryCode, envelopes: {passphrase: await wrap(raw, passphrase, user, id), recovery: await wrap(raw, recoveryCode, user, id, true)}};
  } finally { raw.fill(0); }
}
export async function unlock(passphrase, vault, user) {
  const raw = await unwrap(passphrase, vault.envelopes.passphrase, user, vault.id);
  try { return await aes(raw); } finally { raw.fill(0); }
}
export async function recover(code, newPassphrase, vault, user) {
  if (newPassphrase.length < 12) throw Error("Use at least 12 characters");
  const raw = await unwrap(code, vault.envelopes.recovery, user, vault.id, true);
  try {
    return {key: await aes(raw), envelopes: {passphrase: await wrap(raw, newPassphrase, user, vault.id), recovery: vault.envelopes.recovery}};
  } finally { raw.fill(0); }
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
