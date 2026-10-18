"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const {
  closeMarkedIssues,
  extractIssueNumbers,
} = require("./close-issues-on-develop");

const BEFORE_SHA = "a".repeat(40);
const MERGE_SHA = "b".repeat(40);

function makeHarness({
  body = "",
  merged = true,
  base = "develop",
  baseRepository = "jjj999/bamboo",
  items = {},
  commitShas = [MERGE_SHA],
  associated,
  pullRequests,
  eventName = "push",
  ref = "refs/heads/develop",
  forced = false,
  compareError,
  associationError,
  totalCommits = commitShas.length,
} = {}) {
  const calls = {
    compare: [],
    associated: [],
    pullGet: [],
    get: [],
    update: [],
  };
  const logs = { error: [], info: [], warning: [] };
  const after = commitShas.at(-1) || MERGE_SHA;
  const defaultPullRequest = {
    number: 15,
    body,
    merged,
    merged_at: merged ? "2026-10-18T03:01:06Z" : null,
    merge_commit_sha: after,
    base: { ref: base, repo: { full_name: baseRepository } },
  };
  const pulls = pullRequests || { 15: defaultPullRequest };
  const associations =
    associated ||
    Object.fromEntries(commitShas.map((sha) => [sha, [{ number: 15 }]]));
  const github = {
    rest: {
      repos: {
        async compareCommitsWithBasehead(parameters) {
          calls.compare.push(parameters);
          if (compareError) {
            throw compareError;
          }
          const start = (parameters.page - 1) * parameters.per_page;
          return {
            data: {
              commits: commitShas
                .slice(start, start + parameters.per_page)
                .map((sha) => ({ sha })),
              total_commits: totalCommits,
            },
          };
        },
        async listPullRequestsAssociatedWithCommit(parameters) {
          calls.associated.push(parameters);
          if (associationError) {
            throw associationError;
          }
          return { data: associations[parameters.commit_sha] || [] };
        },
      },
      pulls: {
        async get(parameters) {
          calls.pullGet.push(parameters);
          return { data: pulls[parameters.pull_number] };
        },
      },
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
      ref,
      before: BEFORE_SHA,
      after,
      created: false,
      deleted: false,
      forced,
    },
    eventName,
    repo: { owner: "jjj999", repo: "bamboo" },
  };
  const core = {
    error(message) {
      logs.error.push(message);
    },
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

test("does nothing when a PR targets develop in another repository", async () => {
  const harness = makeHarness({
    body: "Issue-Closure: #25",
    baseRepository: "someone/bamboo",
    items: { 25: { number: 25, state: "open" } },
  });

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

test("does nothing for a direct push with no associated pull request", async () => {
  const harness = makeHarness({
    body: "Issue-Closure: #25",
    associated: { [MERGE_SHA]: [] },
    items: { 25: { number: 25, state: "open" } },
  });

  assert.deepEqual(await harness.close(), []);
  assert.equal(harness.calls.pullGet.length, 0);
  assert.equal(harness.calls.update.length, 0);
});

test("does nothing when the push ref is main", async () => {
  const harness = makeHarness({
    body: "Issue-Closure: #25",
    ref: "refs/heads/main",
    items: { 25: { number: 25, state: "open" } },
  });

  assert.deepEqual(await harness.close(), []);
  assert.equal(harness.calls.compare.length, 0);
  assert.equal(harness.calls.update.length, 0);
});

test("does nothing when no related pull request is found", async () => {
  const harness = makeHarness({ associated: { [MERGE_SHA]: [] } });

  assert.deepEqual(await harness.close(), []);
  assert.match(harness.logs.info.at(-1), /No pull requests/);
});

test("rejects a historical pull request whose merge commit is not in the push", async () => {
  const historicalSha = "c".repeat(40);
  const harness = makeHarness({
    body: "Issue-Closure: #25",
    pullRequests: {
      15: {
        number: 15,
        body: "Issue-Closure: #25",
        merged: true,
        merged_at: "2026-10-01T00:00:00Z",
        merge_commit_sha: historicalSha,
        base: {
          ref: "develop",
          repo: { full_name: "jjj999/bamboo" },
        },
      },
    },
    items: { 25: { number: 25, state: "open" } },
  });

  assert.deepEqual(await harness.close(), []);
  assert.equal(harness.calls.update.length, 0);
  assert.match(harness.logs.info.at(-1), /not a merge into develop/);
});

test("processes a squash merge whose merge SHA is in the push", async () => {
  const squashSha = "d".repeat(40);
  const harness = makeHarness({
    body: "Issue-Closure: #25",
    commitShas: [squashSha],
    items: { 25: { number: 25, state: "open" } },
  });

  assert.deepEqual(await harness.close(), [{ issueNumber: 25, status: "closed" }]);
});

test("processes a rebase merge using its final rebased commit", async () => {
  const firstRebasedSha = "d".repeat(40);
  const finalRebasedSha = "e".repeat(40);
  const harness = makeHarness({
    body: "Issue-Closure: #25",
    commitShas: [firstRebasedSha, finalRebasedSha],
    items: { 25: { number: 25, state: "open" } },
  });

  assert.deepEqual(await harness.close(), [{ issueNumber: 25, status: "closed" }]);
  assert.equal(harness.calls.pullGet.length, 1);
  assert.equal(harness.calls.update.length, 1);
});

test("finds every merged pull request in a multi-commit push", async () => {
  const firstMergeSha = "d".repeat(40);
  const secondMergeSha = "e".repeat(40);
  const harness = makeHarness({
    commitShas: [firstMergeSha, secondMergeSha],
    associated: {
      [firstMergeSha]: [{ number: 15 }],
      [secondMergeSha]: [{ number: 16 }],
    },
    pullRequests: {
      15: {
        number: 15,
        body: "Issue-Closure: #25",
        merged: true,
        merged_at: "2026-10-18T03:01:06Z",
        merge_commit_sha: firstMergeSha,
        base: {
          ref: "develop",
          repo: { full_name: "jjj999/bamboo" },
        },
      },
      16: {
        number: 16,
        body: "Issue-Closure: #26",
        merged: true,
        merged_at: "2026-10-18T03:02:06Z",
        merge_commit_sha: secondMergeSha,
        base: {
          ref: "develop",
          repo: { full_name: "jjj999/bamboo" },
        },
      },
    },
    items: {
      25: { number: 25, state: "open" },
      26: { number: 26, state: "open" },
    },
  });

  assert.deepEqual(await harness.close(), [
    { issueNumber: 25, status: "closed" },
    { issueNumber: 26, status: "closed" },
  ]);
  assert.equal(harness.calls.associated.length, 2);
  assert.equal(harness.calls.update.length, 2);
});

test("paginates commit discovery for a large push", async () => {
  const commitShas = Array.from({ length: 101 }, (_, index) =>
    index.toString(16).padStart(40, "0"),
  );
  const harness = makeHarness({ commitShas, associated: {} });

  assert.deepEqual(await harness.close(), []);
  assert.equal(harness.calls.compare.length, 2);
  assert.equal(harness.calls.associated.length, 101);
});

test("does nothing for a force push", async () => {
  const harness = makeHarness({
    body: "Issue-Closure: #25",
    forced: true,
    items: { 25: { number: 25, state: "open" } },
  });

  assert.deepEqual(await harness.close(), []);
  assert.equal(harness.calls.compare.length, 0);
  assert.equal(harness.calls.update.length, 0);
  assert.match(harness.logs.warning.at(-1), /force pushes/);
});

test("reports and propagates GitHub API errors", async () => {
  const apiError = new Error("GitHub unavailable");
  apiError.status = 503;
  const harness = makeHarness({ associationError: apiError });

  await assert.rejects(harness.close(), /GitHub unavailable/);
  assert.match(
    harness.logs.error.at(-1),
    /Failed to list pull requests associated with commit/,
  );
});

test("fails visibly when commit discovery is incomplete", async () => {
  const harness = makeHarness({ totalCommits: 2 });

  await assert.rejects(harness.close(), /returned 1 of 2 commits/);
  assert.match(harness.logs.error.at(-1), /Incomplete push commit discovery/);
  assert.equal(harness.calls.associated.length, 0);
});

test("models PR #15 without modifying its already closed Issue", async () => {
  const pr15MergeSha = "3bf66e4be564bade66d8f72a5d73c3f62e1f6a3e";
  const harness = makeHarness({
    body: "Refs #14\nIssue-Closure: #14",
    commitShas: [pr15MergeSha],
    items: { 14: { number: 14, state: "closed" } },
  });

  assert.deepEqual(await harness.close(), [
    { issueNumber: 14, status: "already-closed" },
  ]);
  assert.equal(harness.calls.update.length, 0);
});
