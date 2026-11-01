// @vitest-environment node
import { describe, it, expect } from "vitest";
import { buildSchemasFromVersion } from "hed-validator";
import { parseHedVersionInput } from "./hedVersion";

describe("parseHedVersionInput", () => {
  describe("accepted forms", () => {
    const pair = ["score_2.2.0", "lang_1.2.0"];
    const cases = [
      ["8.4.0", ["8.4.0"]],
      ["sc:score_2.1.0", ["sc:score_2.1.0"]],
      ["8.4.0, sc:score_2.1.0", ["8.4.0", "sc:score_2.1.0"]],
      ["score_2.2.0, lang_1.2.0", pair],
      ["[score_2.2.0, lang_1.2.0]", pair],
      ['["score_2.2.0", "lang_1.2.0"]', pair],
      ["['score_2.2.0', 'lang_1.2.0']", pair],
      ['"8.4.0"', ["8.4.0"]],
      ["'8.4.0'", ["8.4.0"]],
      ["  [ score_2.2.0 ,lang_1.2.0 ]  ", pair],
      ["8.4.0,", ["8.4.0"]],
      ["[8.4.0,]", ["8.4.0"]],
    ];
    it.each(cases)("%s", (input, expected) => {
      expect(parseHedVersionInput(input)).toEqual({ versions: expected });
    });
  });

  describe("rejected forms", () => {
    const cases = [
      ["[8.4.0", /without a closing/],
      ["8.4.0]", /without an opening/],
      ["[[8.4.0]]", /nested brackets/],
      ['["8.4.0]', /unmatched quotes/],
      ["\"8.4.0'", /unmatched quotes/],
      ['["8.4.0""]', /unmatched quotes/],
      ['[8.4".0]', /unmatched quotes/],
      ["score_2.2.0 lang_1.2.0", /separate versions with commas/],
      ["[]", /is empty/],
      ["[ , ]", /is empty/],
      ['""', /is empty/],
    ];
    it.each(cases)("%s", (input, pattern) => {
      const result = parseHedVersionInput(input);
      expect(result.versions).toBeUndefined();
      expect(result.error).toMatch(pattern);
    });
  });

  it("gives versions that hed-validator loads", async () => {
    const { versions } = parseHedVersionInput("[score_2.2.0, lang_1.2.0]");
    await expect(
      buildSchemasFromVersion(versions.join(",")),
    ).resolves.toBeDefined();
  });
});
