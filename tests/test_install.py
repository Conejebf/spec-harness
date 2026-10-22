import json
import subprocess
import sys

from conftest import REPO, write


def _install(target, *flags):
    return subprocess.run([sys.executable, str(REPO / "install.py"), str(target), *flags],
                          capture_output=True, text=True, encoding="utf-8", check=True)


def test_install_is_idempotent_and_respects_foreign_hooks(tmp_path):
    foreign = {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "python otro.py"}]}]}, "model": "x"}
    write(tmp_path / ".claude" / "settings.json", json.dumps(foreign))
    write(tmp_path / "CLAUDE.md", "# Mi proyecto\n")
    write(tmp_path / ".claude" / "steering" / "tech.md", "mío")
    _install(tmp_path)
    _install(tmp_path)
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert len(settings["hooks"]["Stop"]) == 2 and settings["model"] == "x"
    assert len(settings["hooks"]["SessionStart"]) == 1
    claude = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert claude.count("spec-harness:start") == 1 and claude.startswith("# Mi proyecto")
    assert (tmp_path / ".claude" / "steering" / "tech.md").read_text(encoding="utf-8") == "mío"
    assert (tmp_path / ".claude" / "skills" / "spec-run" / "SKILL.md").is_file()
    assert (tmp_path / ".claude" / "spec_harness" / "hooks.py").is_file()


def test_uninstall_keeps_specs_and_foreign_config(tmp_path):
    write(tmp_path / ".claude" / "settings.json", json.dumps({"hooks": {"Stop": [{"hooks": [{"command": "x"}]}]}}))
    write(tmp_path / "CLAUDE.md", "# Mi proyecto\n")
    _install(tmp_path)
    write(tmp_path / "specs" / "a" / "requirements.md", "x")
    _install(tmp_path, "--uninstall")
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert settings == {"hooks": {"Stop": [{"hooks": [{"command": "x"}]}]}}
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == "# Mi proyecto\n"
    assert not (tmp_path / ".claude" / "spec_harness").exists()
    assert not (tmp_path / ".claude" / "skills" / "spec-run").exists()
    assert (tmp_path / "specs" / "a" / "requirements.md").is_file()
    assert (tmp_path / ".claude" / "steering" / "product.md").is_file()


def test_installed_cli_finds_project_root(tmp_path):
    _install(tmp_path)
    out = subprocess.run([sys.executable, str(tmp_path / ".claude" / "spec_harness" / "cli.py"), "new", "demo"],
                         capture_output=True, text=True, encoding="utf-8", cwd=REPO, check=False)
    assert out.returncode == 0, out.stderr
    assert (tmp_path / "specs" / "demo").is_dir()
