# ============== WARNING ==============================================================================
# File is managed by copier template: gh:LabAutomationAndScreening/copier-base-template.git
# See .config/.copier-managed-files.json for details.
#
# You are welcome to make changes to this file in your repo if they are custom to your project,
# but if the change should be shared with other projects, please backport it to the template repo.
# =====================================================================================================
import pytest

# pytest only rewrites asserts in the modules it collects as tests (plus conftest and registered plugins), so
# an assert reached through fixtures.py/helpers.py reports a bare AssertionError with no diff unless its
# module is registered here, so a new top-level test package needs adding to this list. The subpackages are
# named individually rather than registering `tests`, which is already imported by the time this conftest runs
# and would only warn.
pytest.register_assert_rewrite("tests.unit")
