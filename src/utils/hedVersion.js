// Normalizes the text of the HED schema version box before it goes to hed-validator.
// Accepts a single version, a comma list, or a bracketed list with optionally quoted entries.
// Returns { versions: string[] } on success or { error: string } on failure.
// The versions themselves are not checked here; buildSchemasFromVersion does that.

export function parseHedVersionInput(text) {
  let body = String(text ?? "").trim();

  // Optional surrounding brackets
  const opens = body.startsWith("[");
  const closes = body.endsWith("]");
  if (opens && !closes) {
    return { error: 'Schema version list: "[" without a closing "]".' };
  }
  if (closes && !opens) {
    return { error: 'Schema version list: "]" without an opening "[".' };
  }
  if (opens && closes) {
    body = body.slice(1, -1);
  }
  if (body.includes("[") || body.includes("]")) {
    return { error: "Schema version list: nested brackets are not allowed." };
  }

  const versions = [];
  for (const rawEntry of body.split(",")) {
    let entry = rawEntry.trim();
    if (!entry) continue;

    // Optional matching quotes around an entry
    const first = entry[0];
    const last = entry[entry.length - 1];
    const isQuote = (c) => c === '"' || c === "'";
    if (isQuote(first) || isQuote(last)) {
      if (entry.length < 2 || first !== last) {
        return {
          error: `Schema version list: entry ${entry} has unmatched quotes.`,
        };
      }
      entry = entry.slice(1, -1).trim();
      if (!entry) continue;
    }

    if (/\s/.test(entry)) {
      return {
        error: `Schema version list: separate versions with commas (${entry}).`,
      };
    }
    versions.push(entry);
  }

  if (versions.length === 0) {
    return { error: "Schema version list is empty." };
  }
  return { versions };
}
