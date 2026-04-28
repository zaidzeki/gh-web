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
            button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
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

                refreshDashboardRepos();
                refreshWorkspacePortfolio();
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
            const repoAriaLabel = `Open repository ${escapeHTML(repo.full_name)}${repo.open_prs_count > 0 ? ` (${repo.open_prs_count} open pull requests)` : ''}`;

            item.innerHTML = `
                <div>
                    <h6 class="mb-0 text-primary" style="cursor:pointer;" data-repo="${escapeHTML(repo.full_name)}" tabindex="0" role="button" aria-label="${repoAriaLabel}">
                        ${escapeHTML(repo.full_name)}
                        ${prBadge}
                    </h6>
                    <small class="text-muted text-truncate d-block" style="max-width: 400px;" title="${escapeHTML(repo.description || 'No description')}">${escapeHTML(repo.description || 'No description')}</small>
                </div>
                <div class="d-flex gap-2">
                    <button class="btn btn-sm btn-outline-secondary issues-action" data-repo="${escapeHTML(repo.full_name)}" aria-label="View issues for ${escapeHTML(repo.full_name)}">Issues</button>
                    <button class="btn btn-sm btn-outline-secondary pr-action" data-repo="${escapeHTML(repo.full_name)}" aria-label="View pull requests for ${escapeHTML(repo.full_name)}">PRs</button>
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

                div.innerHTML = `
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div class="text-truncate" style="max-width: 60%;">
                            <h6 class="mb-0 text-primary open-workspace" style="cursor:pointer;" data-repo-name="${escapeHTML(item.repo_name)}" tabindex="0" role="button" aria-label="Open workspace ${escapeHTML(item.repo_name)} (${statusText})">${escapeHTML(item.repo_name)}</h6>
                            <small class="text-muted font-monospace">${escapeHTML(item.branch)}</small>
                        </div>
                        ${statusBadge}
                    </div>
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
            if (!repoFull) return showAlert('Repo Full Name is required', 'danger');

            toggleLoading(listIssuesBtn, true);
            try {
                const response = await fetch(`/api/repos/${repoFull}/issues`);
                const issues = await response.json();

                if (!response.ok) {
                    showAlert(issues.error || 'Failed to fetch Issues', 'danger');
                    return;
                }

                const tbody = document.querySelector('#issuesTable tbody');
                tbody.innerHTML = '';
                if (issues.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No open issues found.</td></tr>';
                }
                issues.forEach(issue => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${escapeHTML(String(issue.number))}</td>
                        <td><a href="${escapeHTML(issue.html_url)}" target="_blank">${escapeHTML(issue.title)}</a></td>
                        <td><small class="text-muted">${escapeHTML(new Date(issue.created_at).toLocaleDateString())}</small></td>
                        <td>
                            <button class="btn btn-sm btn-outline-info comments-issue-btn" data-number="${escapeHTML(String(issue.number))}" aria-label="View comments for issue #${escapeHTML(String(issue.number))}">Comments</button>
                            <button class="btn btn-sm btn-outline-primary fix-issue-btn" data-number="${escapeHTML(String(issue.number))}" aria-label="Fix issue #${escapeHTML(String(issue.number))}">Fix</button>
                            <button class="btn btn-sm btn-outline-danger close-issue-btn" data-number="${escapeHTML(String(issue.number))}" aria-label="Close issue #${escapeHTML(String(issue.number))}">Close</button>
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
                        <button class="btn btn-sm btn-outline-danger delete-template-btn" data-template="${t}" aria-label="Delete template ${escapeHTML(t)}" title="Delete template ${escapeHTML(t)}">Delete</button>
                    `;
                    libraryList.appendChild(item);
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
                } else {
                    statusBadge.textContent = 'Clean';
                    statusBadge.className = 'badge bg-success';
                }
                statusBadge.style.display = 'inline-block';

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
            if (!repoFull) return showAlert('Repo Full Name is required', 'danger');

            toggleLoading(listPrsBtn, true);
            try {
                const response = await fetch(`/api/repos/${repoFull}/prs`);
                const prs = await response.json();

                if (!response.ok) {
                    showAlert(prs.error || 'Failed to fetch PRs', 'danger');
                    return;
                }

                const tbody = document.querySelector('#prsTable tbody');
                tbody.innerHTML = '';
                if (prs.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No open pull requests found.</td></tr>';
                }
                prs.forEach(pr => {
                    const tr = document.createElement('tr');
                    const collabBadge = pr.can_push ?
                        '<span class="badge bg-info text-dark ms-1" title="You can push changes to this PR branch">Collaborative</span>' :
                        '<span class="badge bg-secondary ms-1" title="Read-only access to this PR branch">Read-Only</span>';

                    tr.innerHTML = `
                        <td>${escapeHTML(String(pr.number))}</td>
                        <td><a href="${escapeHTML(pr.html_url)}" target="_blank">${escapeHTML(pr.title)}</a></td>
                        <td>
                            ${escapeHTML(pr.state)}
                            ${collabBadge}
                        </td>
                        <td>
                            <button class="btn btn-sm btn-outline-info comments-pr-btn" data-number="${escapeHTML(String(pr.number))}" aria-label="View comments for PR #${escapeHTML(String(pr.number))}">Comments</button>
                            <button class="btn btn-sm btn-success merge-btn" data-number="${escapeHTML(String(pr.number))}" aria-label="Merge pull request #${escapeHTML(String(pr.number))}">Merge</button>
                            <button class="btn btn-sm btn-primary review-btn" data-number="${escapeHTML(String(pr.number))}" aria-label="Review pull request #${escapeHTML(String(pr.number))}">Review</button>
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
});
