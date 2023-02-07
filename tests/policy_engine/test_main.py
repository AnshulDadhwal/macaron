# Copyright (c) 2023 - 2023, Oracle and/or its affiliates. All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/.

"""This module tests the policy parser."""

import os
import subprocess  # nosec B404
from pathlib import Path
from unittest import TestCase

from macaron.policy_engine.__main__ import Config, get_generated, policy_engine


class TestSoufflePolicyEngineMain(TestCase):
    """This class tests the Policy Parser."""

    POLICY_DIR = Path(__file__).parent.joinpath("resources").joinpath("policies")
    POLICY_FILE = os.path.join(POLICY_DIR, "testpolicy.dl")
    DATABASE_FILE = os.path.join(Path(__file__).parent.joinpath("resources", "facts", "macaron.db"))

    @classmethod
    def setUpClass(cls) -> None:
        if not os.path.exists(cls.DATABASE_FILE):
            if os.path.exists(cls.DATABASE_FILE + ".gz"):
                subprocess.run(["gunzip", "-k", cls.DATABASE_FILE + ".gz"], check=True, shell=False)  # nosec B603 B607

    def test_dump_prelude(self) -> None:
        """Test loading the policy from file."""
        res = get_generated(self.DATABASE_FILE)
        assert len(res) > 10

    def test_eval_policy(self) -> None:
        """Test loading the policy from file."""
        conf = Config
        conf.database_path = os.path.join(self.POLICY_FILE, self.DATABASE_FILE)
        conf.show_prelude = False
        conf.policy_file = self.POLICY_FILE
        res = policy_engine(conf, conf.policy_file)
        assert res == {
            "passed_policies": [
                ["trusted_builder", "1", "slsa-framework/slsa-verifier"],
                ["trusted_git_server", "1", "slsa-framework/slsa-verifier"],
            ],
            "failed_policies": [],
        }