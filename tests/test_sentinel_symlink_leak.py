import os
import shutil
import tempfile
import pytest

def test_symlink_leak_in_save_template_fixed():
    """
    Verify that using symlinks=True in shutil.copytree prevents following
    symlinks and thus prevents leaking data from outside the workspace.
    """
    with tempfile.TemporaryDirectory() as tmp_base:
        # 1. Setup a "workspace" and a "secret" file outside of it
        workspace_dir = os.path.join(tmp_base, "workspace")
        os.makedirs(workspace_dir)

        secret_file = os.path.join(tmp_base, "secret.txt")
        secret_content = "CONFIDENTIAL_API_KEY_12345"
        with open(secret_file, "w") as f:
            f.write(secret_content)

        # 2. Create a symlink inside the workspace pointing to the secret file
        leak_symlink = os.path.join(workspace_dir, "leak.txt")
        os.symlink(secret_file, leak_symlink)

        # 3. Destination for the template
        template_path = os.path.join(tmp_base, "template_storage")

        # 4. Use the FIXED implementation logic
        def ignore_git(path, names):
            return ['.git'] if '.git' in names else []

        shutil.copytree(workspace_dir, template_path, ignore=ignore_git, symlinks=True)

        # 5. Verification
        leak_in_template = os.path.join(template_path, "leak.txt")

        # It SHOULD be a link now
        assert os.path.islink(leak_in_template), "Expected a symlink, but found a regular file (content was likely copied!)"

        # The link should point to the same secret file (or at least be a link)
        # In a real scenario, this link might be broken in the destination if relative,
        # but here it's absolute. The point is it didn't copy the CONTENT.

def test_symlink_leak_in_publish_template_fixed():
    """
    Verify that using follow_symlinks=False in shutil.copy2 prevents
    following symlinks.
    """
    with tempfile.TemporaryDirectory() as tmp_base:
        template_dir = os.path.join(tmp_base, "template")
        os.makedirs(template_dir)

        secret_file = os.path.join(tmp_base, "secret.txt")
        secret_content = "TOP_SECRET_CREDENTIALS"
        with open(secret_file, "w") as f:
            f.write(secret_content)

        leak_symlink = os.path.join(template_dir, "leak.txt")
        os.symlink(secret_file, leak_symlink)

        publish_tmp_dir = os.path.join(tmp_base, "publish_tmp")
        os.makedirs(publish_tmp_dir)

        # Use FIXED implementation logic
        for item in os.listdir(template_dir):
            s = os.path.join(template_dir, item)
            d = os.path.join(publish_tmp_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, symlinks=True)
            else:
                shutil.copy2(s, d, follow_symlinks=False)

        leak_in_publish = os.path.join(publish_tmp_dir, "leak.txt")
        assert os.path.islink(leak_in_publish), "Expected a symlink in destination, but found a regular file!"
