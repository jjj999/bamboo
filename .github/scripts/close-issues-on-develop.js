"use strict";

const TARGET_BRANCH = "develop";
const TARGET_REF = `refs/heads/${TARGET_BRANCH}`;
const ZERO_SHA = "0".repeat(40);
const PER_PAGE = 100;

function stripHtmlComments(line, inComment) {
  let remaining = line;
  let output = "";

  while (remaining.length > 0) {
    if (inComment) {
      const end = remaining.indexOf("-->");
      if (end === -1) {
        return { line: output, inComment: true };
      }
      remaining = remaining.slice(end + 3);
      inComment = false;
      continue;
    }

    const start = remaining.indexOf("<!--");
    if (start === -1) {
      output += remaining;
      break;
    }

    output += remaining.slice(0, start);
    remaining = remaining.slice(start + 4);
    inComment = true;
  }

  return { line: output, inComment };
}

function extractIssueNumbers(body) {
  const numbers = new Set();
  let fence = null;
  let inHtmlComment = false;

  for (const originalLine of String(body || "").split(/\r?\n/)) {
    const fenceMatch = originalLine.match(/^ {0,3}(`{3,}|~{3,})/);
    if (fenceMatch) {
      const marker = fenceMatch[1];
      if (fence === null) {
        fence = { character: marker[0], length: marker.length };
      } else if (
        marker[0] === fence.character &&
        marker.length >= fence.length
      ) {
        fence = null;
      }
      continue;
    }

    if (fence !== null || /^\s*>/.test(originalLine)) {
      continue;
    }

    const stripped = stripHtmlComments(originalLine, inHtmlComment);
    inHtmlComment = stripped.inComment;
    const line = stripped.line;

    if (/^(?: {4}|\t)/.test(line)) {
      continue;
    }

    const match = line.match(/^ {0,3}Issue-Closure:\s*#([1-9]\d*)\s*$/);
    if (match) {
      numbers.add(Number(match[1]));
    }
  }

  return [...numbers];
}

function reportApiError(core, operation, error) {
  const detail = error instanceof Error ? error.message : String(error);
  const message = `${operation}: ${detail}`;
  if (typeof core.error === "function") {
    core.error(message);
  } else {
    core.warning(message);
  }
}

async function getPushedCommitShas({ github, context, core }) {
  const payload = context.payload;
  if (context.eventName !== "push" || payload.ref !== TARGET_REF) {
    core.info("Skipping: this is not a push to develop.");
    return [];
  }
  if (payload.deleted || payload.created) {
    core.warning("Skipping: branch creation and deletion pushes are not eligible.");
    return [];
  }
  if (payload.forced) {
    core.warning("Skipping: force pushes cannot safely identify newly merged PRs.");
    return [];
  }

  const before = payload.before;
  const after = payload.after;
  if (!before || !after || before === ZERO_SHA || after === ZERO_SHA) {
    core.warning("Skipping: the push does not contain a comparable commit range.");
    return [];
  }

  const { owner, repo } = context.repo;
  const commits = [];
  let totalCommits;

  try {
    for (let page = 1; ; page += 1) {
      const response = await github.rest.repos.compareCommitsWithBasehead({
        owner,
        repo,
        basehead: `${before}...${after}`,
        per_page: PER_PAGE,
        page,
      });
      const pageCommits = response.data.commits || [];
      totalCommits = response.data.total_commits ?? totalCommits;
      commits.push(...pageCommits.map((commit) => commit.sha));

      if (
        pageCommits.length < PER_PAGE ||
        (totalCommits !== undefined && commits.length >= totalCommits)
      ) {
        break;
      }
    }
  } catch (error) {
    reportApiError(core, `Failed to compare push range ${before}...${after}`, error);
    throw error;
  }

  const uniqueCommits = [...new Set(commits)];
  if (totalCommits !== undefined && uniqueCommits.length < totalCommits) {
    const error = new Error(
      `Commit comparison returned ${uniqueCommits.length} of ${totalCommits} commits.`,
    );
    reportApiError(core, "Incomplete push commit discovery", error);
    throw error;
  }
  if (!uniqueCommits.includes(after)) {
    const error = new Error("The push head is missing from the commit comparison.");
    reportApiError(core, "Incomplete push commit discovery", error);
    throw error;
  }

  core.info(
    `Discovered ${uniqueCommits.length} commit(s) in push ${before}...${after}.`,
  );
  return uniqueCommits;
}

async function findMergedPullRequestsForPush({
  github,
  context,
  core,
  commitShas,
}) {
  const { owner, repo } = context.repo;
  const commitSet = new Set(commitShas);
  const candidateNumbers = new Set();

  for (const commitSha of commitShas) {
    try {
      for (let page = 1; ; page += 1) {
        const response =
          await github.rest.repos.listPullRequestsAssociatedWithCommit({
            owner,
            repo,
            commit_sha: commitSha,
            per_page: PER_PAGE,
            page,
          });
        const pullRequests = response.data || [];
        for (const pullRequest of pullRequests) {
          candidateNumbers.add(pullRequest.number);
        }
        if (pullRequests.length < PER_PAGE) {
          break;
        }
      }
    } catch (error) {
      reportApiError(
        core,
        `Failed to list pull requests associated with commit ${commitSha}`,
        error,
      );
      throw error;
    }
  }

  if (candidateNumbers.size === 0) {
    core.info("No pull requests are associated with this push.");
    return [];
  }

  const repositoryName = `${owner}/${repo}`.toLowerCase();
  const pullRequests = [];
  for (const pullNumber of candidateNumbers) {
    let pullRequest;
    try {
      const response = await github.rest.pulls.get({
        owner,
        repo,
        pull_number: pullNumber,
      });
      pullRequest = response.data;
    } catch (error) {
      reportApiError(core, `Failed to fetch pull request #${pullNumber}`, error);
      throw error;
    }

    const baseRepository = pullRequest.base?.repo?.full_name?.toLowerCase();
    const isCurrentMerge =
      pullRequest.merged === true &&
      Boolean(pullRequest.merged_at) &&
      pullRequest.base?.ref === TARGET_BRANCH &&
      baseRepository === repositoryName &&
      commitSet.has(pullRequest.merge_commit_sha);

    if (!isCurrentMerge) {
      core.info(
        `Skipping PR #${pullNumber}: it is not a merge into develop from this push.`,
      );
      continue;
    }

    core.info(
      `Matched PR #${pullNumber} to merge commit ${pullRequest.merge_commit_sha}.`,
    );
    pullRequests.push(pullRequest);
  }

  return pullRequests;
}

async function closeIssueNumbers({ github, context, core, issueNumbers }) {
  const results = [];
  const { owner, repo } = context.repo;

  for (const issueNumber of issueNumbers) {
    let item;
    try {
      const response = await github.rest.issues.get({
        owner,
        repo,
        issue_number: issueNumber,
      });
      item = response.data;
    } catch (error) {
      if (error.status === 404) {
        core.warning(`Skipping #${issueNumber}: Issue does not exist.`);
        results.push({ issueNumber, status: "missing" });
        continue;
      }
      reportApiError(core, `Failed to fetch Issue #${issueNumber}`, error);
      throw error;
    }

    if (item.pull_request) {
      core.warning(`Skipping #${issueNumber}: number belongs to a pull request.`);
      results.push({ issueNumber, status: "pull-request" });
      continue;
    }

    if (item.state !== "open") {
      core.info(`Skipping #${issueNumber}: Issue is already closed.`);
      results.push({ issueNumber, status: "already-closed" });
      continue;
    }

    try {
      await github.rest.issues.update({
        owner,
        repo,
        issue_number: issueNumber,
        state: "closed",
        state_reason: "completed",
      });
    } catch (error) {
      reportApiError(core, `Failed to close Issue #${issueNumber}`, error);
      throw error;
    }
    core.info(`Closed Issue #${issueNumber} as completed.`);
    results.push({ issueNumber, status: "closed" });
  }

  return results;
}

async function closeMarkedIssues({ github, context, core }) {
  const commitShas = await getPushedCommitShas({ github, context, core });
  if (commitShas.length === 0) {
    return [];
  }

  const pullRequests = await findMergedPullRequestsForPush({
    github,
    context,
    core,
    commitShas,
  });
  const issueNumbers = new Set();

  for (const pullRequest of pullRequests) {
    const markedIssues = extractIssueNumbers(pullRequest.body);
    if (markedIssues.length === 0) {
      core.info(`PR #${pullRequest.number} has no Issue-Closure markers.`);
      continue;
    }
    for (const issueNumber of markedIssues) {
      issueNumbers.add(issueNumber);
    }
  }

  return closeIssueNumbers({
    github,
    context,
    core,
    issueNumbers: [...issueNumbers],
  });
}

module.exports = {
  closeIssueNumbers,
  closeMarkedIssues,
  extractIssueNumbers,
  findMergedPullRequestsForPush,
  getPushedCommitShas,
};
