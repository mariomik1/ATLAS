from atlas_core.utils.env_loader import load_env_file, mask_secret


def test_load_env_file_without_mutating_process_env(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text('\n# comment\nFMP_API_KEY="abc12345"\nEMPTY=\nMARKETAUX_API_KEY=xyz\n', encoding="utf-8")

    values = load_env_file(env_file)

    assert values["FMP_API_KEY"] == "abc12345"
    assert values["MARKETAUX_API_KEY"] == "xyz"
    assert values["EMPTY"] == ""


def test_mask_secret_hides_value():
    assert mask_secret(None) == "missing"
    assert mask_secret("abcdef123456").endswith("3456")
    assert "abcdef" not in mask_secret("abcdef123456")
