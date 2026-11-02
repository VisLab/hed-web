import React from "react";
import { act } from "react";
import { createRoot } from "react-dom/client";
import { renderToStaticMarkup } from "react-dom/server";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import helpText from "../help/help_text.json";
import { HelpButton } from "./HelpButton";
import { FileInput } from "./FileInput";

const srcDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

describe("HelpButton", () => {
  let container;
  let root;

  beforeEach(() => {
    container = document.createElement("div");
    document.body.appendChild(container);
  });

  afterEach(() => {
    act(() => root.unmount());
    document.body.removeChild(container);
  });

  async function renderComponent(ui) {
    await act(async () => {
      root = createRoot(container);
      root.render(ui);
    });
  }

  async function click(element) {
    await act(async () => {
      element.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });
  }

  function helpButtons() {
    return Array.from(container.querySelectorAll("button[aria-label^='Help for']"));
  }

  it("starts closed", async () => {
    await renderComponent(<HelpButton helpKey="check_warnings" />);
    const [button] = helpButtons();
    expect(button.getAttribute("aria-expanded")).toBe("false");
    expect(button.getAttribute("aria-label")).toBe("Help for Check warnings");
    expect(container.querySelector("[role='tooltip']")).toBeNull();
  });

  it("opens on click with the title and text from help_text.json", async () => {
    await renderComponent(<HelpButton helpKey="limit_errors" />);
    const [button] = helpButtons();
    await click(button);
    const panel = container.querySelector("[role='tooltip']");
    const { title, text } = helpText.entries.limit_errors;
    expect(button.getAttribute("aria-expanded")).toBe("true");
    expect(button.getAttribute("aria-describedby")).toBe(panel.id);
    expect(button.getAttribute("aria-controls")).toBe(panel.id);
    expect(panel.textContent).toBe(title + text);
  });

  it("closes on a second click", async () => {
    await renderComponent(<HelpButton helpKey="check_warnings" />);
    const [button] = helpButtons();
    await click(button);
    await click(button);
    expect(button.getAttribute("aria-expanded")).toBe("false");
    expect(container.querySelector("[role='tooltip']")).toBeNull();
  });

  it("closes on Escape and returns focus to the button", async () => {
    await renderComponent(<HelpButton helpKey="check_warnings" />);
    const [button] = helpButtons();
    await click(button);
    await act(async () => {
      document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
    });
    expect(container.querySelector("[role='tooltip']")).toBeNull();
    expect(document.activeElement).toBe(button);
  });

  it("closes on a click outside", async () => {
    await renderComponent(
      <div>
        <p id="outside">Elsewhere</p>
        <HelpButton helpKey="check_warnings" />
      </div>,
    );
    const [button] = helpButtons();
    await click(button);
    await click(container.querySelector("#outside"));
    expect(container.querySelector("[role='tooltip']")).toBeNull();
  });

  it("keeps the panel open on a click inside it", async () => {
    await renderComponent(<HelpButton helpKey="check_warnings" />);
    const [button] = helpButtons();
    await click(button);
    await click(container.querySelector("[role='tooltip']"));
    expect(container.querySelector("[role='tooltip']")).not.toBeNull();
  });

  it("closes the first panel when a second one opens", async () => {
    await renderComponent(
      <div>
        <HelpButton helpKey="check_warnings" />
        <HelpButton helpKey="limit_errors" />
      </div>,
    );
    const [first, second] = helpButtons();
    await click(first);
    await click(second);
    expect(first.getAttribute("aria-expanded")).toBe("false");
    expect(second.getAttribute("aria-expanded")).toBe("true");
    expect(container.querySelectorAll("[role='tooltip']")).toHaveLength(1);
  });

  it("does not toggle the checkbox it sits beside", async () => {
    await renderComponent(
      <div>
        <input id="check-warnings" type="checkbox" defaultChecked={false} />
        <label htmlFor="check-warnings">Check warnings</label>
        <HelpButton helpKey="check_warnings" />
      </div>,
    );
    await click(helpButtons()[0]);
    expect(container.querySelector("#check-warnings").checked).toBe(false);
  });

  it("does not open the file dialog of the FileInput it sits in", async () => {
    await renderComponent(
      <FileInput
        id="json-upload"
        buttonText="JSON file"
        helpKey="sidecar_file"
        accept=".json"
        onFileSelect={() => {}}
        isLoading={false}
      />,
    );
    const fileInput = container.querySelector("#json-upload");
    const fileClicks = vi.fn();
    fileInput.addEventListener("click", fileClicks);
    expect(helpButtons()[0].closest("label")).toBeNull();
    await click(helpButtons()[0]);
    expect(fileClicks).not.toHaveBeenCalled();
    expect(container.querySelector("[role='tooltip']")).not.toBeNull();
  });

  it("throws for an unknown key", () => {
    expect(() => renderToStaticMarkup(<HelpButton helpKey="no_such_key" />)).toThrow(
      "Unknown help key: no_such_key",
    );
    expect(() => renderToStaticMarkup(<HelpButton helpKey="toString" />)).toThrow(
      "Unknown help key: toString",
    );
  });
});

describe("help_text.json", () => {
  const entries = Object.entries(helpText.entries);

  it("has sorted keys", () => {
    const keys = Object.keys(helpText.entries);
    expect(keys).toEqual([...keys].sort());
  });

  it.each(entries)("entry %s has only a plain ASCII title and text", (key, entry) => {
    expect(Object.keys(entry).sort()).toEqual(["text", "title"]);
    for (const value of [entry.title, entry.text]) {
      expect(typeof value).toBe("string");
      expect(value.trim()).not.toBe("");
      expect(value).toMatch(/^[\x20-\x7E]+$/);
      expect(value).not.toMatch(/[<>]/);
    }
  });

  it("matches the helpKeys used in src", () => {
    const used = [];
    const walk = (dir) => {
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          walk(fullPath);
        } else if (/\.jsx?$/.test(entry.name) && !/\.spec\.jsx?$/.test(entry.name)) {
          const source = fs.readFileSync(fullPath, "utf8");
          for (const match of source.matchAll(/helpKey="([^"]+)"/g)) {
            used.push(match[1]);
          }
        }
      }
    };
    walk(srcDir);
    expect(used).toHaveLength(15);
    expect([...new Set(used)].sort()).toEqual(Object.keys(helpText.entries).sort());
  });
});
