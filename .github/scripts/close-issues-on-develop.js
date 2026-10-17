"use strict";

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

async function closeMarkedIssues({ github, context, core }) {
  const pullRequest = context.payload.pull_request;
  if (!pullRequest?.merged || pullRequest.base?.ref !== "develop") {
    core.info("Skipping: the pull request was not merged into develop.");
    return [];
  }

  const issueNumbers = extractIssueNumbers(pullRequest.body);
  if (issueNumbers.length === 0) {
    core.info("No Issue-Closure markers found.");
    return [];
  }

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

    await github.rest.issues.update({
      owner,
      repo,
      issue_number: issueNumber,
      state: "closed",
      state_reason: "completed",
    });
    core.info(`Closed Issue #${issueNumber} as completed.`);
    results.push({ issueNumber, status: "closed" });
  }

  return results;
}

module.exports = {
  closeMarkedIssues,
  extractIssueNumbers,
};
