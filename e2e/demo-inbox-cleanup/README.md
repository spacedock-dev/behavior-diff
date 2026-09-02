# Output-diff smoke case — inbox cleanup

Emma gets hundreds of emails. Every morning, her agent archives messages that
match her saved inbox rules. This saves Emma from sorting the same kinds of
email by hand.

Her current rule archives newsletters. Emma wants the agent to remove more
routine messages, so she considers this broader rule:

> Also archive an automated message when it does not ask Emma to reply or take
> action.

The rule sounds reasonable. Its consequence is hard to predict because many
different emails are automated. Emma uses behavior-diff before accepting the
rule. She wants to see which messages would disappear from her inbox every
morning.

## The story on one screen

The task and inbox stay the same. Only the proposed rule changes.

| Message | Before | After | What Emma wanted |
|---|---|---|---|
| Weekly newsletter | `ARCHIVE` | `ARCHIVE` | Archive |
| Parcel delivered | `KEEP` | `ARCHIVE` | Archive |
| Tonight's class cancelled | `KEEP` | `ARCHIVE` | **Keep** |
| Friend asks to move dinner | `KEEP` | `KEEP` | Keep |

The new rule has the intended effect on the parcel update. It also hides the
important cancellation notice. Emma can now reject or narrow the rule before
it controls her real inbox.

This fixture shows a concrete output consequence, but it does not create a
meaningful behavior route. Both agents only classify messages. Use
`demo-invoice-review` when the audience needs to see different evidence,
decisions, and business results.

## Instruction-file layout

`project/AGENTS.md` is the canonical project instruction file. It contains
stable project context and the current recurring rule. `project/CLAUDE.md`
only imports `AGENTS.md`, so both supported agents use the same rules.

The fixture is synthetic. It contains no real email or personal data.

## Run the journey

From the repository root:

    NUDGE_E2E_FIXTURE=demo-inbox-cleanup behavior-diff/tests/nudge-e2e.sh setup

The setup command prints the isolated session command, the proposed rule, and
the neutral task. To run behavior-diff directly in the prepared sandbox:

    cd /tmp/nudge-e2e
    behavior-diff /path/to/engram/behavior-diff/e2e/demo-inbox-cleanup/rule.md \
      --into AGENTS.md \
      --task "$(cat /path/to/engram/behavior-diff/e2e/demo-inbox-cleanup/task.md)" \
      --fast

`--fast` runs one trial per side. It can show the story shape, but it cannot
prove that the same result will happen consistently. The table above is the
fixture's expected case shape, not a guaranteed model result.
