import os
import json
import re
from urllib.parse import urlparse
from flask import session
from werkzeug.utils import secure_filename
from jinja2.sandbox import SandboxedEnvironment

def get_workspace_dir(repo_name):
    session_id = secure_filename(session.get('session_id', 'default'))
    if not session_id:
        session_id = 'default'

    # Ensure base workspace root exists with restricted permissions (0700)
    # to prevent other users on the system from accessing cloned repo data.
    base_dir = '/tmp/gh-web-workspaces'
    os.makedirs(base_dir, mode=0o700, exist_ok=True)
    try:
        os.chmod(base_dir, 0o700)
    except OSError:
        pass

    workspace_root = os.path.join(base_dir, session_id)
    # Sanitize repo_name to prevent path traversal via malicious repository names
    safe_repo_name = secure_filename(repo_name)
    if not safe_repo_name:
        raise ValueError("Invalid repository name")
    repo_workspace = os.path.join(workspace_root, safe_repo_name)

    # Ensure individual repo workspaces are also restricted
    os.makedirs(repo_workspace, mode=0o700, exist_ok=True)
    try:
        os.chmod(repo_workspace, 0o700)
    except OSError:
        pass
    return repo_workspace

def mask_token(s):
    if not isinstance(s, str):
        return s

    # Mask specific session token if it exists
    try:
        token = session.get('github_token')
        if token:
            s = s.replace(token, '********')
    except RuntimeError:
        # Outside request context, continue with regex masking
        pass

    # Mask other common GitHub token patterns as defense-in-depth
    # Patterns: ghp_, gho_, ghu_, ghs_, ghr_ followed by 36 chars
    # And fine-grained PATs: github_pat_...
    s = re.sub(r'gh[pousr]_[a-zA-Z0-9]{36}', '********', s, flags=re.IGNORECASE)
    s = re.sub(r'github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}', '********', s, flags=re.IGNORECASE)

    # Mask tokens in git URLs (defense-in-depth for log/error leakage)
    s = re.sub(r'https://(?P<token>[a-zA-Z0-9._~-]+)@github\.com', r'https://********@github.com', s, flags=re.IGNORECASE)
    s = re.sub(r'https://(?P<user>[a-zA-Z0-9._~-]+):(?P<token>[a-zA-Z0-9._~-]+)@github\.com', r'https://\g<user>:********@github.com', s, flags=re.IGNORECASE)

    return s

def get_repo_full_name_from_url(url):
    """Extracts 'owner/repo' from a GitHub URL."""
    if not url:
        return None
    match = re.search(r'github\.com[:/](.+?)(?:\.git)?$', url)
    return match.group(1) if match else None

def validate_github_url(url):
    """
    SSRF Protection: Robustly validates that the URL is an official GitHub repository URL.
    Uses urlparse to prevent hostname-based bypasses (e.g., github.com.evil.com).
    """
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ['http', 'https']:
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        hostname = hostname.lower()
        if hostname != 'github.com' and hostname != 'www.github.com':
            return False
        # Prevent path traversal in the URL itself which might confuse downstream logic
        path_parts = parsed.path.split('/')
        if '..' in path_parts:
            return False
        return True
    except Exception:
        return False

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

def get_templates_root():
    """
    Returns the centralized templates root directory (~/.zekiprod/templates)
    and ensures it exists with restricted permissions (0700).
    """
    app_root = os.path.expanduser('~/.zekiprod')
    templates_root = os.path.join(app_root, 'templates')

    # Create root with restricted permissions
    os.makedirs(app_root, mode=0o700, exist_ok=True)
    try:
        os.chmod(app_root, 0o700)
    except OSError:
        pass

    # Create templates subdir with restricted permissions
    os.makedirs(templates_root, mode=0o700, exist_ok=True)
    try:
        os.chmod(templates_root, 0o700)
    except OSError:
        pass

    return templates_root

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

            # Safety check: Ensure the rendered path stays within the target directory
            # We always check against target_path to prevent traversal via template variables
            if not is_safe_path(target_path, dest_file_path):
                continue # Skip unsafe paths

            if is_safe_path_func and workspace_root:
                if not is_safe_path_func(workspace_root, dest_file_path):
                    continue # Skip unsafe paths

            os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)

            # Determine if we should render content
            should_render = True
            if os.path.islink(source_file_path):
                should_render = False

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
                    # Security: set follow_symlinks=False to avoid following symlinks.
                    shutil.copy2(source_file_path, dest_file_path, follow_symlinks=False)
            except Exception:
                # Fallback to direct copy on error
                import shutil
                # Security: set follow_symlinks=False to avoid following symlinks.
                shutil.copy2(source_file_path, dest_file_path, follow_symlinks=False)


