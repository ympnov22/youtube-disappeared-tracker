#!/usr/bin/env python3
"""
YouTube Disappeared Video Tracker - Session Rehydration Script

This script reads the continuity documentation and session state to generate
a ready-to-use kickstart prompt for the next Devin session.

Usage:
    python scripts/rehydrate.py
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def load_session_state() -> Dict[str, Any]:
    """Load the current session state from JSON file."""
    state_file = Path("state/session_state.json")
    if not state_file.exists():
        raise FileNotFoundError(
            "Session state file not found. " "Run this script from the project root."
        )

    with open(state_file, "r") as f:
        return json.load(f)  # type: ignore[no-any-return]


def load_continuity_doc() -> str:
    """Load the continuity documentation."""
    continuity_file = Path("docs/CONTINUITY.md")
    if not continuity_file.exists():
        raise FileNotFoundError("Continuity documentation not found.")

    with open(continuity_file, "r") as f:
        return f.read()


def generate_kickstart_prompt(state: Dict[str, Any], continuity_content: str) -> str:
    """Generate the kickstart prompt for the next session."""

    current_phase = state["current_phase"]
    next_actions = state["next_actions"]
    blockers = state["blockers"]
    git_status = state["git_status"]
    deployment = state["deployment"]

    if current_phase["status"] == "complete" and blockers:
        session_focus = "Resolve blockers and proceed to next phase"
    elif current_phase["status"] == "in_progress":
        session_focus = f"Continue Phase {current_phase['number']} implementation"
    else:
        next_phase_num = current_phase["number"] + 1
        session_focus = f"Begin Phase {next_phase_num} implementation"

    actions_text = ""
    for i, action in enumerate(next_actions[:3], 1):
        owner_icon = "👤" if action["owner"] == "user" else "🤖"
        blocking_text = " (BLOCKING)" if action.get("blocking", False) else ""
        actions_text += f"{i}. {owner_icon} {action['description']}{blocking_text}\n"

    blockers_text = ""
    if blockers:
        for blocker in blockers:
            severity_icon = "🔴" if blocker["severity"] == "high" else "🟡"
            blockers_text += f"- {severity_icon} {blocker['description']}\n"
    else:
        blockers_text = "- ✅ No current blockers\n"

    session_id = state["session_info"]["session_id"]
    phase_num = current_phase["number"]
    phase_name = current_phase["name"]
    phase_status = current_phase["status"].title()
    current_branch = git_status["current_branch"]
    commit_hash = git_status["last_commit"]["hash"]
    commit_msg = git_status["last_commit"]["message"]
    deploy_status = deployment["status"].replace("_", " ").title()

    prompt = f"""# YouTube Disappeared Video Tracker - Session Kickstart

**Project**: YouTube Disappeared Video Tracker
**Repository**: `/home/ubuntu/youtube-disappeared-tracker/`
**GitHub**: ympnov22/youtube-disappeared-tracker
**Devin Session**: https://app.devin.ai/sessions/{session_id}

**Phase**: {phase_num} - {phase_name}
**Status**: {phase_status}
**Branch**: `{current_branch}`
**Last Commit**: `{commit_hash}` - {commit_msg}
**Deploy Status**: {deploy_status}

{session_focus}

{actions_text}

{blockers_text}

- **Current Branch**: `{git_status['current_branch']}`
- **Uncommitted Changes**: {
        'Yes' if git_status['uncommitted_changes'] else 'No'
    }
- **Unpushed Commits**: {git_status['unpushed_commits']}
- **Remote Origin**: {git_status['remote_origin'] or 'Not configured'}

- **Development Ready**: {
        '✅' if state['environment']['development_ready'] else '❌'
    }
- **Docker Ready**: {'✅' if state['environment']['docker_ready'] else '❌'}
- **CI/CD Ready**: {'✅' if state['environment']['ci_cd_ready'] else '❌'}

- `docs/specification.md` - Technical specification
- `docs/phases.md` - Development phases breakdown
- `docs/CONTINUITY.md` - Current session state
- `docs/CHANGELOG.md` - Phase completion history
- `state/session_state.json` - Machine-readable state

Based on current state, the next session should focus on:

- [ ] Resolve any blocking issues
- [ ] Complete current phase deliverables
- [ ] Update documentation and state files

- [ ] Get user approval for completed work
- [ ] Proceed to next phase implementation
- [ ] Maintain bilingual documentation requirements

- **Bilingual Requirement**: PRs and reports need English + Japanese
  translations
- **User Approval Required**: Each phase needs explicit user approval
  before proceeding
- **Quality Standards**: Maintain 80%+ test coverage, pass all linting
- **Session Handoffs**: Update continuity docs at end of each session

```
/app                    # Application code
  /api                  # API endpoints
  /core                 # Core business logic
  /jobs                 # Background jobs
  /models               # Data models
  /services             # External services
  /web                  # Web UI
/tests                  # Test files
/docs                   # Documentation
/state                  # Session state files
/scripts                # Utility scripts
/.github                # GitHub templates
```

---

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Last Updated**: {state['session_info']['last_updated']}

Use this information to quickly understand the project state and continue
development.
"""

    return prompt


def main() -> int:
    """Main function to generate and display the kickstart prompt."""
    try:
        state = load_session_state()
        continuity_content = load_continuity_doc()

        prompt = generate_kickstart_prompt(state, continuity_content)

        print("=" * 80)
        print("DEVIN SESSION KICKSTART PROMPT")
        print("=" * 80)
        print()
        print(prompt)
        print()
        print("=" * 80)
        print("Copy the above content to start your next Devin session")
        print("=" * 80)

        output_file = Path("state/kickstart_prompt.md")
        with open(output_file, "w") as f:
            f.write(prompt)

        print(f"\nPrompt also saved to: {output_file}")

    except Exception as e:
        print(f"Error generating kickstart prompt: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
