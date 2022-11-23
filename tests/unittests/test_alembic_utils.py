import pytest

from alembic_utils.utils import check_scripts_do_not_have_conflicts


@pytest.mark.parametrize(
    "head,num_files,squashed_migration,exception",
    [(1, 2, None, None), (2, 1, None, Exception), (48, 1, 48, None)],
)
def test_check_scripts_do_not_have_conflicts(
    monkeypatch, head, num_files, squashed_migration, exception
):
    """Revisions starts from 0, so there has to be 2 files for revision 1 to
    be ok"""

    from alembic_utils import utils

    monkeypatch.setattr(utils.script, "get_current_head", lambda *args, **kwargs: head)
    monkeypatch.setattr(utils, "get_all_script_files", lambda: range(num_files))
    if exception:
        with pytest.raises(Exception):
            check_scripts_do_not_have_conflicts(squashed_migration=squashed_migration)
    else:
        check_scripts_do_not_have_conflicts(squashed_migration=squashed_migration)
