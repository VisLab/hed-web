// @vitest-environment node
// Page-flow tests: each describe makes the same hed-validator calls, in the same
// order, as one validation page. The pages are not imported; keep these call
// sequences in step with the page files named in each describe.
import {
  BidsDataset,
  BidsHedIssue,
  BidsSidecar,
  BidsTsvFile,
  BidsWebAccessor,
  IssueError,
  buildSchemasFromVersion,
  parseStandaloneString,
  parseTSV,
} from "hed-validator";
import { parseHedVersionInput } from "../../src/utils/hedVersion";
import { readFixtureFile, readFixtureFolder } from "../helpers/demoFiles";

const DEFAULT_VERSION = "8.4.0";
const DEMO_SIDECAR = "bidsDemoData/task-FacePerception_events.json";
const DEMO_EVENTS =
  "bidsDemoData/sub-002/ses-1/eeg/sub-002_ses-1_task-FacePerception_run-1_events.tsv";

// Codes of BIDS issues after the pages' processIssues step (no warnings, no limit).
function bidsCodes(issues) {
  return BidsHedIssue.processIssues(issues, false, false).map(
    (issue) => issue.hedIssue.hedCode,
  );
}

// Every page starts by parsing the version box and loading the schemas.
async function loadSchemas(versionText) {
  const { versions, error } = parseHedVersionInput(versionText);
  expect(error).toBeUndefined();
  return buildSchemasFromVersion(versions.join(","));
}

// src/validate_string.jsx:54-79
describe("string page", () => {
  async function validateString(hedString) {
    const schemas = await loadSchemas(DEFAULT_VERSION);
    const [, rawErrors, rawWarnings] = parseStandaloneString(
      hedString.trim(),
      schemas,
      null,
    );
    return { rawErrors, rawWarnings };
  }

  it("reports one TAG_INVALID error for Blech", async () => {
    const { rawErrors } = await validateString("Blech");
    expect(rawErrors.map((issue) => issue.hedCode)).toEqual(["TAG_INVALID"]);
  });

  it("reports no issues for Sensory-event", async () => {
    const { rawErrors, rawWarnings } = await validateString("Sensory-event");
    expect(rawErrors).toEqual([]);
    expect(rawWarnings).toEqual([]);
  });
});

// src/validate_sidecar.jsx:55-73
describe("sidecar page", () => {
  async function validateSidecar(jsonFile) {
    let issues = [];
    try {
      const schemas = await loadSchemas(DEFAULT_VERSION);
      const jsonText = await jsonFile.text();
      const jsonObject = JSON.parse(jsonText);
      const sidecar = new BidsSidecar(
        jsonFile.name,
        { path: jsonFile.name, name: jsonFile.name },
        jsonObject,
      );
      issues = sidecar.validate(schemas);
    } catch (err) {
      issues = BidsHedIssue.transformToBids([err], {
        path: jsonFile?.name ?? "sidecar.json",
      });
    }
    return bidsCodes(issues);
  }

  it("reports no issues for the demo sidecar", async () => {
    expect(await validateSidecar(readFixtureFile(DEMO_SIDECAR))).toEqual([]);
  });

  it("reports no issues for valid_sidecar.json", async () => {
    expect(
      await validateSidecar(readFixtureFile("small/valid_sidecar.json")),
    ).toEqual([]);
  });

  it("reports TAG_INVALID for invalid_sidecar.json", async () => {
    expect(
      await validateSidecar(readFixtureFile("small/invalid_sidecar.json")),
    ).toEqual(["TAG_INVALID"]);
  });
});

