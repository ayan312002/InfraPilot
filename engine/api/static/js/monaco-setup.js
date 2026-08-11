let _monacoRequire = null;
let _editorInstance = null;

function loadMonaco() {
  if (typeof _monacoRequire !== "undefined" && _monacoRequire !== null) {
    return _monacoRequire;
  }

  return new Promise((resolve, reject) => {
    if (window.monaco && window.monaco.editor) {
      resolve(window.monaco);
      return;
    }

    const script = document.createElement("script");
    script.src = "https://unpkg.com/monaco-editor/min/vs/loader.js";
    script.onload = () => {
      window.require.config({
        paths: {
          vs: "https://unpkg.com/monaco-editor/min/vs",
        },
      });
      window.require(["vs/editor/editor.main"], () => {
        resolve(window.monaco);
      });
    };
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

async function initMonaco(element, initialValue = "") {
  let monaco;
  try {
    monaco = await loadMonaco();
  } catch (err) {
    console.warn("Monaco CDN unavailable, using fallback viewer");
    element.innerHTML =
      '<pre style="padding:1.5rem;font-family:monospace;white-space:pre-wrap;' +
      'background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;overflow:auto;">' +
      (initialValue || "") +
      "</pre>";
    return {
      getValue: () => initialValue || "",
      setValue: (v) => {
        initialValue = v || "";
        const pre = element.querySelector("pre");
        if (pre) pre.textContent = initialValue;
      },
      _isFallback: true,
    };
  }

  _editorInstance = monaco.editor.create(element, {
    value: initialValue,
    language: "yaml",
    theme: "vs",
    readOnly: true,
    minimap: { enabled: false },
    lineNumbers: "on",
    scrollBeyondLastLine: false,
    automaticLayout: true,
    renderLineHighlight: "all",
    bracketPairColorization: { enabled: true },
  });

  monaco.editor.defineTheme("light-custom", {
    base: "vs",
    inherit: true,
    rules: [],
    colors: {
      "editor.background": "#ffffff",
      "editor.lineHighlightBackground": "#f0f9ff",
    },
  });
  _editorInstance.updateOptions({ theme: "light-custom" });

  return _editorInstance;
}

function setEditorValue(content) {
  if (_editorInstance) {
    _editorInstance.setValue(content || "");
  }
}

function getEditorValue() {
  if (_editorInstance) {
    return _editorInstance.getValue();
  }
  return "";
}

async function reloadMonaco(content) {
  if (!_editorInstance) return;
  if (_editorInstance._isFallback) {
    const pre = _editorInstance.element?.querySelector("pre");
    if (pre) pre.textContent = content || "";
    return;
  }
  _editorInstance.setValue(content || "");
  _editorInstance.redrawLines();
}
