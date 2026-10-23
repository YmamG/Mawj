/* Run with Node 22+; no dependency install and no secrets printed. */
import assert from "node:assert/strict";
import {managedKey, encryptDocument, decryptDocument} from "../static/web/vault-crypto.mjs";

const vault = {id: crypto.randomUUID()};
const noteId = crypto.randomUUID();
const document = {text: "ملاحظة اختبار وهمية <script>not executed</script>", clean_text: "", suggestions: []};
const managed = await managedKey(Buffer.alloc(32, 7).toString("base64"));
const managedNote = await encryptDocument(document, managed, 1, vault.id, noteId);
assert.deepEqual(await decryptDocument(managedNote, managed, 1, vault.id, noteId), document);
await assert.rejects(managedKey(Buffer.alloc(31, 7).toString("base64")));
const one = await encryptDocument(document, managed, 1, vault.id, noteId);
const two = await encryptDocument(document, managed, 1, vault.id, noteId);
assert.notEqual(one.iv, two.iv);
assert.notEqual(one.ciphertext, two.ciphertext);
assert.deepEqual(await decryptDocument(one, managed, 1, vault.id, noteId), document);
assert.equal(JSON.stringify(one).includes(document.text), false);
await assert.rejects(decryptDocument(one, managed, 2, vault.id, noteId));
await assert.rejects(decryptDocument(one, managed, 1, vault.id, crypto.randomUUID()));
const modified = {...one, ciphertext: (one.ciphertext[0] === "A" ? "B" : "A") + one.ciphertext.slice(1)};
await assert.rejects(decryptDocument(modified, managed, 1, vault.id, noteId));
console.log("Web Crypto managed-key round trip, nonce uniqueness, and tamper/context rejection checks passed.");
