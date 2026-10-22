/* Browser-only session cache. Never stores passphrases, recovery codes or notes. */
const database = "mawj-journal-device-v1";
async function open() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(database, 1);
    request.onupgradeneeded = () => request.result.createObjectStore("keys", {keyPath: "userId"});
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
    request.onblocked = () => reject(Error("Browser storage unavailable"));
  });
}
async function transaction(mode, action) {
  const db = await open();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("keys", mode);
    const request = action(tx.objectStore("keys"));
    tx.oncomplete = () => { db.close(); resolve(request.result); };
    tx.onerror = () => { db.close(); reject(tx.error); };
    tx.onabort = () => { db.close(); reject(tx.error || Error("Browser storage unavailable")); };
  });
}
function usable(key) {
  return key instanceof CryptoKey && key.type === "secret" && key.extractable === false && key.algorithm.name === "AES-GCM" && key.algorithm.length === 256;
}
export async function rememberDeviceKey(userId, session, vaultId, key) {
  if (!Number.isSafeInteger(userId) || !session || !vaultId || !usable(key)) throw Error("Invalid device key");
  await transaction("readwrite", (store) => store.put({userId, session, vaultId, key}));
}
export async function forgetDeviceKey(userId) {
  if (!Number.isSafeInteger(userId)) return;
  await transaction("readwrite", (store) => store.delete(userId));
}
export async function readDeviceKey(userId, session, vaultId) {
  const saved = await transaction("readonly", (store) => store.get(userId));
  if (!saved) return null;
  if (saved.session !== session || saved.vaultId !== vaultId || !usable(saved.key)) {
    await forgetDeviceKey(userId);
    return null;
  }
  return saved.key;
}
