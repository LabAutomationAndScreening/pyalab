#!/usr/bin/env node
// PreToolUse hook: blocks command chaining in Bash tool calls
// Enforces AGENTS.md: "execute exactly one command per tool call"
// Quoted spans and backslash-escapes are replaced with a space before scanning, so a `;` inside a
// string literal (or the trailing `\;` of `find -exec`) is not mistaken for a chain. Replacing with
// a space rather than deleting keeps tokens separate, so `printf hi >\x&` cannot collapse to
// `printf hi >&` and hide the backgrounding `&` behind the redirection lookbehind.
// Once https://github.com/anthropics/claude-code/issues/16561 is resolved, this should no longer be necessary
// Improvements based on https://github.com/iandunn/dotfiles/blob/main/claude/hooks/block-chained-commands.js

const CHAIN_OPERATORS = /&&|\|\||;/; // a single `|` is a pipe, which is allowed
const BACKGROUND_AMPERSAND = /(?<![<>])&(?!>)/; // a lone `&` backgrounds the command, but `2>&1` and `&>file` are redirections

function stripQuotedAndEscaped(command) {
  return command.replace(/\\.|'[^']*'|"(?:\\.|[^"\\])*"/g, " ");
}

let input = "";
process.stdin.on("data", (chunk) => {
  input += chunk;
});
process.stdin.on("end", () => {
  try {
    const data = JSON.parse(input);
    const command = (data.tool_input?.command || "").trim();
    const scannable = stripQuotedAndEscaped(command);

    if (CHAIN_OPERATORS.test(scannable)) {
      process.stderr.write(
        "AGENTS.md violation: never chain commands with &&, ||, or ;. " +
          "Run one command per tool call. " +
          "Use cd as a separate prior tool call instead of cd && ...",
      );
      process.exit(2);
    }

    if (BACKGROUND_AMPERSAND.test(scannable)) {
      process.stderr.write(
        "AGENTS.md violation: never background a command with &. " +
          "Use the Bash tool's run_in_background option instead.",
      );
      process.exit(2);
    }
  } catch (e) {
    // Silent fail — never block on hook errors
  }
});

/*
 * ============== WARNING ==============================================================================
 * File is managed by copier template: gh:LabAutomationAndScreening/copier-base-template.git
 * See .config/.copier-managed-files.json for details.
 *
 * You are welcome to make changes to this file in your repo if they are custom to your project,
 * but if the change should be shared with other projects, please backport it to the template repo.
 * =====================================================================================================
 */
