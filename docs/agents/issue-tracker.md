# Issue tracker: GitHub

Issues and PRDs for this repo live as GitHub Issues on **`khanhkhmt/llm_oriagent`**. Use the `gh` CLI for all operations.

> **Note:** This repo has two remotes. `origin` points at the upstream `open-webui/open-webui` — do **not** create issues there. Always pass `--repo khanhkhmt/llm_oriagent` explicitly.

## Conventions

- **Create an issue**: `gh issue create --repo khanhkhmt/llm_oriagent --title "..." --body "..."`. Use a heredoc for multi-line bodies.
- **Read an issue**: `gh issue view <number> --repo khanhkhmt/llm_oriagent --comments`
- **List issues**: `gh issue list --repo khanhkhmt/llm_oriagent --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` with appropriate `--label` and `--state` filters.
- **Comment on an issue**: `gh issue comment <number> --repo khanhkhmt/llm_oriagent --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --repo khanhkhmt/llm_oriagent --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --repo khanhkhmt/llm_oriagent --comment "..."`

## When a skill says "publish to the issue tracker"

Create a GitHub issue on `khanhkhmt/llm_oriagent`.

## When a skill says "fetch the relevant ticket"

Run `gh issue view <number> --repo khanhkhmt/llm_oriagent --comments`.
