#!/usr/bin/env node
// PreToolUse hook: blocks command chaining in Bash tool calls
// Detects &&/|| which violate AGENTS.md: "execute exactly one command per tool call"
// Once https://github.com/anthropics/claude-code/issues/16561 is resolved, this should no longer be necessary

let input = "";
process.stdin.on("data", (chunk) => {
  input += chunk;
});
process.stdin.on("end", () => {
  try {
    const data = JSON.parse(input);
    const command = (data.tool_input?.command || "").trim();

    if (/\s(&&|\|\||;)\s|\s&(\s|$)/.test(command)) {
      process.stderr.write(
        "AGENTS.md violation: never chain commands with &&, ||, ;, or &. " +
          "Run one command per tool call. " +
          "Use cd as a separate prior tool call instead of cd && ...",
      );
      process.exit(2);
    }
  } catch (e) {
    // Silent fail — never block on hook errors
  }
});
