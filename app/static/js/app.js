document.addEventListener('DOMContentLoaded', () => {
    const escapeHTML = (str) => {
        if (str == null) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    };

    const timeAgo = (date) => {
        if (!date) return 'never';
        const seconds = Math.floor((new Date() - new Date(date)) / 1000);
        let interval = seconds / 31536000;
        if (interval >= 1) return Math.floor(interval) + "y ago";
        interval = seconds / 2592000;
        if (interval >= 1) return Math.floor(interval) + "mo ago";
        interval = seconds / 86400;
        if (interval >= 1) return Math.floor(interval) + "d ago";
        interval = seconds / 3600;
        if (interval >= 1) return Math.floor(interval) + "h ago";
        interval = seconds / 60;
        if (interval >= 1) return Math.floor(interval) + "m ago";
        return Math.floor(Math.max(0, seconds)) + "s ago";
    };

    const showAlert = (message, type = 'success') => {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'danger' ? 'danger' : (type === 'info' ? 'info' : (type === 'warning' ? 'warning' : 'success'))} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');

        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${escapeHTML(message)}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        container.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    };

    const toggleLoading = (button, isLoading) => {
        if (isLoading) {
            button.dataset.originalHtml = button.innerHTML;
            button.disabled = true;
            button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span><span class="visually-hidden">Loading...</span>';
        } else {
            if (button.dataset.originalHtml) {
                button.innerHTML = button.dataset.originalHtml;
            }
            button.disabled = false;
        }
    };

    const handleForm = (formId, endpoint, method = 'POST', isMultipart = false, onSuccess = null) => {
        const form = document.getElementById(formId);
        if (!form) return;
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            // Check if template is selected and needs parameters
            if (formId === 'createRepoForm' || formId === 'applyTemplateForm' || formId === 'dummyApplyTemplateForm') {
                const templateSelect = form.querySelector('select[name="template_name"]') || document.getElementById('workspaceTemplateSelect');
                const templateName = templateSelect ? templateSelect.value : '';
                if (templateName && !form.dataset.paramsConfirmed) {
                    return await showTemplateParams(templateName, form);
                }
            }

            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) toggleLoading(submitBtn, true);
            const formData = isMultipart ? new FormData(form) : new URLSearchParams(new FormData(form));

            // Inject context if confirmed
            if (form.dataset.context) {
                if (isMultipart) {
                    formData.append('context', form.dataset.context);
                } else {
                    formData.set('context', form.dataset.context);
                }
            }

            try {
                const url = typeof endpoint === 'function' ? endpoint() : endpoint;
                const response = await fetch(url, {
                    method: method,
                    body: formData
                });
                const result = await response.json();
                if (response.ok) {
                    showAlert(result.message || 'Operation successful');
                    if (onSuccess) onSuccess(result);
                    // Reset confirmation state
                    delete form.dataset.paramsConfirmed;
                    delete form.dataset.context;
                } else {
                    showAlert(result.error || 'Operation failed', 'danger');
                }
            } catch (error) {
                showAlert(error.message, 'danger');
            } finally {
                if (submitBtn) toggleLoading(submitBtn, false);
            }
        });
    };

    // Expose handleForm for testing or dynamic forms
    window.handleForm = handleForm;
    window.showAlert = showAlert;

    const initDashboard = async () => {
        const profileDiv = document.getElementById('userProfile');
        const loginForm = document.getElementById('loginForm');

        try {
            const response = await fetch('/api/user');
            if (response.ok) {
                const user = await response.json();
                document.getElementById('userAvatar').src = user.avatar_url;
                document.getElementById('userLogin').textContent = user.login;
                profileDiv.classList.remove('d-none');
                profileDiv.classList.add('d-flex');
                if (loginForm) loginForm.classList.add('d-none');

                await refreshDashboardRepos();
                refreshWorkspacePortfolio();
                refreshTaskInbox();
            } else {
                profileDiv.classList.add('d-none');
                profileDiv.classList.remove('d-flex');
                if (loginForm) loginForm.classList.remove('d-none');
            }
        } catch (error) {
            console.error('Failed to fetch user profile:', error);
        }
    };

    let allRepos = [];
    const refreshDashboardRepos = async (search = '') => {
        const repoList = document.getElementById('dashboardRepoList');
        if (!repoList) return;

        try {
            const url = search ? `/api/repos?search=${encodeURIComponent(search)}` : '/api/repos';
            const response = await fetch(url);
            const repos = await response.json();

            if (!response.ok) {
                repoList.innerHTML = `<p class="text-danger p-3">${escapeHTML(repos.error || 'Failed to fetch repositories')}</p>`;
                return;
            }

            allRepos = repos;
            renderRepoList(repos);

            // Update datalist for autosuggest
            const datalist = document.getElementById('userReposList');
            if (datalist) {
                datalist.innerHTML = '';
                repos.forEach(repo => {
                    const opt = document.createElement('option');
                    opt.value = repo.full_name;
                    datalist.appendChild(opt);
                });
            }
        } catch (error) {
            repoList.innerHTML = `<p class="text-danger p-3">Error: ${escapeHTML(error.message)}</p>`;
        }
    };

    const renderRepoList = (repos) => {
        const repoList = document.getElementById('dashboardRepoList');
        if (!repoList) return;

        if (repos.length === 0) {
            repoList.innerHTML = '<p class="text-muted p-3">No repositories found.</p>';
            return;
        }

        repoList.innerHTML = '';
        repos.forEach(repo => {
            const item = document.createElement('div');
            item.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
            const prBadge = repo.open_prs_count > 0 ?
                `<span class="badge bg-warning text-dark ms-2" title="${repo.open_prs_count} open pull requests">${repo.open_prs_count} PRs</span>` : '';
            const issueBadge = repo.open_issues_count > 0 ?
                `<span class="badge bg-secondary ms-2" title="${repo.open_issues_count} open issues">${repo.open_issues_count} Issues</span>` : '';
            const pushedStr = repo.pushed_at ? timeAgo(repo.pushed_at) : 'never';

            const repoAriaLabel = `Open repository ${escapeHTML(repo.full_name)}. ${repo.open_issues_count} issues, ${repo.open_prs_count} pull requests. Last pushed ${pushedStr}.`;

            item.innerHTML = `
                <div>
                    <h6 class="mb-0 text-primary" style="cursor:pointer;" data-repo="${escapeHTML(repo.full_name)}" tabindex="0" role="button" aria-label="${repoAriaLabel}">
                        ${escapeHTML(repo.full_name)}
                        ${issueBadge}
                        ${prBadge}
                    </h6>
                    <small class="text-muted text-truncate d-block" style="max-width: 400px;" title="${escapeHTML(repo.description || 'No description')}">
                        <span class="badge bg-light text-dark border me-1" title="${repo.pushed_at ? new Date(repo.pushed_at).toLocaleString() : 'Never'}">${pushedStr}</span>
                        ${escapeHTML(repo.description || 'No description')}
                    </small>
                </div>
                <div class="d-flex gap-1">
                    <button class="btn btn-sm btn-outline-secondary issues-action" data-repo="${escapeHTML(repo.full_name)}" aria-label="View issues for ${escapeHTML(repo.full_name)}">Issues</button>
                    <button class="btn btn-sm btn-outline-secondary pr-action" data-repo="${escapeHTML(repo.full_name)}" aria-label="View pull requests for ${escapeHTML(repo.full_name)}">PRs</button>
                    <button class="btn btn-sm btn-outline-secondary actions-action" data-repo="${escapeHTML(repo.full_name)}" aria-label="View actions for ${escapeHTML(repo.full_name)}">Actions</button>
                    <button class="btn btn-sm btn-outline-secondary releases-action" data-repo="${escapeHTML(repo.full_name)}" aria-label="View releases for ${escapeHTML(repo.full_name)}">Releases</button>
                    <button class="btn btn-sm btn-outline-info clone-action" data-repo-url="${escapeHTML(repo.html_url)}" aria-label="Clone repository ${escapeHTML(repo.full_name)}">Clone</button>
                </div>
            `;
            repoList.appendChild(item);
        });

        repoList.querySelectorAll('h6[data-repo]').forEach(el => {
            const openRepo = () => {
                const repo = el.getAttribute('data-repo');
                document.getElementById('repoFullName').value = repo;
                document.getElementById('downloadRepoName').value = repo;
                const prTab = document.getElementById('prs-tab');
                bootstrap.Tab.getOrCreateInstance(prTab).show();
                document.getElementById('listPrsBtn').click();
            };
            el.addEventListener('click', openRepo);
            el.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    openRepo();
                }
            });
        });


        repoList.querySelectorAll('.issues-action').forEach(btn => {
            btn.addEventListener('click', () => {
                const repo = btn.getAttribute('data-repo');
                document.querySelectorAll('.repo-full-name-input').forEach(input => input.value = repo);
                const issuesTab = document.getElementById('issues-tab');
                bootstrap.Tab.getOrCreateInstance(issuesTab).show();
                document.getElementById('listIssuesBtn').click();
            });
        });

        repoList.querySelectorAll('.actions-action').forEach(btn => {
            btn.addEventListener('click', () => {
                const repo = btn.getAttribute('data-repo');
                document.querySelectorAll('.repo-full-name-input').forEach(input => input.value = repo);
                const actionsTab = document.getElementById('actions-tab');
                bootstrap.Tab.getOrCreateInstance(actionsTab).show();
                document.getElementById('listActionsBtn').click();
            });
        });

        repoList.querySelectorAll('.releases-action').forEach(btn => {
            btn.addEventListener('click', () => {
                const repo = btn.getAttribute('data-repo');
                document.querySelectorAll('.repo-full-name-input').forEach(input => input.value = repo);
                const releasesTab = document.getElementById('releases-tab');
                bootstrap.Tab.getOrCreateInstance(releasesTab).show();
                document.getElementById('listReleasesBtn').click();
            });
        });

        repoList.querySelectorAll('.pr-action').forEach(btn => {
            btn.addEventListener('click', () => {
                const repo = btn.getAttribute('data-repo');
                document.querySelectorAll('.repo-full-name-input').forEach(input => input.value = repo);
                const prTab = document.getElementById('prs-tab');
                bootstrap.Tab.getOrCreateInstance(prTab).show();
                document.getElementById('listPrsBtn').click();
            });
        });

        repoList.querySelectorAll('.clone-action').forEach(btn => {
            btn.addEventListener('click', () => {
                const url = btn.getAttribute('data-repo-url');
                document.getElementById('repoUrl').value = url;
                const workspaceTab = document.getElementById('workspace-tab');
                bootstrap.Tab.getOrCreateInstance(workspaceTab).show();
            });
        });
    };

    const dashboardRepoSearch = document.getElementById('dashboardRepoSearch');
    if (dashboardRepoSearch) {
        let timeout = null;
        dashboardRepoSearch.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            if (timeout) clearTimeout(timeout);

            // Client-side filtering first
            const filtered = allRepos.filter(r => r.full_name.toLowerCase().includes(query) || (r.description && r.description.toLowerCase().includes(query)));
            renderRepoList(filtered);

            // Debounced server-side search if needed
            timeout = setTimeout(() => {
                if (query && filtered.length < 5) {
                    refreshDashboardRepos(query);
                }
            }, 500);
        });
    }

    const refreshWorkspacePortfolio = async () => {
        const portfolioList = document.getElementById('activeWorkspacesList');
        if (!portfolioList) return;

        try {
            const response = await fetch('/api/workspace/portfolio');
            const data = await response.json();

            if (!response.ok) {
                portfolioList.innerHTML = `<p class="text-danger p-3">${escapeHTML(data.error || 'Failed to fetch portfolio')}</p>`;
                return;
            }

            if (data.length === 0) {
                portfolioList.innerHTML = '<p class="text-muted p-3">No active workspaces found.</p>';
                return;
            }

            portfolioList.innerHTML = '';
            data.forEach(item => {
                const div = document.createElement('div');
                div.className = 'list-group-item';
                const isModified = item.is_dirty || item.untracked;
                const statusText = isModified ? 'Modified' : 'Clean';
                const statusBadge = `<span class="badge ${isModified ? 'bg-warning text-dark' : 'bg-success'} float-end ms-2">${statusText}</span>`;

                const aheadBadge = item.ahead > 0 ? `<span class="badge bg-info text-dark ms-1" title="${item.ahead} commits ahead">↑${item.ahead}</span>` : '';
                const behindBadge = item.behind > 0 ? `<span class="badge bg-danger ms-1" title="${item.behind} commits behind">↓${item.behind}</span>` : '';

                let activeTaskHtml = '';
                if (item.active_issue) {
                    const taskType = item.active_issue.is_pr ? 'PR' : 'Issue';
                    activeTaskHtml = `<div class="small mt-1 text-truncate"><span class="badge bg-dark">${taskType} #${escapeHTML(String(item.active_issue.number))}</span> ${escapeHTML(item.active_issue.title)}</div>`;
                }

                div.innerHTML = `
                    <div class="d-flex justify-content-between align-items-start mb-1">
                        <div class="text-truncate" style="max-width: 60%;">
                            <h6 class="mb-0 text-primary open-workspace" style="cursor:pointer;" data-repo-name="${escapeHTML(item.repo_name)}" tabindex="0" role="button" aria-label="Open workspace ${escapeHTML(item.repo_name)} (${statusText})">
                                ${escapeHTML(item.repo_name)}
                                ${aheadBadge}${behindBadge}
                            </h6>
                            <small class="text-muted font-monospace">${escapeHTML(item.branch)}</small>
                        </div>
                        ${statusBadge}
                    </div>
                    ${activeTaskHtml}
                    <div class="small text-muted text-truncate mb-2" title="${escapeHTML(item.last_commit_subject || '')}">${escapeHTML(item.last_commit_subject || 'No commits')}</div>
                    <div class="d-flex gap-1 justify-content-end">
                        <button class="btn btn-sm btn-outline-primary sync-workspace-btn" data-repo-name="${escapeHTML(item.repo_name)}" title="Sync (Fetch)" aria-label="Sync workspace ${escapeHTML(item.repo_name)}">🔄</button>
                        <button class="btn btn-sm btn-outline-danger revert-workspace-btn" data-repo-name="${escapeHTML(item.repo_name)}" title="Discard Changes" aria-label="Discard changes for workspace ${escapeHTML(item.repo_name)}">🗑️</button>
                    </div>
                `;
                portfolioList.appendChild(div);
            });

            portfolioList.querySelectorAll('.open-workspace').forEach(el => {
                const activateWorkspace = async () => {
                    const repoName = el.getAttribute('data-repo-name');
                    try {
                        await fetch('/api/workspace/activate', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({repo_name: repoName})
                        });
                        const workspaceTab = document.getElementById('workspace-tab');
                        bootstrap.Tab.getOrCreateInstance(workspaceTab).show();
                        refreshExplorer();
                    } catch (e) {}
                };
                el.addEventListener('click', activateWorkspace);
                el.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        activateWorkspace();
                    }
                });
            });

            portfolioList.querySelectorAll('.sync-workspace-btn').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const repoName = btn.getAttribute('data-repo-name');
                    toggleLoading(btn, true);
                    try {
                        // Activate first then sync
                        await fetch('/api/workspace/activate', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({repo_name: repoName})
                        });
                        const response = await fetch('/api/workspace/sync', { method: 'POST' });
                        const result = await response.json();
                        if (response.ok) {
                            showAlert(result.message);
                            refreshWorkspacePortfolio();
                        } else {
                            showAlert(result.error, 'danger');
                        }
                    } catch (error) {
                        showAlert(error.message, 'danger');
                    } finally {
                        toggleLoading(btn, false);
                    }
                });
            });

            portfolioList.querySelectorAll('.revert-workspace-btn').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const repoName = btn.getAttribute('data-repo-name');
                    if (!confirm(`Discard changes for ${repoName}?`)) return;
                    toggleLoading(btn, true);
                    try {
                        // Activate first then revert
                        await fetch('/api/workspace/activate', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({repo_name: repoName})
                        });
                        const response = await fetch('/api/workspace/revert', { method: 'POST' });
                        const result = await response.json();
                        if (response.ok) {
                            showAlert(result.message);
                            refreshWorkspacePortfolio();
                        } else {
                            showAlert(result.error, 'danger');
                        }
                    } catch (error) {
                        showAlert(error.message, 'danger');
                    } finally {
                        toggleLoading(btn, false);
                    }
                });
            });
        } catch (error) {
            portfolioList.innerHTML = `<p class="text-danger p-3">Error: ${escapeHTML(error.message)}</p>`;
        }
    };

    const refreshPortfolioBtn = document.getElementById('refreshPortfolioBtn');
    if (refreshPortfolioBtn) {
        refreshPortfolioBtn.addEventListener('click', () => {
            toggleLoading(refreshPortfolioBtn, true);
            refreshWorkspacePortfolio().finally(() => toggleLoading(refreshPortfolioBtn, false));
        });
    }

    const syncAllWorkspacesBtn = document.getElementById('syncAllWorkspacesBtn');
    if (syncAllWorkspacesBtn) {
        syncAllWorkspacesBtn.addEventListener('click', async () => {
            toggleLoading(syncAllWorkspacesBtn, true);
            try {
                const response = await fetch('/api/workspace/sync-all', { method: 'POST' });
                const result = await response.json();
                if (response.ok || response.status === 207) {
                    showAlert(result.message);
                    refreshWorkspacePortfolio();
                } else {
                    showAlert(result.error, 'danger');
                }
            } catch (error) {
                showAlert(error.message, 'danger');
            } finally {
                toggleLoading(syncAllWorkspacesBtn, false);
            }
        });
    }

    const refreshTaskInbox = async () => {
        const inbox = document.getElementById('taskInboxList');
        if (!inbox) return;

        try {
            const response = await fetch('/api/tasks');
            const tasks = await response.json();

            if (!response.ok) {
                inbox.innerHTML = `<p class="text-danger p-3 mb-0">${escapeHTML(tasks.error || 'Failed to fetch tasks')}</p>`;
                return;
            }

            if (tasks.length === 0) {
                inbox.innerHTML = '<p class="text-muted p-3 mb-0">No active tasks found. You&#39;re all caught up!</p>';
                return;
            }

            inbox.innerHTML = '';
            tasks.forEach(task => {
                const item = document.createElement('div');
                item.className = 'list-group-item d-flex justify-content-between align-items-center py-3';

                const typeIcon = task.type === 'pr' ? '🌿' : '🎫';
                const categoryBadge = task.category === 'review_requested' ?
                    '<span class="badge bg-danger">Action Required</span>' :
                    (task.category === 'assigned' ? '<span class="badge bg-primary">In Progress</span>' : '<span class="badge bg-secondary">My PR</span>');

                let statusBadges = '';
                if (task.ci_status) {
                    const ciClass = task.ci_status === 'success' ? 'bg-success' : (task.ci_status === 'failure' ? 'bg-danger' : 'bg-warning text-dark');
                    statusBadges += `<span class="badge ${ciClass} ms-1">CI: ${task.ci_status.toUpperCase()}</span>`;
                }
                if (task.review_status) {
                    const revClass = task.review_status === 'approved' ? 'bg-success' : (task.review_status === 'changes_requested' ? 'bg-danger' : 'bg-warning text-dark');
                    statusBadges += `<span class="badge ${revClass} ms-1">Review: ${task.review_status.replace('_', ' ').toUpperCase()}</span>`;
                }

                const actionBtn = task.type === 'pr' ?
                    `<button class="btn btn-sm btn-outline-primary review-task-btn" data-repo="${escapeHTML(task.repo)}" data-number="${escapeHTML(String(task.number))}">Review</button>` :
                    `<button class="btn btn-sm btn-outline-success fix-task-btn" data-repo="${escapeHTML(task.repo)}" data-number="${escapeHTML(String(task.number))}">Fix</button>`;

                item.innerHTML = `
                    <div class="d-flex align-items-start gap-3 w-75">
                        <span class="fs-4" aria-hidden="true">${typeIcon}</span>
                        <div class="text-truncate">
                            <div class="d-flex align-items-center gap-2 mb-1">
                                ${categoryBadge}
                                <span class="text-muted small">${escapeHTML(task.repo)}#${escapeHTML(String(task.number))}</span>
                                ${statusBadges}
                            </div>
                            <h6 class="mb-0 text-truncate"><a href="${escapeHTML(task.html_url)}" target="_blank" rel="noopener noreferrer" class="text-decoration-none">${escapeHTML(task.title)}</a></h6>
                            <small class="text-muted" title="${new Date(task.updated_at).toLocaleString()}">Updated ${timeAgo(task.updated_at)}</small>
                        </div>
                    </div>
                    <div class="d-flex gap-2">
                        <button class="btn btn-sm btn-outline-info comments-task-btn" data-repo="${escapeHTML(task.repo)}" data-number="${escapeHTML(String(task.number))}" data-type="${task.type}">Comments</button>
                        ${actionBtn}
                    </div>
                `;
                inbox.appendChild(item);
            });

            inbox.querySelectorAll('.comments-task-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    openConversation(btn.dataset.repo, btn.dataset.number, btn.dataset.type);
                });
            });

            inbox.querySelectorAll('.fix-task-btn').forEach(btn => {
                btn.addEventListener('click', async () => {
                    toggleLoading(btn, true);
                    try {
                        const resp = await fetch('/api/workspace/setup-issue-fix', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                repo_full_name: btn.dataset.repo,
                                issue_number: btn.dataset.number
                            })
                        });
                        const res = await resp.json();
                        if (resp.ok) {
                            showAlert(res.message);
                            bootstrap.Tab.getOrCreateInstance(document.getElementById('workspace-tab')).show();
                            refreshExplorer();
                        } else {
                            showAlert(res.error, 'danger');
                        }
                    } catch (error) {
                        showAlert(error.message, 'danger');
                    } finally {
                        toggleLoading(btn, false);
                    }
                });
            });

            inbox.querySelectorAll('.review-task-btn').forEach(btn => {
                btn.addEventListener('click', async () => {
                    toggleLoading(btn, true);
                    try {
                        const resp = await fetch('/api/workspace/stream-pr', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                repo_full_name: btn.dataset.repo,
                                pr_number: btn.dataset.number
                            })
                        });
                        const res = await resp.json();
                        if (resp.ok) {
                            showAlert(res.message);
                            bootstrap.Tab.getOrCreateInstance(document.getElementById('workspace-tab')).show();
                            refreshExplorer();
                        } else {
                            showAlert(res.error, 'danger');
                        }
                    } catch (error) {
                        showAlert(error.message, 'danger');
                    } finally {
                        toggleLoading(btn, false);
                    }
                });
            });

        } catch (error) {
            inbox.innerHTML = `<p class="text-danger p-3 mb-0">Error: ${escapeHTML(error.message)}</p>`;
        }
    };

    const refreshTasksBtn = document.getElementById('refreshTasksBtn');
    if (refreshTasksBtn) {
        refreshTasksBtn.addEventListener('click', () => {
            toggleLoading(refreshTasksBtn, true);
            refreshTaskInbox().finally(() => toggleLoading(refreshTasksBtn, false));
        });
    }

    initDashboard();

    handleForm('loginForm', '/login', 'POST', false, () => {
        initDashboard();
        refreshTemplates();
    });
    handleForm('createRepoForm', '/api/repos');

    const createIssueForm = document.getElementById('createIssueForm');
    if (createIssueForm) {
        createIssueForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = createIssueForm.querySelector('button[type="submit"]');
            const repoFull = document.getElementById('issuesRepoFullName').value;
            if (!repoFull) return showAlert('Repo Full Name is required', 'danger');

            toggleLoading(submitBtn, true);
            const formData = new URLSearchParams(new FormData(createIssueForm));
            try {
                const response = await fetch(`/api/repos/${repoFull}/issues`, {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                if (response.ok) {
                    showAlert(result.message);
                    document.getElementById('listIssuesBtn').click();
                } else {
                    showAlert(result.error, 'danger');
                }
            } catch (error) {
                showAlert(error.message, 'danger');
            } finally {
                toggleLoading(submitBtn, false);
            }
        });
    }

    const openConversation = async (repoFull, number, type = 'issue') => {
        const thread = document.getElementById('conversationThread');
        const modalLabel = document.getElementById('conversationModalLabel');
        const reviewControls = document.getElementById('reviewControls');
        const submitBtn = document.getElementById('submitCommentBtn');
        const commentBody = document.getElementById('commentBody');

        modalLabel.textContent = `${type === 'pr' ? 'Pull Request' : 'Issue'} #${number} Conversation`;
        thread.innerHTML = '<div class="text-center p-4"><span class="spinner-border" role="status"></span></div>';
        reviewControls.style.display = type === 'pr' ? 'block' : 'none';
        commentBody.value = '';

        const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('conversationModal'));
        modal.show();

        const loadComments = async () => {
            try {
                const response = await fetch(`/api/repos/${repoFull}/issues/${number}/comments`);
                const comments = await response.json();
                if (response.ok) {
                    thread.innerHTML = '';
                    if (comments.length === 0) {
                        thread.innerHTML = '<p class="text-muted text-center p-3">No comments yet.</p>';
                    }
                    comments.forEach(c => {
                        const div = document.createElement('div');
                        div.className = 'card mb-2 shadow-sm';
                        const isReview = c.type === 'review';
                        const badgeClass = c.state === 'APPROVED' ? 'bg-success' : (c.state === 'CHANGES_REQUESTED' ? 'bg-danger' : 'bg-secondary');
                        const reviewBadge = isReview ? `<span class="badge ${badgeClass} ms-2 small">${escapeHTML(c.state)}</span>` : '';

                        div.innerHTML = `
                            <div class="card-header d-flex align-items-center py-1 ${isReview ? 'bg-light border-info' : 'bg-light'}">
                                <img src="${escapeHTML(c.avatar_url)}" class="rounded-circle me-2" width="20" height="20" alt="${escapeHTML(c.user)}">
                                <strong class="small">${escapeHTML(c.user)}</strong>
                                ${reviewBadge}
                                <small class="text-muted ms-auto">${escapeHTML(new Date(c.created_at).toLocaleString())}</small>
                            </div>
                            <div class="card-body py-2">
                                <p class="card-text small mb-0" style="white-space: pre-wrap;">${escapeHTML(c.body)}</p>
                            </div>
                        `;
                        thread.appendChild(div);
                    });
                    thread.scrollTop = thread.scrollHeight;
                } else {
                    thread.innerHTML = `<p class="text-danger p-3">${escapeHTML(comments.error)}</p>`;
                }
            } catch (error) {
                thread.innerHTML = `<p class="text-danger p-3">${escapeHTML(error.message)}</p>`;
            }
        };

        await loadComments();

        // Clear and re-attach listener
        const newSubmitBtn = submitBtn.cloneNode(true);
        submitBtn.parentNode.replaceChild(newSubmitBtn, submitBtn);

        newSubmitBtn.addEventListener('click', async () => {
            const body = commentBody.value.trim();
            if (!body) return;

            toggleLoading(newSubmitBtn, true);
            try {
                let response;
                if (type === 'pr') {
                    const event = document.querySelector('input[name="reviewEvent"]:checked').value;
                    response = await fetch(`/api/repos/${repoFull}/prs/${number}/reviews`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ body, event })
                    });
                } else {
                    response = await fetch(`/api/repos/${repoFull}/issues/${number}/comments`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ body })
                    });
                }

                const result = await response.json();
                if (response.ok) {
                    showAlert(result.message);
                    commentBody.value = '';
                    await loadComments();
                } else {
                    showAlert(result.error, 'danger');
                }
            } catch (error) {
                showAlert(error.message, 'danger');
            } finally {
                toggleLoading(newSubmitBtn, false);
            }
        });
    };

    const listIssuesForm = document.getElementById('listIssuesForm');
    if (listIssuesForm) {
        listIssuesForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const listIssuesBtn = document.getElementById('listIssuesBtn');
            const repoFull = document.getElementById('issuesRepoFullName').value;
            const state = document.querySelector('input[name="state"]:checked').value;
            if (!repoFull) return showAlert('Repo Full Name is required', 'danger');

            toggleLoading(listIssuesBtn, true);
            try {
                const response = await fetch(`/api/repos/${repoFull}/issues?state=${state}`);
                const issues = await response.json();

                if (!response.ok) {
                    showAlert(issues.error || 'Failed to fetch Issues', 'danger');
                    return;
                }

                const tbody = document.querySelector('#issuesTable tbody');
                tbody.innerHTML = '';
                if (issues.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted">No ${state} issues found.</td></tr>`;
                }
                issues.forEach(issue => {
                    const tr = document.createElement('tr');
                    const labelBadges = (issue.labels || []).map(l =>
                        `<span class="badge rounded-pill me-1" style="background-color: #${l.color}; color: ${parseInt(l.color, 16) > 0xffffff / 2 ? 'black' : 'white'}">${escapeHTML(l.name)}</span>`
                    ).join('');

                    const triageBtn = issue.state === 'open' ?
                        `<button class="btn btn-sm btn-outline-danger close-issue-btn" data-number="${escapeHTML(String(issue.number))}" aria-label="Close issue #${escapeHTML(String(issue.number))}">Close</button>` :
                        `<button class="btn btn-sm btn-outline-warning reopen-issue-btn" data-number="${escapeHTML(String(issue.number))}" aria-label="Reopen issue #${escapeHTML(String(issue.number))}">Reopen</button>`;

                    tr.innerHTML = `
                        <td>${escapeHTML(String(issue.number))}</td>
                        <td>
                            <div><a href="${escapeHTML(issue.html_url)}" target="_blank" rel="noopener noreferrer" class="fw-bold">${escapeHTML(issue.title)}</a></div>
                            <div class="mt-1">${labelBadges}</div>
                        </td>
                        <td><small class="text-muted" title="${escapeHTML(new Date(issue.created_at).toLocaleString())}">${timeAgo(issue.created_at)}</small></td>
                        <td>
                            <div class="d-flex gap-1">
                                <button class="btn btn-sm btn-outline-info comments-issue-btn" data-number="${escapeHTML(String(issue.number))}" aria-label="View comments for issue #${escapeHTML(String(issue.number))}">Comments</button>
                                ${issue.state === 'open' ? `<button class="btn btn-sm btn-outline-primary fix-issue-btn" data-number="${escapeHTML(String(issue.number))}" aria-label="Fix issue #${escapeHTML(String(issue.number))}">Fix</button>` : ''}
                                ${triageBtn}
                            </div>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });

                document.querySelectorAll('.comments-issue-btn').forEach(btn => {
                    btn.addEventListener('click', () => {
                        openConversation(repoFull, btn.getAttribute('data-number'), 'issue');
                    });
                });

                document.querySelectorAll('.fix-issue-btn').forEach(btn => {
                    btn.addEventListener('click', async () => {
                        const num = btn.getAttribute('data-number');
                        toggleLoading(btn, true);
                        try {
                            const resp = await fetch('/api/workspace/setup-issue-fix', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    repo_full_name: repoFull,
                                    issue_number: num
                                })
                            });
                            const res = await resp.json();
                            if (resp.ok) {
                                showAlert(res.message);
                                // Switch to Workspace tab
                                const workspaceTab = document.getElementById('workspace-tab');
                                bootstrap.Tab.getOrCreateInstance(workspaceTab).show();
                                refreshExplorer();
                            } else {
                                showAlert(res.error, 'danger');
                            }
                        } catch (error) {
                            showAlert(error.message, 'danger');
                        } finally {
                            toggleLoading(btn, false);
                        }
                    });
                });

                document.querySelectorAll('.reopen-issue-btn').forEach(btn => {
                    btn.addEventListener('click', async () => {
                        const num = btn.getAttribute('data-number');
                        toggleLoading(btn, true);
                        try {
                            const resp = await fetch(`/api/repos/${repoFull}/issues/${num}/reopen`, {
                                method: 'POST'
                            });
                            const res = await resp.json();
                            if (resp.ok) {
                                showAlert(res.message);
                                listIssuesBtn.click();
                            } else {
                                showAlert(res.error, 'danger');
                            }
                        } catch (error) {
                            showAlert(error.message, 'danger');
                        } finally {
                            toggleLoading(btn, false);
                        }
                    });
                });

                document.querySelectorAll('.close-issue-btn').forEach(btn => {
                    btn.addEventListener('click', async () => {
                        const num = btn.getAttribute('data-number');
                        if (!confirm(`Close issue #${num}?`)) return;
                        toggleLoading(btn, true);
                        try {
                            const resp = await fetch(`/api/repos/${repoFull}/issues/${num}/close`, {
                                method: 'POST'
                            });
                            const res = await resp.json();
                            if (resp.ok) {
                                showAlert(res.message);
                                listIssuesBtn.click();
                            } else {
                                showAlert(res.error, 'danger');
                            }
                        } catch (error) {
                            showAlert(error.message, 'danger');
                        } finally {
                            toggleLoading(btn, false);
                        }
                    });
                });
            } catch (error) {
                showAlert(error.message, 'danger');
            } finally {
                toggleLoading(listIssuesBtn, false);
            }
        });
    }
    handleForm('cloneForm', '/api/workspace/clone');
    handleForm('downloadForm', '/api/workspace/download');
    handleForm('uploadFileForm', '/api/workspace/modify/upload', 'POST', true);
    handleForm('uploadArchiveForm', '/api/workspace/modify/archive', 'POST', true);
    handleForm('applyPatchForm', '/api/workspace/modify/patch', 'POST', true);
    const refreshTemplates = async () => {
        try {
            const response = await fetch('/api/workspace/templates');
            const templates = await response.json();

            // Populate all template selects
            const selects = ['templateSelect', 'workspaceTemplateSelect'];
            selects.forEach(id => {
                const select = document.getElementById(id);
                if (select) {
                    const firstOption = select.options[0] ? select.options[0].textContent : (id === 'templateSelect' ? 'None (Empty Repository)' : 'Apply Template...');
                    select.innerHTML = `<option value="">${firstOption}</option>`;
                    templates.forEach(t => {
                        const opt = document.createElement('option');
                        opt.value = t;
                        opt.textContent = t;
                        select.appendChild(opt);
                    });
                }
            });

            // Populate template library list
            const libraryList = document.getElementById('templateLibraryList');
            if (libraryList) {
                libraryList.innerHTML = '';
                if (templates.length === 0) {
                    libraryList.innerHTML = '<p class="text-muted">No templates found.</p>';
                }
                templates.forEach(t => {
                    const item = document.createElement('div');
                    item.className = 'list-group-item d-flex justify-content-between align-items-center';
                    item.innerHTML = `
                        <span>${t}</span>
                        <div class="d-flex gap-1">
                            <button class="btn btn-sm btn-outline-primary publish-template-btn" data-template="${t}" aria-label="Publish template ${escapeHTML(t)} to GitHub" title="Publish to GitHub">Publish</button>
                            <button class="btn btn-sm btn-outline-danger delete-template-btn" data-template="${t}" aria-label="Delete template ${escapeHTML(t)}" title="Delete template ${escapeHTML(t)}">Delete</button>
                        </div>
                    `;
                    libraryList.appendChild(item);
                });

                libraryList.querySelectorAll('.publish-template-btn').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const t = btn.getAttribute('data-template');
                        document.getElementById('publishTemplateOriginalName').value = t;
                        document.getElementById('publishRepoName').value = t;
                        document.getElementById('publishRepoDescription').value = `Template published from GH-Web: ${t}`;
                        const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('publishTemplateModal'));
                        modal.show();
                    });
                });

                libraryList.querySelectorAll('.delete-template-btn').forEach(btn => {
                    btn.addEventListener('click', async () => {
                        const t = btn.getAttribute('data-template');
                        if (!confirm(`Delete template '${t}'?`)) return;
                        try {
                            const response = await fetch(`/api/workspace/templates/${encodeURIComponent(t)}`, {
                                method: 'DELETE'
                            });
                            const result = await response.json();
                            if (response.ok) {
                                showAlert(result.message);
                                refreshTemplates();
                            } else {
                                showAlert(result.error, 'danger');
                            }
                        } catch (error) {
                            showAlert(error.message, 'danger');
                        }
                    });
                });
            }
        } catch (error) {
            console.error('Failed to fetch templates:', error);
        }
    };

    refreshTemplates();
    handleForm('saveTemplateForm', '/api/workspace/save-template', 'POST', false, () => {
        refreshTemplates();
        refreshExplorer();
    });
    handleForm('importTemplateForm', '/api/workspace/import-template', 'POST', false, refreshTemplates);

    const showTemplateParams = async (templateName, sourceForm) => {
        try {
            const resp = await fetch(`/api/workspace/templates/${encodeURIComponent(templateName)}/manifest`);
            const manifest = await resp.json();

            if (!manifest.variables || manifest.variables.length === 0) {
                sourceForm.dataset.paramsConfirmed = 'true';
                sourceForm.dispatchEvent(new Event('submit'));
                return;
            }

            const container = document.getElementById('dynamicParamsContainer');
            container.innerHTML = '';
            manifest.variables.forEach(v => {
                const div = document.createElement('div');
                div.className = 'mb-3';
                const inputId = `param-${v.name}`;
                div.innerHTML = `
                    <label class="form-label" for="${escapeHTML(inputId)}">${escapeHTML(v.label || v.name)}</label>
                    <input type="${escapeHTML(v.type || 'text')}" class="form-control" id="${escapeHTML(inputId)}" name="${escapeHTML(v.name)}" value="${escapeHTML(v.default || '')}" required>
                `;
                container.appendChild(div);
            });

            const modal = new bootstrap.Modal(document.getElementById('templateParamsModal'));
            modal.show();

            const confirmBtn = document.getElementById('confirmTemplateBtn');
            // Clone button to clear old listeners
            const newConfirmBtn = confirmBtn.cloneNode(true);
            confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

            newConfirmBtn.addEventListener('click', () => {
                const paramsForm = document.getElementById('templateParamsForm');
                const context = {};
                new FormData(paramsForm).forEach((value, key) => {
                    context[key] = value;
                });
                sourceForm.dataset.context = JSON.stringify(context);
                sourceForm.dataset.paramsConfirmed = 'true';
                const modalInstance = bootstrap.Modal.getInstance(document.getElementById('templateParamsModal'));
                if (modalInstance) modalInstance.hide();
                sourceForm.dispatchEvent(new Event('submit'));
            });

        } catch (err) {
            showAlert('Failed to fetch template manifest: ' + err.message, 'danger');
        }
    };

    const applyTemplateBtn = document.getElementById('applyTemplateBtn');
    if (applyTemplateBtn) {
        applyTemplateBtn.addEventListener('click', async () => {
            const templateName = document.getElementById('workspaceTemplateSelect').value;
            if (!templateName) return showAlert('Please select a template', 'danger');

            // We'll simulate a form submission to reuse handleForm logic if possible,
            // or just trigger showTemplateParams directly.
            // Let's create a dummy form to handle this.
            let dummyForm = document.getElementById('dummyApplyTemplateForm');
            if (!dummyForm) {
                dummyForm = document.createElement('form');
                dummyForm.id = 'dummyApplyTemplateForm';
                dummyForm.style.display = 'none';
                dummyForm.innerHTML = '<input type="hidden" name="template_name">';
                document.body.appendChild(dummyForm);
                handleForm('dummyApplyTemplateForm', '/api/workspace/apply-template', 'POST', false, refreshExplorer);
            }
            dummyForm.querySelector('input[name="template_name"]').value = templateName;
            dummyForm.dispatchEvent(new Event('submit'));
        });
    }

    const updateCommitCounter = () => {
        const input = document.getElementById('commitMessage');
        const counter = document.getElementById('commitCounter');
        if (!input || !counter) return;

        const length = input.value.length;
        counter.textContent = `${length}/50`;
        if (length > 50) {
            counter.classList.remove('text-muted');
            counter.classList.add('text-danger');
        } else {
            counter.classList.remove('text-danger');
            counter.classList.add('text-muted');
        }
    };

    const refreshStatus = async () => {
        const branchBadge = document.getElementById('branchBadge');
        const issueBadge = document.getElementById('issueBadge');
        const statusBadge = document.getElementById('statusBadge');
        const ciStatusBadge = document.getElementById('ciStatusBadge');
        const collabBadge = document.getElementById('collabBadge');
        if (!branchBadge || !statusBadge) return;

        try {
            const response = await fetch('/api/workspace/status');
            const data = await response.json();
            if (response.ok && data.is_git) {
                branchBadge.textContent = data.branch;
                branchBadge.style.display = 'inline-block';

                if (data.active_issue) {
                    const issueText = (data.is_pr ? 'PR #' : 'Issue #') + data.active_issue + (data.issue_title ? `: ${data.issue_title}` : '');
                    issueBadge.textContent = issueText;
                    issueBadge.style.display = 'inline-block';
                    const commitInput = document.getElementById('commitMessage');
                    if (commitInput && !commitInput.value) {
                        commitInput.value = `Closes #${data.active_issue}`;
                        updateCommitCounter();
                    }

                    const conversationBtn = document.getElementById('workspaceConversationBtn');
                    if (conversationBtn) {
                        conversationBtn.style.display = 'inline-block';
                        // Refresh listener
                        const newBtn = conversationBtn.cloneNode(true);
                        conversationBtn.parentNode.replaceChild(newBtn, conversationBtn);
                        newBtn.addEventListener('click', () => {
                            openConversation(data.repo_full_name, data.active_issue, data.is_pr ? 'pr' : 'issue');
                        });
                    }
                } else {
                    issueBadge.style.display = 'none';
                    const conversationBtn = document.getElementById('workspaceConversationBtn');
                    if (conversationBtn) conversationBtn.style.display = 'none';
                }
                if (data.is_dirty || data.untracked) {
                    statusBadge.textContent = 'Modified';
                    statusBadge.className = 'badge bg-warning text-dark';
                    statusBadge.style.cursor = 'pointer';
                    statusBadge.setAttribute('role', 'button');
                    statusBadge.setAttribute('tabindex', '0');
                    statusBadge.setAttribute('aria-label', 'Modified. Click to view diff.');

                    if (!statusBadge.dataset.listenerAttached) {
                        const openDiff = () => {
                            const viewDiffBtn = document.getElementById('viewDiffBtn');
                            if (viewDiffBtn) viewDiffBtn.click();
                        };
                        statusBadge.addEventListener('click', openDiff);
                        statusBadge.addEventListener('keydown', (e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                                e.preventDefault();
                                openDiff();
                            }
                        });
                        statusBadge.dataset.listenerAttached = 'true';
                    }
                } else {
                    statusBadge.textContent = 'Clean';
                    statusBadge.className = 'badge bg-success';
                    statusBadge.style.cursor = 'default';
                    statusBadge.removeAttribute('role');
                    statusBadge.removeAttribute('tabindex');
                    statusBadge.removeAttribute('aria-label');
                }
                statusBadge.style.display = 'inline-block';

                if (ciStatusBadge) {
                    if (data.ci_status) {
                        ciStatusBadge.textContent = `CI: ${data.ci_status.toUpperCase()}`;
                        ciStatusBadge.className = `badge bg-${data.ci_status === 'success' ? 'success' : (data.ci_status === 'failure' ? 'danger' : 'secondary')}`;
                        ciStatusBadge.style.display = 'inline-block';
                    } else {
                        ciStatusBadge.style.display = 'none';
                    }
                }

                if (collabBadge) {
                    if (data.can_push) {
                        collabBadge.textContent = 'Collaborative Mode';
                        collabBadge.className = 'badge bg-info text-dark';
                        collabBadge.style.display = 'inline-block';
                        collabBadge.title = 'You have permission to push changes to the source branch.';
                    } else {
                        collabBadge.textContent = 'Read-Only Mode';
                        collabBadge.className = 'badge bg-secondary';
                        collabBadge.style.display = 'inline-block';
                        collabBadge.title = 'You do not have permission to push to the source branch. Changes will be local-only.';
                    }
                }
            } else {
                branchBadge.style.display = 'none';
                statusBadge.style.display = 'none';
            }
        } catch (error) {
            console.error('Failed to fetch workspace status:', error);
        }
    };

    const workspaceSearchForm = document.getElementById('workspaceSearchForm');
    if (workspaceSearchForm) {
        workspaceSearchForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const query = workspaceSearchForm.querySelector('input[name="q"]').value;
            const searchBtn = document.getElementById('workspaceSearchBtn');

            toggleLoading(searchBtn, true);
            try {
                const response = await fetch(`/api/workspace/search?q=${encodeURIComponent(query)}`);
                const results = await response.json();

                if (!response.ok) {
                    showAlert(results.error || 'Search failed', 'danger');
                    return;
                }

                const resultsList = document.getElementById('searchResultsList');
                resultsList.innerHTML = '';

                if (results.length === 0) {
                    resultsList.innerHTML = '<p class="text-muted p-3">No matches found.</p>';
                } else {
                    results.forEach(match => {
                        const item = document.createElement('button');
                        item.type = 'button';
                        item.className = 'list-group-item list-group-item-action';
                        item.innerHTML = `
                            <div class="d-flex w-100 justify-content-between">
                                <h6 class="mb-1 text-primary">${escapeHTML(match.path)}</h6>
                                <small class="text-muted">Line ${escapeHTML(match.line)}</small>
                            </div>
                            <pre class="mb-1 small bg-light p-2 rounded text-truncate"><code>${escapeHTML(match.content)}</code></pre>
                        `;
                        item.addEventListener('click', async () => {
                            try {
                                const resp = await fetch(`/api/workspace/files/content?path=${encodeURIComponent(match.path)}`);
                                const contentData = await resp.json();
                                if (resp.ok) {
                                    document.getElementById('fileModalLabel').textContent = `Editing: ${match.path}`;
                                    document.getElementById('fileModalLabel').dataset.path = match.path;
                                    document.getElementById('fileContentEditor').value = contentData.content;
                                    bootstrap.Modal.getOrCreateInstance(document.getElementById('searchModal')).hide();
                                    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('fileModal'));
                                    modal.show();
                                } else {
                                    showAlert(contentData.error, 'danger');
                                }
                            } catch (err) {
                                showAlert(err.message, 'danger');
                            }
                        });
                        resultsList.appendChild(item);
                    });
                }

                const searchModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('searchModal'));
                searchModal.show();
            } catch (error) {
                showAlert(error.message, 'danger');
            } finally {
                toggleLoading(searchBtn, false);
            }
        });
    }

    const refreshExplorer = async () => {
        const explorer = document.getElementById('workspaceExplorer');
        if (!explorer) return;

        refreshStatus();
        try {
            const response = await fetch('/api/workspace/files');
            const data = await response.json();

            if (!response.ok) {
                explorer.innerHTML = `<p class="text-muted">${data.error || 'No active repository.'}</p>`;
                return;
            }

            const renderTree = (nodes) => {
                if (!nodes || nodes.length === 0) return '<ul class="list-unstyled ms-3"><li>(empty)</li></ul>';
                let html = '<ul class="list-unstyled ms-3">';
                nodes.forEach(node => {
                    const icon = node.type === 'directory' ? '📁' : '📄';
                    const isFile = node.type === 'file';
                    html += `<li class="mb-1">
                        <span class="me-2" aria-hidden="true">${icon}</span>
                        <span class="${isFile ? 'text-primary' : 'fw-bold'}"
                              style="${isFile ? 'cursor:pointer;' : ''}"
                              data-path="${escapeHTML(node.path)}"
                              data-type="${escapeHTML(node.type)}"
                              ${isFile ? `tabindex="0" role="button" aria-label="View file ${escapeHTML(node.name)}"` : ''}>
                            ${escapeHTML(node.name)}
                        </span>
                        <button class="btn btn-sm text-danger delete-file-btn ms-2"
                                data-path="${escapeHTML(node.path)}"
                                style="padding: 0 5px;"
                                aria-label="Delete ${escapeHTML(node.name)}"
                                title="Delete ${escapeHTML(node.name)}">&times;</button>
                        ${node.children ? renderTree(node.children) : ''}
                    </li>`;
                });
                html += '</ul>';
                return html;
            };

            explorer.innerHTML = renderTree(data);

            // Add click and keyboard handlers for files
            explorer.querySelectorAll('span[data-type="file"]').forEach(el => {
                const openFile = async () => {
                    const path = el.getAttribute('data-path');
                    try {
                        const resp = await fetch(`/api/workspace/files/content?path=${encodeURIComponent(path)}`);
                        const contentData = await resp.json();
                        if (resp.ok) {
                            document.getElementById('fileModalLabel').textContent = `Editing: ${path}`;
                            document.getElementById('fileModalLabel').dataset.path = path;
                            document.getElementById('fileContentEditor').value = contentData.content;
                            const modal = new bootstrap.Modal(document.getElementById('fileModal'));
                            modal.show();
                        } else {
                            showAlert(contentData.error, 'danger');
                        }
                    } catch (err) {
                        showAlert(err.message, 'danger');
                    }
                };
                el.addEventListener('click', openFile);
                el.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        openFile();
                    }
                });
            });

            // Add click handlers for deletion
            explorer.querySelectorAll('.delete-file-btn').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const path = btn.getAttribute('data-path');
                    if (!confirm(`Are you sure you want to delete ${path}?`)) return;

                    try {
                        const resp = await fetch('/api/workspace/files', {
                            method: 'DELETE',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ path: path })
                        });
                        const delResult = await resp.json();
                        if (resp.ok) {
                            showAlert(delResult.message);
                            refreshExplorer();
                        } else {
                            showAlert(delResult.error, 'danger');
                        }
                    } catch (err) {
                        showAlert(err.message, 'danger');
                    }
                });
            });

        } catch (error) {
            console.error('Failed to fetch workspace files:', error);
            explorer.innerHTML = '<p class="text-danger">Failed to load workspace explorer.</p>';
        }
    };

    const refreshExplorerBtn = document.getElementById('refreshExplorerBtn');
    if (refreshExplorerBtn) {
        refreshExplorerBtn.addEventListener('click', async () => {
            toggleLoading(refreshExplorerBtn, true);
            await refreshExplorer();
            toggleLoading(refreshExplorerBtn, false);
        });
    }

    const saveFileBtn = document.getElementById('saveFileBtn');
    const fileContentEditor = document.getElementById('fileContentEditor');
    if (fileContentEditor && saveFileBtn) {
        fileContentEditor.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                saveFileBtn.click();
            }
        });
    }

    if (saveFileBtn) {
        saveFileBtn.addEventListener('click', async () => {
            const path = document.getElementById('fileModalLabel').dataset.path;
            const content = document.getElementById('fileContentEditor').value;

            toggleLoading(saveFileBtn, true);
            try {
                const response = await fetch('/api/workspace/files/content', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ path: path, content: content })
                });
                const result = await response.json();
                if (response.ok) {
                    showAlert(result.message);
                    bootstrap.Modal.getInstance(document.getElementById('fileModal')).hide();
                } else {
                    showAlert(result.error, 'danger');
                }
            } catch (error) {
                showAlert(error.message, 'danger');
            } finally {
                toggleLoading(saveFileBtn, false);
            }
        });
    }

    // Auto-refresh explorer when clone/download/upload/patch/commit happens
    handleForm('cloneForm', '/api/workspace/clone', 'POST', false, refreshExplorer);
    handleForm('downloadForm', '/api/workspace/download', 'POST', false, refreshExplorer);
    handleForm('uploadFileForm', '/api/workspace/modify/upload', 'POST', true, refreshExplorer);
    handleForm('uploadArchiveForm', '/api/workspace/modify/archive', 'POST', true, refreshExplorer);
    handleForm('applyPatchForm', '/api/workspace/modify/patch', 'POST', true, refreshExplorer);
    handleForm('commitForm', '/api/workspace/commit', 'POST', false, (res) => {
        refreshExplorer();
        const commitInput = document.getElementById('commitMessage');
        if (commitInput) {
            commitInput.value = '';
            updateCommitCounter();
        }
    });

    const commitInput = document.getElementById('commitMessage');
    if (commitInput) {
        commitInput.addEventListener('input', updateCommitCounter);
    }
    handleForm('branchForm', '/api/workspace/branch', 'POST', false, refreshExplorer);

    const pushBtn = document.getElementById('pushBtn');
    if (pushBtn) {
        pushBtn.addEventListener('click', async () => {
            toggleLoading(pushBtn, true);
            try {
                const response = await fetch('/api/workspace/push', { method: 'POST' });
                const result = await response.json();
                if (response.ok) showAlert(result.message);
                else showAlert(result.error, 'danger');
            } catch (error) {
                showAlert(error.message, 'danger');
            } finally {
                toggleLoading(pushBtn, false);
            }
        });
    }

    const copyDiffBtn = document.getElementById('copyDiffBtn');
    if (copyDiffBtn) {
        copyDiffBtn.addEventListener('click', () => {
            const diffContent = document.getElementById('diffContent');
            if (diffContent) {
                const text = diffContent.textContent;
                navigator.clipboard.writeText(text).then(() => {
                    const originalText = copyDiffBtn.textContent;
                    copyDiffBtn.textContent = 'Copied!';
                    setTimeout(() => {
                        copyDiffBtn.textContent = originalText;
                    }, 2000);
                }).catch(err => {
                    console.error('Failed to copy diff: ', err);
                    showAlert('Failed to copy diff to clipboard', 'danger');
                });
            }
        });
    }

    const viewDiffBtn = document.getElementById('viewDiffBtn');
    if (viewDiffBtn) {
        viewDiffBtn.addEventListener('click', async () => {
            toggleLoading(viewDiffBtn, true);
            try {
                const response = await fetch('/api/workspace/diff');
                const result = await response.json();
                if (response.ok) {
                    const diffContent = document.getElementById('diffContent');
                    diffContent.textContent = result.diff || 'No uncommitted changes.';
                    const modal = new bootstrap.Modal(document.getElementById('diffModal'));
                    modal.show();
                } else {
                    showAlert(result.error, 'danger');
                }
            } catch (error) {
                showAlert(error.message, 'danger');
            } finally {
                toggleLoading(viewDiffBtn, false);
            }
        });
    }

    const viewHistoryBtn = document.getElementById('viewHistoryBtn');
    if (viewHistoryBtn) {
        viewHistoryBtn.addEventListener('click', async () => {
            toggleLoading(viewHistoryBtn, true);
            try {
                const response = await fetch('/api/workspace/history');
                const result = await response.json();
                if (response.ok) {
                    const historyList = document.getElementById('historyList');
                    historyList.innerHTML = '';
                    if (result.length === 0) {
                        historyList.innerHTML = '<p class="text-muted p-3">No commit history found.</p>';
                    } else {
                        result.forEach(commit => {
                            const item = document.createElement('div');
                            item.className = 'list-group-item';
                            item.innerHTML = `
                                <div class="d-flex w-100 justify-content-between">
                                    <h6 class="mb-1 text-truncate">${escapeHTML(commit.message)}</h6>
                                    <small class="text-muted font-monospace">${escapeHTML(commit.hash.substring(0, 7))}</small>
                                </div>
                                <p class="mb-1 small">By <strong>${escapeHTML(commit.author)}</strong></p>
                                <small class="text-muted">${escapeHTML(new Date(commit.date).toLocaleString())}</small>
                            `;
                            historyList.appendChild(item);
                        });
                    }
                    const modal = new bootstrap.Modal(document.getElementById('historyModal'));
                    modal.show();
                } else {
                    showAlert(result.error, 'danger');
                }
            } catch (error) {
                showAlert(error.message, 'danger');
            } finally {
                toggleLoading(viewHistoryBtn, false);
            }
        });
    }

    const revertChangesBtn = document.getElementById('revertChangesBtn');
    if (revertChangesBtn) {
        revertChangesBtn.addEventListener('click', async () => {
            if (!confirm('Are you sure you want to discard all uncommitted changes? This action cannot be undone.')) return;
            toggleLoading(revertChangesBtn, true);
            try {
                const response = await fetch('/api/workspace/revert', { method: 'POST' });
                const result = await response.json();
                if (response.ok) {
                    showAlert(result.message);
                    refreshExplorer();
                } else {
                    showAlert(result.error, 'danger');
                }
            } catch (error) {
                showAlert(error.message, 'danger');
            } finally {
                toggleLoading(revertChangesBtn, false);
            }
        });
    }

    const createPrForm = document.getElementById('createPrForm');
    if (createPrForm) {
        createPrForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = createPrForm.querySelector('button[type="submit"]');
            const repoFull = document.getElementById('repoFullName').value;
            if (!repoFull) return showAlert('Repo Full Name is required', 'danger');

            toggleLoading(submitBtn, true);
            const formData = new URLSearchParams(new FormData(createPrForm));
            try {
                const response = await fetch(`/api/repos/${repoFull}/prs`, {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                if (response.ok) showAlert(result.message);
                else showAlert(result.error, 'danger');
            } catch (error) {
                showAlert(error.message, 'danger');
            } finally {
                toggleLoading(submitBtn, false);
            }
        });
    }

    const prTabBtn = document.getElementById('prs-tab');
    if (prTabBtn) {
        prTabBtn.addEventListener('shown.bs.tab', async () => {
            try {
                const response = await fetch('/api/workspace/status');
                const data = await response.json();
                if (response.ok && data.active_issue) {
                    const titleInput = document.getElementById('prTitle');
                    const headInput = document.getElementById('prHead');
                    const baseInput = document.getElementById('prBase');
                    const bodyInput = document.getElementById('prBody');

                    if (titleInput && !titleInput.value && data.issue_title) {
                        titleInput.value = `Fix: ${data.issue_title}`;
                    }
                    if (headInput && !headInput.value) {
                        headInput.value = data.branch;
                    }
                    if (baseInput && !baseInput.value && data.default_branch) {
                        baseInput.value = data.default_branch;
                    }
                    if (bodyInput && !bodyInput.value) {
                        bodyInput.value = `Closes #${data.active_issue}`;
                    }
                }
            } catch (error) {
                console.error('Failed to pre-fill PR form:', error);
            }
        });
    }

    const listPrsForm = document.getElementById('listPrsForm');
    if (listPrsForm) {
        listPrsForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const listPrsBtn = document.getElementById('listPrsBtn');
            const repoFull = document.getElementById('repoFullName').value;
            const state = document.querySelector('input[name="prState"]:checked').value;
            if (!repoFull) return showAlert('Repo Full Name is required', 'danger');

            toggleLoading(listPrsBtn, true);
            try {
                const response = await fetch(`/api/repos/${repoFull}/prs?state=${state}`);
                const prs = await response.json();

                if (!response.ok) {
                    showAlert(prs.error || 'Failed to fetch PRs', 'danger');
                    return;
                }

                const tbody = document.querySelector('#prsTable tbody');
                tbody.innerHTML = '';
                if (prs.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted">No ${state} pull requests found.</td></tr>`;
                }
                prs.forEach(pr => {
                    const tr = document.createElement('tr');
                    const collabBadge = pr.can_push ?
                        '<span class="badge bg-info text-dark ms-1" title="You can push changes to this PR branch">Collaborative</span>' :
                        '<span class="badge bg-secondary ms-1" title="Read-only access to this PR branch">Read-Only</span>';

                    const labelBadges = (pr.labels || []).map(l =>
                        `<span class="badge rounded-pill me-1" style="background-color: #${l.color}; color: ${parseInt(l.color, 16) > 0xffffff / 2 ? 'black' : 'white'}">${escapeHTML(l.name)}</span>`
                    ).join('');

                    const triageBtn = pr.state === 'open' ?
                        `<button class="btn btn-sm btn-outline-danger close-pr-btn" data-number="${escapeHTML(String(pr.number))}" aria-label="Close PR #${escapeHTML(String(pr.number))}">Close</button>` :
                        `<button class="btn btn-sm btn-outline-warning reopen-pr-btn" data-number="${escapeHTML(String(pr.number))}" aria-label="Reopen PR #${escapeHTML(String(pr.number))}">Reopen</button>`;

                    tr.innerHTML = `
                        <td>${escapeHTML(String(pr.number))}</td>
                        <td>
                            <div><a href="${escapeHTML(pr.html_url)}" target="_blank" rel="noopener noreferrer" class="fw-bold">${escapeHTML(pr.title)}</a></div>
                            <div class="mt-1">${labelBadges}</div>
                        </td>
                        <td>
                            ${escapeHTML(pr.state)}
                            ${collabBadge}
                        </td>
                        <td>
                            <div class="d-flex gap-1">
                                <button class="btn btn-sm btn-outline-info comments-pr-btn" data-number="${escapeHTML(String(pr.number))}" aria-label="View comments for PR #${escapeHTML(String(pr.number))}">Comments</button>
                                ${pr.state === 'open' ? `<button class="btn btn-sm btn-success merge-btn" data-number="${escapeHTML(String(pr.number))}" aria-label="Merge pull request #${escapeHTML(String(pr.number))}">Merge</button>` : ''}
                                ${pr.state === 'open' ? `<button class="btn btn-sm btn-primary review-btn" data-number="${escapeHTML(String(pr.number))}" aria-label="Review pull request #${escapeHTML(String(pr.number))}">Review</button>` : ''}
                                ${triageBtn}
                            </div>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
                document.querySelectorAll('.comments-pr-btn').forEach(btn => {
                    btn.addEventListener('click', () => {
                        openConversation(repoFull, btn.getAttribute('data-number'), 'pr');
                    });
                });
                document.querySelectorAll('.merge-btn').forEach(btn => {
                    btn.addEventListener('click', async () => {
                        const num = btn.getAttribute('data-number');
                        toggleLoading(btn, true);
                        try {
                            const resp = await fetch(`/api/repos/${repoFull}/prs/${num}/merge`, {
                                method: 'POST',
                                body: new URLSearchParams({commit_message: 'Merged via GH-Web'})
                            });
                            const res = await resp.json();
                            if (resp.ok) showAlert(res.message);
                            else showAlert(res.error, 'danger');
                        } catch (error) {
                            showAlert(error.message, 'danger');
                        } finally {
                            toggleLoading(btn, false);
                        }
                    });
                });

                document.querySelectorAll('.close-pr-btn').forEach(btn => {
                    btn.addEventListener('click', async () => {
                        const num = btn.getAttribute('data-number');
                        if (!confirm(`Close pull request #${num}?`)) return;
                        toggleLoading(btn, true);
                        try {
                            const resp = await fetch(`/api/repos/${repoFull}/prs/${num}/close`, {
                                method: 'POST'
                            });
                            const res = await resp.json();
                            if (resp.ok) {
                                showAlert(res.message);
                                listPrsBtn.click();
                            } else {
                                showAlert(res.error, 'danger');
                            }
                        } catch (error) {
                            showAlert(error.message, 'danger');
                        } finally {
                            toggleLoading(btn, false);
                        }
                    });
                });

                document.querySelectorAll('.reopen-pr-btn').forEach(btn => {
                    btn.addEventListener('click', async () => {
                        const num = btn.getAttribute('data-number');
                        toggleLoading(btn, true);
                        try {
                            const resp = await fetch(`/api/repos/${repoFull}/prs/${num}/reopen`, {
                                method: 'POST'
                            });
                            const res = await resp.json();
                            if (resp.ok) {
                                showAlert(res.message);
                                listPrsBtn.click();
                            } else {
                                showAlert(res.error, 'danger');
                            }
                        } catch (error) {
                            showAlert(error.message, 'danger');
                        } finally {
                            toggleLoading(btn, false);
                        }
                    });
                });
                document.querySelectorAll('.review-btn').forEach(btn => {
                    btn.addEventListener('click', async () => {
                        const num = btn.getAttribute('data-number');
                        toggleLoading(btn, true);
                        try {
                            const resp = await fetch('/api/workspace/stream-pr', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    repo_full_name: repoFull,
                                    pr_number: num
                                })
                            });
                            const res = await resp.json();
                            if (resp.ok) {
                                showAlert(res.message);
                                // Switch to Workspace tab
                                const workspaceTab = document.getElementById('workspace-tab');
                                bootstrap.Tab.getOrCreateInstance(workspaceTab).show();
                                refreshExplorer();
                            } else {
                                showAlert(res.error, 'danger');
                            }
                        } catch (error) {
                            showAlert(error.message, 'danger');
                        } finally {
                            toggleLoading(btn, false);
                        }
                    });
                });
            } catch (error) {
                showAlert(error.message, 'danger');
            } finally {
                toggleLoading(listPrsBtn, false);
            }
        });
    }

    const listReleasesForm = document.getElementById('listReleasesForm');
    if (listReleasesForm) {
        listReleasesForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const listBtn = document.getElementById('listReleasesBtn');
            const repoFull = document.getElementById('releasesRepoFullName').value;
            if (!repoFull) return showAlert('Repo Full Name is required', 'danger');

            toggleLoading(listBtn, true);
            try {
                const response = await fetch(`/api/repos/${repoFull}/releases`);
                const releases = await response.json();

                if (!response.ok) {
                    showAlert(releases.error || 'Failed to fetch releases', 'danger');
                    return;
                }

                const list = document.getElementById('releasesList');
                list.innerHTML = '';
                if (releases.length === 0) {
                    list.innerHTML = '<p class="text-muted p-3 text-center border rounded">No releases found.</p>';
                }
                releases.forEach(r => {
                    const div = document.createElement('div');
                    div.className = 'list-group-item';
                    const badge = r.draft ? '<span class="badge bg-warning text-dark me-2">Draft</span>' : (r.prerelease ? '<span class="badge bg-info text-dark me-2">Pre-release</span>' : '<span class="badge bg-success me-2">Latest</span>');
                    div.innerHTML = `
                        <div class="d-flex w-100 justify-content-between align-items-center">
                            <h6 class="mb-1 text-primary">
                                ${badge}
                                <a href="${escapeHTML(r.html_url)}" target="_blank" rel="noopener noreferrer" class="text-decoration-none">${escapeHTML(r.name || r.tag_name)}</a>
                            </h6>
                            <small class="text-muted font-monospace">${escapeHTML(r.tag_name)}</small>
                        </div>
                        <p class="mb-1 small text-truncate" style="max-width: 90%;">${escapeHTML(r.body || 'No description provided.')}</p>
                        <small class="text-muted">${r.published_at ? new Date(r.published_at).toLocaleString() : 'Not published yet'}</small>
                    `;
                    list.appendChild(div);
                });
            } catch (error) {
                showAlert(error.message, 'danger');
            } finally {
                toggleLoading(listBtn, false);
            }
        });
    }

    const refreshActions = async (repoFull) => {
        const workflowsList = document.getElementById('workflowsList');
        const runsTableBody = document.querySelector('#runsTable tbody');
        if (!workflowsList || !runsTableBody) return;

        workflowsList.innerHTML = '<div class="text-center p-3"><span class="spinner-border spinner-border-sm" role="status"></span></div>';
        runsTableBody.innerHTML = '<tr><td colspan="4" class="text-center p-3"><span class="spinner-border spinner-border-sm" role="status"></span></td></tr>';

        try {
            // Fetch Workflows
            const wfResponse = await fetch(`/api/repos/${repoFull}/actions/workflows`);
            const workflows = await wfResponse.json();

            if (wfResponse.ok) {
                workflowsList.innerHTML = '';
                if (workflows.length === 0) {
                    workflowsList.innerHTML = '<p class="text-muted p-3 text-center border rounded">No workflows found.</p>';
                } else {
                    workflows.forEach(wf => {
                        const item = document.createElement('div');
                        item.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
                        const isActive = wf.state === 'active';
                        item.innerHTML = `
                            <div class="text-truncate me-2">
                                <h6 class="mb-0 small fw-bold">${escapeHTML(wf.name)}</h6>
                                <small class="text-muted font-monospace" style="font-size: 0.75rem;">${escapeHTML(wf.path.split('/').pop())}</small>
                            </div>
                            <button class="btn btn-sm btn-outline-primary dispatch-wf-btn" data-id="${wf.id}" data-name="${escapeHTML(wf.name)}" ${isActive ? '' : 'disabled'} title="Run Workflow">▶️</button>
                        `;
                        workflowsList.appendChild(item);
                    });

                    workflowsList.querySelectorAll('.dispatch-wf-btn').forEach(btn => {
                        btn.addEventListener('click', () => {
                            document.getElementById('dispatchWorkflowId').value = btn.dataset.id;
                            document.getElementById('dispatchModalLabel').textContent = `Dispatch: ${btn.dataset.name}`;
                            const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('dispatchModal'));
                            modal.show();
                        });
                    });
                }
            } else {
                workflowsList.innerHTML = `<p class="text-danger p-3 small">${escapeHTML(workflows.error)}</p>`;
            }

            // Fetch Runs
            await refreshRuns(repoFull);

        } catch (error) {
            showAlert(error.message, 'danger');
        }
    };

    let allRuns = [];
    const refreshRuns = async (repoFull) => {
        const runsTableBody = document.querySelector('#runsTable tbody');
        try {
            const response = await fetch(`/api/repos/${repoFull}/actions/runs`);
            const runs = await response.json();
            if (response.ok) {
                allRuns = runs;
                renderRuns(runs);
            } else {
                runsTableBody.innerHTML = `<tr><td colspan="4" class="text-danger text-center p-3">${escapeHTML(runs.error)}</td></tr>`;
            }
        } catch (error) {
            runsTableBody.innerHTML = `<tr><td colspan="4" class="text-danger text-center p-3">${escapeHTML(error.message)}</td></tr>`;
        }
    };

    const renderRuns = (runs) => {
        const runsTableBody = document.querySelector('#runsTable tbody');
        runsTableBody.innerHTML = '';
        if (runs.length === 0) {
            runsTableBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted p-3">No runs found.</td></tr>';
            return;
        }

        runs.forEach(run => {
            const tr = document.createElement('tr');
            const statusClass = run.conclusion === 'success' ? 'bg-success' : (run.conclusion === 'failure' ? 'bg-danger' : (run.status === 'completed' ? 'bg-secondary' : 'bg-warning text-dark'));
            const statusText = run.conclusion || run.status;

            tr.innerHTML = `
                <td>
                    <div class="fw-bold small"><a href="${escapeHTML(run.html_url)}" target="_blank" rel="noopener noreferrer" class="text-decoration-none">${escapeHTML(run.name)}</a></div>
                    <small class="text-muted">#${run.run_number} by ${escapeHTML(run.sha.substring(0, 7))}</small>
                </td>
                <td><span class="badge ${statusClass} small">${escapeHTML(statusText.toUpperCase())}</span></td>
                <td><span class="badge bg-light text-dark border small">${escapeHTML(run.branch)}</span></td>
                <td><small class="text-muted" title="${escapeHTML(new Date(run.updated_at).toLocaleString())}">${timeAgo(run.updated_at)}</small></td>
            `;
            runsTableBody.appendChild(tr);
        });
    };

    const listActionsForm = document.getElementById('listActionsForm');
    if (listActionsForm) {
        listActionsForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const repoFull = document.getElementById('actionsRepoFullName').value;
            if (repoFull) refreshActions(repoFull);
        });
    }

    const confirmDispatchBtn = document.getElementById('confirmDispatchBtn');
    if (confirmDispatchBtn) {
        confirmDispatchBtn.addEventListener('click', async () => {
            const workflowId = document.getElementById('dispatchWorkflowId').value;
            const ref = document.getElementById('dispatchRef').value;
            const repoFull = document.getElementById('actionsRepoFullName').value;

            if (!workflowId || !ref || !repoFull) return;

            toggleLoading(confirmDispatchBtn, true);
            try {
                const response = await fetch(`/api/repos/${repoFull}/actions/workflows/${workflowId}/dispatch`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ref: ref })
                });
                const result = await response.json();
                if (response.ok) {
                    showAlert(result.message);
                    bootstrap.Modal.getInstance(document.getElementById('dispatchModal')).hide();
                    // Refresh runs after a short delay to allow GitHub to register the dispatch
                    setTimeout(() => refreshRuns(repoFull), 2000);
                } else {
                    showAlert(result.error, 'danger');
                }
            } catch (error) {
                showAlert(error.message, 'danger');
            } finally {
                toggleLoading(confirmDispatchBtn, false);
            }
        });
    }

    const runSearch = document.getElementById('runSearch');
    if (runSearch) {
        runSearch.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const filtered = allRuns.filter(r =>
                r.name.toLowerCase().includes(query) ||
                r.branch.toLowerCase().includes(query) ||
                r.status.toLowerCase().includes(query) ||
                (r.conclusion && r.conclusion.toLowerCase().includes(query))
            );
            renderRuns(filtered);
        });
    }

    const generateNotesBtn = document.getElementById('generateNotesBtn');
    if (generateNotesBtn) {
        generateNotesBtn.addEventListener('click', async () => {
            const repoFull = document.getElementById('releasesRepoFullName').value;
            const tagName = document.getElementById('releaseTagName').value;
            const target = document.getElementById('releaseTarget').value;

            if (!repoFull || !tagName) {
                return showAlert('Repo Full Name and Tag Name are required to generate notes', 'warning');
            }

            toggleLoading(generateNotesBtn, true);
            try {
                const response = await fetch(`/api/repos/${repoFull}/releases/generate-notes`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ tag_name: tagName, target_commitish: target })
                });
                const result = await response.json();
                if (response.ok) {
                    document.getElementById('releaseName').value = result.name || '';
                    document.getElementById('releaseBody').value = result.body || '';
                    showAlert('Release notes generated successfully');
                } else {
                    showAlert(result.error, 'danger');
                }
            } catch (error) {
                showAlert(error.message, 'danger');
            } finally {
                toggleLoading(generateNotesBtn, false);
            }
        });
    }

    const createReleaseForm = document.getElementById('createReleaseForm');
    if (createReleaseForm) {
        createReleaseForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = createReleaseForm.querySelector('button[type="submit"]');
            const repoFull = document.getElementById('releasesRepoFullName').value;
            if (!repoFull) return showAlert('Repo Full Name is required', 'danger');

            toggleLoading(submitBtn, true);
            const formData = new URLSearchParams(new FormData(createReleaseForm));
            try {
                const response = await fetch(`/api/repos/${repoFull}/releases`, {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                if (response.ok) {
                    showAlert(result.message);
                    document.getElementById('listReleasesBtn').click();
                } else {
                    showAlert(result.error, 'danger');
                }
            } catch (error) {
                showAlert(error.message, 'danger');
            } finally {
                toggleLoading(submitBtn, false);
            }
        });
    }

    const confirmPublishBtn = document.getElementById('confirmPublishBtn');
    if (confirmPublishBtn) {
        confirmPublishBtn.addEventListener('click', async () => {
            const originalName = document.getElementById('publishTemplateOriginalName').value;
            const repoName = document.getElementById('publishRepoName').value;
            const description = document.getElementById('publishRepoDescription').value;
            const visibility = document.querySelector('input[name="visibility"]:checked').value;

            if (!repoName) return showAlert('Repository name is required', 'danger');

            toggleLoading(confirmPublishBtn, true);
            try {
                const response = await fetch(`/api/workspace/templates/${encodeURIComponent(originalName)}/publish`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: repoName,
                        description: description,
                        visibility: visibility
                    })
                });
                const result = await response.json();
                if (response.ok) {
                    showAlert(result.message);
                    bootstrap.Modal.getInstance(document.getElementById('publishTemplateModal')).hide();
                } else {
                    showAlert(result.error, 'danger');
                }
            } catch (error) {
                showAlert(error.message, 'danger');
            } finally {
                toggleLoading(confirmPublishBtn, false);
            }
        });
    }

    // Global Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
        // Global / shortcut for contextual search
        if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName) && !document.querySelector('.modal.show')) {
            const activeTabEl = document.querySelector('#mainTabs .nav-link.active');
            if (!activeTabEl) return;

            const activeTab = activeTabEl.id;
            let searchInputId = '';

            switch (activeTab) {
                case 'dashboard-tab':
                    searchInputId = 'dashboardRepoSearch';
                    break;
                case 'actions-tab':
                    searchInputId = 'runSearch';
                    break;
                case 'workspace-tab':
                    searchInputId = 'workspaceOmniSearch';
                    break;
            }

            if (searchInputId) {
                const input = document.getElementById(searchInputId);
                if (input) {
                    e.preventDefault();
                    input.focus();
                    input.select();
                }
            }
        }
    });
});
