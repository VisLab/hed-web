// Reads fixture files into File objects shaped like a browser upload.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const fixturesDir = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../fixtures",
);

// Returns one File for a fixture, named by its basename, like a single-file input.
export function readFixtureFile(relativePath) {
  const fullPath = path.join(fixturesDir, relativePath);
  return new File([fs.readFileSync(fullPath)], path.basename(fullPath));
}

// Returns a File for every file under a fixture folder, each with the
// webkitRelativePath "<folder name>/<path>" that a browser folder upload gives.
export function readFixtureFolder(folderName) {
  const root = path.join(fixturesDir, folderName);
  const files = [];
  const walk = (dir) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        walk(fullPath);
      } else {
        const file = new File([fs.readFileSync(fullPath)], entry.name);
        const relativePath = path
          .relative(root, fullPath)
          .split(path.sep)
          .join("/");
        Object.defineProperty(file, "webkitRelativePath", {
          value: `${path.basename(root)}/${relativePath}`,
        });
        files.push(file);
      }
    }
  };
  walk(root);
  return files;
}
