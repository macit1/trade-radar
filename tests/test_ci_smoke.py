"""A deliberately failing test, used once to prove the CI gate actually blocks.

This file exists only on the `feature/ci-smoke` branch and is deleted with it.
If you are reading this on any other branch, something went wrong: delete it.
"""


def test_ci_gate_blocks_a_failing_pull_request():
    stored_bars = 753
    expected_bars = 754  # wrong on purpose

    assert stored_bars == expected_bars, (
        "intentional failure - proving the required status check turns red "
        "and blocks the merge button"
    )
