"""Tests for ConfigBridge."""

from __future__ import annotations

import argparse

from lucidshark.cli.config_bridge import ConfigBridge


class TestArgsToOverrides:
    """Tests for ConfigBridge.args_to_overrides()."""

    def _make_args(self, **kwargs) -> argparse.Namespace:
        """Build an argparse.Namespace with defaults for all scan command flags."""
        defaults = dict(
            sca=False,
            sast=False,
            iac=False,
            container=False,
            linting=False,
            fix=False,
            images=None,
            fail_on=None,
        )
        merged = {**defaults, **kwargs}
        return argparse.Namespace(**merged)

    def test_linting_flag_sets_pipeline_linting_enabled(self):
        """--linting should set pipeline.linting.enabled = True without hardcoding a tool."""
        args = self._make_args(linting=True)
        overrides = ConfigBridge.args_to_overrides(args)

        assert "pipeline" in overrides
        assert "linting" in overrides["pipeline"]
        assert overrides["pipeline"]["linting"]["enabled"] is True
        # Should NOT hardcode a specific tool - tools come from config or auto-detection
        assert "tools" not in overrides["pipeline"]["linting"]

    def test_linting_does_not_overwrite_existing_tools(self):
        """--linting enables the domain without overriding the configured tool list."""
        args = self._make_args(linting=True)
        overrides = ConfigBridge.args_to_overrides(args)

        # Only sets enabled flag, not a tools list - merge_configs will not
        # clobber any tools from the config file
        linting_cfg = overrides["pipeline"]["linting"]
        assert "enabled" in linting_cfg
        assert "tools" not in linting_cfg

    def test_sca_flag_sets_scanners(self):
        """--sca should enable the SCA scanner."""
        args = self._make_args(sca=True)
        overrides = ConfigBridge.args_to_overrides(args)

        assert "scanners" in overrides
        assert overrides["scanners"]["sca"] == {"enabled": True}

    def test_container_flag_with_images(self):
        """--container with images should set both enabled and images."""
        args = self._make_args(container=True, images=["my-image:latest"])
        overrides = ConfigBridge.args_to_overrides(args)

        assert "scanners" in overrides
        assert overrides["scanners"]["container"] == {
            "enabled": True,
            "images": ["my-image:latest"],
        }

    def test_fix_mode_sets_top_level_flag(self):
        """--fix should set the fix override at top level."""
        args = self._make_args(fix=True)
        overrides = ConfigBridge.args_to_overrides(args)

        assert overrides["fix"] is True

    def test_multiple_security_domains(self):
        """Multiple security flags should all appear in scanners."""
        args = self._make_args(sca=True, sast=True, iac=True)
        overrides = ConfigBridge.args_to_overrides(args)

        assert overrides["scanners"]["sca"] == {"enabled": True}
        assert overrides["scanners"]["sast"] == {"enabled": True}
        assert overrides["scanners"]["iac"] == {"enabled": True}

    def test_empty_args_returns_empty_overrides(self):
        """No flags should return an empty overrides dict."""
        args = self._make_args()
        overrides = ConfigBridge.args_to_overrides(args)

        assert overrides == {}
