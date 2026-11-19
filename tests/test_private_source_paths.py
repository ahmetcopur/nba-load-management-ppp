from pathlib import Path
import subprocess
import tempfile
import unittest
from scripts.data_rebuild.private_source_paths import under_git


class PrivatePathTests(unittest.TestCase):
    def test_actual_git_repository_is_rejected_even_for_ignored_nonexistent_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);repo=root/'repo';repo.mkdir()
            subprocess.run(['git','init','-q',str(repo)],check=True)
            (repo/'.gitignore').write_text('private/\n')
            self.assertTrue(under_git(repo/'private'/'never_created.csv'))
            self.assertFalse(under_git(root/'outside_repository'/'private.csv'))

    def test_worktree_marker_and_symlink_into_git_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);work=root/'worktree';work.mkdir()
            (work/'.git').write_text('gitdir: ../metadata/worktrees/worktree\n')
            self.assertTrue(under_git(work/'private.csv'))
            (root/'alias').symlink_to(work,target_is_directory=True)
            self.assertTrue(under_git(root/'alias'/'private.csv'))

    def test_empty_nonrepository_marker_matches_existing_canonical_boundary_rule(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'.git').mkdir()
            self.assertFalse(under_git(root/'private'/'new.csv'))
            (root/'.git'/'HEAD').write_text('ref: refs/heads/main\n')
            self.assertTrue(under_git(root/'private'/'new.csv'))


if __name__=='__main__':unittest.main()