// src/validate_file.jsx:65-111
describe("file page", () => {
  async function validateFile(tsvFile, jsonFile) {
    let issues = [];
    let defaultPath = "HED schema input";
    try {
      defaultPath = "HED schema input";
      const schemas = await loadSchemas(DEFAULT_VERSION);

      defaultPath = jsonFile.name;
      const jsonText = await jsonFile.text();
      const jsonData = JSON.parse(jsonText);
      const jsonFileObject = { name: jsonFile.name, path: jsonFile.name };
      const bidsSidecar = new BidsSidecar(
        jsonFile.name,
        jsonFileObject,
        jsonData,
      );
      const sidecarIssues = bidsSidecar.validate(schemas);
      const sidecarErrors = sidecarIssues.filter(
        (issue) => issue.severity === "error",
      );

      if (sidecarErrors.length > 0) {
        issues = sidecarIssues;
      } else {
        const tsvText = await tsvFile.text();
        const parsedTsv = parseTSV(tsvText);
        const tsvFileObject = {
          name: tsvFile.name,
          path: tsvFile.name,
          file: tsvFile,
        };
        const bidsTsvFile = new BidsTsvFile(
          tsvFile.name,
          tsvFileObject,
          parsedTsv,
          jsonData,
          schemas.definitions,
        );
        issues = bidsTsvFile.validate(schemas);
      }
    } catch (err) {
      issues = BidsHedIssue.transformToBids([err], { path: defaultPath });
    }
    return bidsCodes(issues);
  }

  it("reports no issues for the demo events file with the demo sidecar", async () => {
    expect(
      await validateFile(
        readFixtureFile(DEMO_EVENTS),
        readFixtureFile(DEMO_SIDECAR),
      ),
    ).toEqual([]);
  });

  it("reports TAG_INVALID for invalid_events.tsv with valid_sidecar.json", async () => {
    expect(
      await validateFile(
        readFixtureFile("small/invalid_events.tsv"),
        readFixtureFile("small/valid_sidecar.json"),
      ),
    ).toEqual(["TAG_INVALID"]);
  });

  it("reports no issues for valid_events.tsv with valid_sidecar.json", async () => {
    expect(
      await validateFile(
        readFixtureFile("small/valid_events.tsv"),
        readFixtureFile("small/valid_sidecar.json"),
      ),
    ).toEqual([]);
  });
});

// src/validate_dataset.jsx:81-146 (load, then validate)
describe("dataset page", () => {
  // Same loop as getFileCounts, src/validate_dataset.jsx:36-56.
  function getFileCounts(dataset) {
    const counts = { json: 0, tsv: 0 };
    for (const pathGroup of dataset.fileAccessor.organizedPaths.values()) {
      const jsonFiles = pathGroup.get("json");
      if (jsonFiles) {
        counts.json += jsonFiles.length;
      }
      const tsvFiles = pathGroup.get("tsv");
      if (tsvFiles) {
        counts.tsv += tsvFiles.length;
      }
    }
    return counts;
  }

  it("loads and validates the demo dataset with no issues", async () => {
    const selectedFiles = readFixtureFolder("bidsDemoData");
    expect(selectedFiles).toHaveLength(56);

    const [createdDataset, createIssues] = await BidsDataset.create(
      selectedFiles,
      BidsWebAccessor,
    );
    expect(bidsCodes(createIssues)).toEqual([]);
    expect(createdDataset).toBeTruthy();
    expect(getFileCounts(createdDataset)).toEqual({ json: 11, tsv: 12 });

    let issues = createdDataset.validateSidecars();
    expect(bidsCodes(issues)).toEqual([]);
    issues = issues.concat(await createdDataset.validateTsvFiles());
    expect(bidsCodes(issues)).toEqual([]);
  });
});

describe("schema version", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 9.9.9 is not bundled, so hed-validator fetches it from GitHub. The fetch is
  // stubbed with a 404 so the test does not depend on the network.
  it("throws SCHEMA_LOAD_FAILED for version 9.9.9", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        new Response(null, { status: 404, statusText: "Not Found" }),
      );
    const { versions } = parseHedVersionInput("9.9.9");
    let thrown;
    try {
      await buildSchemasFromVersion(versions.join(","));
    } catch (err) {
      thrown = err;
    }
    expect(fetchSpy).toHaveBeenCalledTimes(1);
    expect(thrown).toBeInstanceOf(IssueError);
    expect(thrown.issue.hedCode).toBe("SCHEMA_LOAD_FAILED");
  });
});
