import json
import os

from invalidation_closure.cli import main


def test_cli_demo(capsys):
    assert main(["demo"]) == 0
    out = capsys.readouterr().out
    assert "Invalidation closure audit" in out
    assert "silently stale" in out


def test_cli_evaluate_writes_all_files(tmp_path):
    out_dir = str(tmp_path / "results")
    assert main(["evaluate", "--out", out_dir]) == 0
    for name in (
        "evaluation.json",
        "evaluation.csv",
        "evaluation_summary.md",
        "HEADLINE.md",
    ):
        assert os.path.isfile(os.path.join(out_dir, name)), name
    with open(os.path.join(out_dir, "evaluation.json")) as fh:
        payload = json.load(fh)
    assert "headline" in payload
    assert "policies" in payload


def test_cli_evaluate_csv_rows(tmp_path):
    out_dir = str(tmp_path / "results")
    assert main(["evaluate", "--out", out_dir]) == 0
    with open(os.path.join(out_dir, "evaluation.csv")) as fh:
        lines = fh.read().strip().splitlines()
    # Header + five policies + oracle control.
    assert len(lines) == 7
    assert lines[0].startswith("policy,completeness")


def test_cli_no_command_prints_help(capsys):
    assert main([]) == 2
    assert "usage" in capsys.readouterr().out.lower()
