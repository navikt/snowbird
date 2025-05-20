from click.testing import CliRunner

from snowbird.main import plan


def test_spec_with_uppercase_to_roles_should_not_trigger_grant_and_revoke_of_roles():
    runner = CliRunner()
    result = runner.invoke(
        plan,
        [
            "--config",
            "tests/end_to_end/test_case_insensitive_spec.yml",
            "--state",
            "tests/end_to_end/test_case_insensitive_state.json",
            "--silent",
            "--execution-plan",
        ],
    )
    expected = ""
    assert result.exit_code == 0
    assert result.stdout == expected
