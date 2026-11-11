// Headless save-persistence test (node + playwright, see spike/).
// Boots the bundle with ?noapp (no game loop, so Python is callable),
// creates a character, reloads, and checks it survived.
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
// resolve playwright from spike/node_modules (spike/ owns the dev deps)
const require = createRequire(fileURLToPath(new URL("../spike/package.json", import.meta.url)));
const { chromium } = require("playwright");

const base = (process.env.BASE ?? "http://127.0.0.1:8322/") + "?noapp";
const boot = async (page) => {
  for (let i = 0; i < 120; i++) {
    const s = (await page.textContent("#status")) ?? "";
    if (s.startsWith("app running") || s.startsWith("error")) return s;
    await new Promise((r) => setTimeout(r, 500));
  }
  return "timeout";
};

const browser = await chromium.launch();
const page = await browser.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));

await page.goto(base, { waitUntil: "domcontentloaded" });
let status = await boot(page);
console.log(`boot: ${status}`);

const created = await page.evaluate(() =>
  window.pyodide.runPython(`
from quick_herbalist.web_entry import prepare
prepare()
from quick_herbalist.profiles import ProfileManager
pm = ProfileManager()
pm.create_character("PersistTest")
pm.active_character_name`));
console.log(`created, active: ${created}`);

status = await (async () => {
  await page.reload({ waitUntil: "domcontentloaded" });
  return boot(page);
})();
console.log(`reload: ${status}`);
const readback = await page.evaluate(() =>
  window.pyodide.runPython(`
from quick_herbalist.web_entry import prepare
prepare()
from quick_herbalist.profiles import ProfileManager
ProfileManager().active_character_name`));
console.log(`readback: ${readback}`);

let fail = 0;
for (const [label, ok] of [
  ["initial boot ok", status !== "error" && status !== "timeout"],
  ["character survives reload", readback === "PersistTest"],
  ["no page errors", errors.length === 0],
]) {
  console.log(`${ok ? "PASS" : "FAIL"}  ${label}`);
  if (!ok) fail++;
}
if (errors.length) console.log("ERRORS:\n" + errors.join("\n"));
await browser.close();
process.exit(fail ? 1 : 0);
