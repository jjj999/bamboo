"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const {
  closeMarkedIssues,
  extractIssueNumbers,
} = require("./close-issues-on-develop");

function makeHarness({ body = "", merged = true, base = "develop", items = {} }) {
  const calls = { get: [], update: [] };
  const logs = { info: [], warning: [] };
  const github = {
    rest: {
      issues: {
        async get(parameters) {
          calls.get.push(parameters);
          const item = items[parameters.issue_number];
          if (!item) {
            const error = new Error("Not Found");
            error.status = 404;
            throw error;
          }
          return { data: item };
        },
        async update(parameters) {
          calls.update.push(parameters);
          return { data: { ...items[parameters.issue_number], state: "closed" } };
        },
      },
    },
  };
  const context = {
    payload: {
      pull_request: { body, merged, base: { ref: base } },
    },
    repo: { owner: "jjj999", repo: "bamboo" },
  };
  const core = {
    info(message) {
      logs.info.push(message);
    },
    warning(message) {
      logs.warning.push(message);
    },
  };

  return { calls, close: () => closeMarkedIssues({ github, context, core }), logs };
}

test("closes an open Issue marked in a PR merged into develop", async () => {
  const harness = makeHarness({
    body: "Refs #25\nIssue-Closure: #25",
    items: { 25: { number: 25, state: "open" } },
  });

  assert.deepEqual(await harness.close(), [{ issueNumber: 25, status: "closed" }]);
  assert.deepEqual(harness.calls.update, [
    {
      owner: "jjj999",
      repo: "bamboo",
      issue_number: 25,
      state: "closed",
      state_reason: "completed",
    },
  ]);
});

test("does nothing when a PR is closed without merging", async () => {
  const harness = makeHarness({ body: "Issue-Closure: #25", merged: false });

  assert.deepEqual(await harness.close(), []);
  assert.equal(harness.calls.get.length, 0);
});

test("does nothing when a PR is merged into main", async () => {
  const harness = makeHarness({ body: "Issue-Closure: #25", base: "main" });

  assert.deepEqual(await harness.close(), []);
  assert.equal(harness.calls.get.length, 0);
});

test("does nothing when no closure marker exists", async () => {
  const harness = makeHarness({ body: "No related Issues." });

  assert.deepEqual(await harness.close(), []);
  assert.equal(harness.calls.get.length, 0);
});

test("closes multiple unique Issues", async () => {
  const harness = makeHarness({
    body: [
      "Issue-Closure: #25",
      "Issue-Closure: #26",
      "Issue-Closure: #25",
    ].join("\n"),
    items: {
      25: { number: 25, state: "open" },
      26: { number: 26, state: "open" },
    },
  });

  assert.deepEqual(await harness.close(), [
    { issueNumber: 25, status: "closed" },
    { issueNumber: 26, status: "closed" },
  ]);
  assert.equal(harness.calls.update.length, 2);
});

test("skips an Issue number that does not exist", async () => {
  const harness = makeHarness({ body: "Issue-Closure: #404" });

  assert.deepEqual(await harness.close(), [
    { issueNumber: 404, status: "missing" },
  ]);
  assert.equal(harness.calls.update.length, 0);
});

test("skips an Issue that is already closed", async () => {
  const harness = makeHarness({
    body: "Issue-Closure: #25",
    items: { 25: { number: 25, state: "closed" } },
  });

  assert.deepEqual(await harness.close(), [
    { issueNumber: 25, status: "already-closed" },
  ]);
  assert.equal(harness.calls.update.length, 0);
});

test("does not treat Refs as a closure marker", () => {
  assert.deepEqual(extractIssueNumbers("Refs #25"), []);
});

test("ignores markers in code blocks, block quotes, and comments", () => {
  const body = [
    "```text",
    "Issue-Closure: #25",
    "```",
    "> Issue-Closure: #26",
    "    Issue-Closure: #27",
    "<!--",
    "Issue-Closure: #28",
    "-->",
    "Issue-Closure: #29",
  ].join("\n");

  assert.deepEqual(extractIssueNumbers(body), [29]);
});

test("skips a number that belongs to a pull request", async () => {
  const harness = makeHarness({
    body: "Issue-Closure: #25",
    items: {
      25: {
        number: 25,
        state: "open",
        pull_request: { url: "https://api.github.com/repos/jjj999/bamboo/pulls/25" },
      },
    },
  });

  assert.deepEqual(await harness.close(), [
    { issueNumber: 25, status: "pull-request" },
  ]);
  assert.equal(harness.calls.update.length, 0);
});
