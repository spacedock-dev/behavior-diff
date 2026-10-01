# Git history fixtures

**Recorded:** 2026-09-30
**Version discussed:** Behavior Diff v0.3.8
**Status:** Proposal. Not approved for implementation.
**Source:** Skill history replay workflow, case `daymade-git-safety-net-18174c8` (parked at `intent`).

## Main finding

Behavior Diff cannot replay a skill whose decision depends on git state.
Each trial project starts as a fresh repository with one commit, no remote,
and no branch history. Branches, remotes, and divergence that a fixture
builds never reach the agent.

The runner builds each trial like this (`plugin/skills/behavior-diff/scripts/behavior-diff.sh`):

1. `git archive HEAD | tar -x` copies only the files of `HEAD` (line 236).
2. `git init`, then one "snapshot for behavior diff" commit (line 253).

```
fixture repo                       trial project (what the agent sees)
main  [ahead 1, behind 2]    ──►   master, 1 snapshot commit
origin = local bare repo     ──►   no remote
git cherry → "-"             ──►   nothing to compare
```

This choice is deliberate. It keeps the user's real repository history and
remotes out of every trial. The proposal must keep that property.

## Who is affected

Skills whose key decision reads git state:

- branch safety and recovery (diverged branches, force-push guards);
- rebase, merge, and cherry-pick choices;
- "what changed since main" review and PR preparation;
- release and changelog work that reads tags or commit ranges.

Today every such skill shows no difference in a report, because no trial can
reach its decision moment.

## Proposed change

Let a fixture opt in to keeping its own git history in each trial.

1. **Keep the fixture's history, not the user's.** The history comes only
   from a dedicated fixture repository that the run prepares. It never
   comes from the user's working repository.
2. **Local remotes only.** Every remote in a trial must be a local path, such
   as a bare repository created for the run. A remote with a network URL
   fails the run before any trial starts.
3. **Identical on both sides.** Before and After trials get the same history,
   branches, and remotes. Only the instruction file differs, as today.
4. **Default unchanged.** Without the opt-in, trials keep today's archive and
   `git init` behavior.

## Acceptance case

The parked case is the first test the feature must pass:

- Skill: `daymade/claude-code-skills` `git-safety-net/SKILL.md`,
  Before `d9289a3` → After `18174c8` (PR #739).
- Fixture: a local bare repository as `origin`, and a branch that is ahead 1
  and behind 2 of `origin/main`. Its one local commit is patch-identical to
  one of the two upstream commits. `git cherry origin/main main` prints a
  single `-` line.
- Pass: in every trial, before the agent's first action, `git status` shows
  the branch ahead 1 and behind 2, and `git cherry` prints the same single
  `-` line.

The pilot built this fixture and confirmed that `git cherry` gives the
expected output. It also replayed the runner steps, which confirmed that the
history is lost.

## Out of scope

- Network remotes or real hosting accounts.
- Copying the user's own repository history into trials.
- Changing how Behavior Diff drafts its task.

## Open questions

- Should the opt-in be a runner flag, or a marker file in the fixture?
- Should the report show the starting git state, so a reader can see what the
  agent saw?
