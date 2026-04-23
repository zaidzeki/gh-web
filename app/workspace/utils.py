import os
import json
import jinja2
from jinja2.sandbox import SandboxedEnvironment

def is_safe_path(basedir, path, follow_symlinks=True):
    basedir = os.path.realpath(basedir)
    if follow_symlinks:
        matchpath = os.path.realpath(path)
    else:
        matchpath = os.path.abspath(path)

    if os.path.commonpath([basedir, matchpath]) != basedir:
        return False

    # Prevent access to .git directory and its contents
    rel_path = os.path.relpath(matchpath, basedir)
    parts = rel_path.split(os.sep)
    if '.git' in parts:
        return False

    return True

def get_template_manifest(template_path):
    manifest_path = os.path.join(template_path, 'manifest.json')
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    return None

def render_template_dir(source_path, target_path, context, is_safe_path_func=None, workspace_root=None):
    """
    Recursively renders a template directory into a target directory.
    - source_path: Path to the template source
    - target_path: Path to the destination (e.g. workspace)
    - context: Dictionary of variables for rendering
    - is_safe_path_func: Optional function to validate safety of rendered paths
    - workspace_root: Root directory for safety validation
    """
    env = SandboxedEnvironment()

    for root, dirs, files in os.walk(source_path):
        # Calculate relative path from source
        rel_root = os.path.relpath(root, source_path)

        # Render directory names
        for d in dirs:
            rendered_dirname = env.from_string(d).render(context)
            # We don't create them here, but we'll use them in the next iteration's 'root'
            pass

        for f in files:
            if f == 'manifest.json' and rel_root == '.':
                continue

            source_file_path = os.path.join(root, f)

            # Render the relative path
            rel_file_path = os.path.join(rel_root, f)
            rendered_rel_path = env.from_string(rel_file_path).render(context)

            dest_file_path = os.path.join(target_path, rendered_rel_path)

            # Safety check
            if is_safe_path_func and workspace_root:
                if not is_safe_path_func(workspace_root, dest_file_path):
                    continue # Skip unsafe paths

            os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)

            # Determine if we should render content
            should_render = True
            # Basic check for text files
            ext = os.path.splitext(f)[1].lower()
            binary_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip', '.tar', '.gz', '.exe', '.bin']
            if ext in binary_extensions:
                should_render = False

            try:
                if should_render:
                    with open(source_file_path, 'r', encoding='utf-8', errors='replace') as sf:
                        content = sf.read()
                    rendered_content = env.from_string(content).render(context)
                    with open(dest_file_path, 'w', encoding='utf-8') as df:
                        df.write(rendered_content)
                else:
                    import shutil
                    shutil.copy2(source_file_path, dest_file_path)
            except Exception:
                # Fallback to direct copy on error
                import shutil
                shutil.copy2(source_file_path, dest_file_path)
