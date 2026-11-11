// QuickHerbalist web bundle loader. Boots pyodide, extracts the Kivy WASM
// wheel and the app wheel into the Emscripten FS site-packages, then runs
// quick_herbalist.web_entry.main(). Static only — no server logic.
// No micropip: wheel deps are not installable offline, and the game only
// needs the kivy + app wheels themselves.
const status = (msg) => {
  console.log(`WEB: ${msg}`);
  const el = document.getElementById("status");
  if (el) el.textContent = msg;
};

window.onerror = (msg) => status(`page error: ${msg}`);

async function main() {
  status("loading pyodide");
  const pyodide = await loadPyodide({ indexURL: "pyodide/" });
  pyodide.canvas.setCanvas3D(document.getElementById("canvas"));
  // expose the pyodide object on globalThis (from js import pyodide)
  window.pyodide = pyodide;

  status("installing kivy + app wheels");
  const appWheel = (await (await fetch("app-wheel.txt")).text()).trim();
  const wheels = [
    "kivy-3.0.0.dev0-cp313-cp313-pyemscripten_2025_0_wasm32.whl",
    "pyyaml-6.0.2-cp313-cp313-pyemscripten_2025_0_wasm32.whl",
    "filetype-1.2.0-py2.py3-none-any.whl",
    appWheel,
  ];
  for (const name of wheels) {
    const r = await fetch(name);
    if (!r.ok) throw new Error(`fetch ${name} -> ${r.status}`);
    pyodide.FS.writeFile(name, new Uint8Array(await r.arrayBuffer()));
  }
  pyodide.runPython(`
import sysconfig, zipfile
site = sysconfig.get_paths()["purelib"]
for whl in (
${wheels.map((w) => `    "${w}",`).join("\n")}
):
    with zipfile.ZipFile(whl) as zf:
        zf.extractall(site)
`);

  status("starting app");
  // ?noapp boots the runtime without starting the game (used by probe_persist.mjs)
  if (!new URLSearchParams(location.search).has("noapp")) {
    pyodide.runPython("from quick_herbalist.web_entry import main; main()");
  }
  status("app running");
}

main().catch((err) => status(`error: ${err && err.message ? err.message : err}`));