def get_workspace_dir_if_exists(repo_name):
    """Safely checks if a workspace exists for the given repo without creating it."""
    session_id = secure_filename(session.get('session_id', 'default'))
    if not session_id:
        session_id = 'default'
    workspace_root = os.path.join('/tmp/gh-web-workspaces', session_id)
    safe_repo_name = secure_filename(repo_name)
    if not safe_repo_name:
        return None
    repo_workspace = os.path.join(workspace_root, safe_repo_name)
    if os.path.exists(repo_workspace) and os.path.isdir(repo_workspace):
        return repo_workspace
    return None

def calculate_dependency_freshness(workspace_dir):
    """
    Scans requirements.txt and calculates a freshness index (0-100).
    MVP Logic:
    - 100: All dependencies are pinned with '=='
    - 50: Some dependencies are pinned, others are not (e.g., '>=', or unpinned)
    - 0: No dependencies are pinned or no requirements.txt found
    """
    if not workspace_dir or not os.path.exists(workspace_dir):
        return None

    req_path = os.path.join(workspace_dir, 'requirements.txt')
    if not os.path.exists(req_path):
        return None

    try:
        with open(req_path, 'r') as f:
            lines = [l.strip() for l in f.readlines() if l.strip() and not l.startswith('#')]

        if not lines:
            return 100

        pinned = 0
        for line in lines:
            if '==' in line:
                pinned += 1

        score = (pinned / len(lines)) * 100
        return round(score, 2)
    except:
        return 0

def resolve_effective_portfolio(g, org_name=None, team_id=None, repos_arg=None):
    """
    Resolves the list of repository full names for strategic aggregation.
    Priority: 1. repos_arg, 2. org/team context, 3. active workspaces, 4. user context.
    """
    # 1. Explicit repos list
    if repos_arg:
        repo_names = [r.strip() for r in repos_arg.split(',') if r.strip()]
        if repo_names:
            return repo_names[:50]

    # 2. Context-driven (Org/Team)
    if org_name:
        try:
            org = g.get_organization(org_name)
            if team_id:
                team = org.get_team(int(team_id))
                repos = team.get_repos(sort='pushed', direction='desc')
            else:
                repos = org.get_repos(sort='pushed', direction='desc')

            results = []
            for i, repo in enumerate(repos):
                if i >= 20: break
                results.append(repo.full_name)
            if results:
                return results
        except:
            pass

    # 3. Workspace Fallback
    session_id = secure_filename(session.get('session_id', 'default'))
    if not session_id:
        session_id = 'default'
    workspace_root = os.path.join('/tmp/gh-web-workspaces', session_id)
    if os.path.exists(workspace_root):
        try:
            repo_dirs = sorted(os.listdir(workspace_root))
            results = []
            import git
            for rd in repo_dirs:
                if len(results) >= 20: break
                repo_path = os.path.join(workspace_root, rd)
                if os.path.isdir(repo_path) and os.path.exists(os.path.join(repo_path, '.git')):
                    try:
                        r = git.Repo(repo_path)
                        url = r.remotes.origin.url
                        match = re.search(r'github\.com[:/](.+?)(?:\.git)?$', url)
                        full_name = match.group(1) if match else None
                        if full_name:
                            results.append(full_name)
                    except:
                        pass
            if results:
                return results
        except:
            pass

    # 4. User context fallback (Personal recently pushed)
    try:
        user = g.get_user()
        repos = user.get_repos(sort='pushed', direction='desc')
        results = []
        for i, repo in enumerate(repos):
            if i >= 20: break
            results.append(repo.full_name)
        return results
    except:
        pass

    return []
