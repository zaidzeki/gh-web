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

    let currentOrg = '';
    let currentTeamId = '';
    let currentTeamSlug = '';
    let currentHealthFilter = 'all';
    let healthDataCache = {};

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

                await refreshDashboardOrgs();
                await refreshDashboardRepos();
                refreshWorkspacePortfolio();
                refreshTaskInbox();
                refreshPortfolioRoadmap();
                refreshPortfolioPulse();
                refreshPortfolioSecurity();
            } else {
                profileDiv.classList.add('d-none');
                profileDiv.classList.remove('d-flex');
                if (loginForm) loginForm.classList.remove('d-none');
            }
        } catch (error) {
            console.error('Failed to fetch user profile:', error);
        }
    };

    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/logout', { method: 'POST' });
                if (response.ok) {
                    window.location.reload();
                }
            } catch (error) {
                console.error('Logout failed:', error);
            }
        });
    }

    const refreshDashboardOrgs = async () => {
        const container = document.getElementById('orgContextSwitcherContainer');
        const list = document.getElementById('orgContextList');
        if (!container || !list) return;

        try {
            const response = await fetch('/api/user/orgs');
            const orgs = await response.json();

            if (response.ok && orgs.length > 0) {
                container.style.display = 'block';
                // Remove existing items (keep Personal and Divider)
                while (list.children.length > 2) {
                    list.removeChild(list.lastChild);
                }

                for (const org of orgs) {
                    const orgLi = document.createElement('li');
                    orgLi.innerHTML = `
                        <a class="dropdown-item d-flex align-items-center gap-2" href="#" data-org="${escapeHTML(org.login)}">
                            <img src="${escapeHTML(org.avatar_url)}" width="20" height="20" class="rounded-circle">
                            ${escapeHTML(org.login)}
                        </a>
                    `;
                    list.appendChild(orgLi);

                    // Fetch teams for this org
                    try {
                        const teamsResp = await fetch(`/api/user/orgs/${encodeURIComponent(org.login)}/teams`);
                        const teams = await teamsResp.json();
                        if (teamsResp.ok && teams.length > 0) {
                            teams.forEach(team => {
                                const teamLi = document.createElement('li');
                                teamLi.innerHTML = `
                                    <a class="dropdown-item d-flex align-items-center gap-2 ps-4" href="#" data-org="${escapeHTML(org.login)}" data-team-id="${team.id}" data-team-slug="${escapeHTML(team.slug)}">
                                        <span class="text-muted small">↳</span> ${escapeHTML(team.name)}
                                    </a>
                                `;
                                list.appendChild(teamLi);
                            });
                        }
                    } catch (e) {
                        console.error(`Failed to fetch teams for ${org.login}:`, e);
                    }
                }

                list.querySelectorAll('.dropdown-item').forEach(item => {
                    item.addEventListener('click', (e) => {
                        e.preventDefault();
                        const org = item.getAttribute('data-org');
                        const teamId = item.getAttribute('data-team-id') || '';
                        const teamSlug = item.getAttribute('data-team-slug') || '';

                        if (org === currentOrg && teamId === currentTeamId) return;

                        // Update active state
                        list.querySelectorAll('.dropdown-item').forEach(i => i.classList.remove('active'));
                        item.classList.add('active');

                        // Update button text
                        const btn = document.getElementById('orgContextSwitcher');
                        if (teamId) {
                            btn.querySelector('span').textContent = `${org} / ${item.textContent.replace('↳', '').trim()}`;
                        } else {
                            btn.querySelector('span').textContent = org || 'Personal';
                        }

                        currentOrg = org;
                        currentTeamId = teamId;
                        currentTeamSlug = teamSlug;

                        refreshDashboardRepos();
                        refreshTaskInbox();
                    });
                });
            } else {
                container.style.display = 'none';
            }
        } catch (error) {
            console.error('Failed to fetch organizations:', error);
        }
    };

    let allRepos = [];
    const refreshDashboardRepos = async (search = '') => {
        const repoList = document.getElementById('dashboardRepoList');
        if (!repoList) return;

        try {
            const params = new URLSearchParams();
            if (search) params.set('search', search);
            if (currentOrg) params.set('org_name', currentOrg);
            if (currentTeamId) params.set('team_id', currentTeamId);

            const queryString = params.toString();
            const url = queryString ? `/api/repos?${queryString}` : '/api/repos';

            const response = await fetch(url);
            const repos = await response.json();

            if (!response.ok) {
                repoList.innerHTML = `<p class="text-danger p-3">${escapeHTML(repos.error || 'Failed to fetch repositories')}</p>`;
                return;
            }

            allRepos = repos;
            renderRepoList(repos);
            await refreshRepoHealth(repos.map(r => r.full_name));
            refreshRepoPulse(repos.map(r => r.full_name));
            refreshRepoPolicy(repos.map(r => r.full_name));

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

        let filteredRepos = repos;
        if (currentHealthFilter !== 'all') {
            filteredRepos = repos.filter(repo => {
                const health = healthDataCache[repo.full_name];
                if (currentHealthFilter === 'failure') return health && health.ci_status === 'failure';
                if (currentHealthFilter === 'pending') return health && (health.ci_status === 'pending' || health.ci_status === 'in_progress' || health.ci_status === 'queued');
                if (currentHealthFilter === 'modified') {
                    // Check if this repo is in the workspace portfolio and is dirty
                    const portfolioItem = lastPortfolioData ? lastPortfolioData.find(p => p.full_name === repo.full_name || p.repo_name === repo.name) : null;
                    return portfolioItem && (portfolioItem.is_dirty || portfolioItem.untracked);
                }
                return true;
            });
        }

        if (filteredRepos.length === 0) {
            repoList.innerHTML = `<p class="text-muted p-3">No repositories found matching current filters.</p>`;
            return;
        }

        repoList.innerHTML = '';
        filteredRepos.forEach(repo => {
            const item = document.createElement('div');
            item.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center repo-item';
            item.dataset.repo = repo.full_name;
            const prBadge = repo.open_prs_count > 0 ?
                `<span class="badge bg-warning text-dark ms-2" title="${repo.open_prs_count} open pull requests">${repo.open_prs_count} PRs</span>` : '';
            const issueBadge = repo.open_issues_count > 0 ?
                `<span class="badge bg-secondary ms-2" title="${repo.open_issues_count} open issues">${repo.open_issues_count} Issues</span>` : '';
            const pushedStr = repo.pushed_at ? timeAgo(repo.pushed_at) : 'never';

            const repoAriaLabel = `Open repository ${escapeHTML(repo.full_name)}. ${repo.open_issues_count} issues, ${repo.open_prs_count} pull requests. Last pushed ${pushedStr}.`;

            item.innerHTML = `
                <div class="flex-grow-1 text-truncate">
                    <div class="d-flex align-items-center mb-1">
                        <h6 class="mb-0 text-primary" style="cursor:pointer;" data-repo="${escapeHTML(repo.full_name)}" tabindex="0" role="button" aria-label="${repoAriaLabel}">
                            ${escapeHTML(repo.full_name)}
                        </h6>
                        <span class="policy-badge ms-1"></span>
                        ${issueBadge}
                        ${prBadge}
                        <span class="health-badges ms-2"></span>
                    </div>
                    <small class="text-muted text-truncate d-block" style="max-width: 500px;" title="${escapeHTML(repo.description || 'No description')}">
                        <span class="badge bg-light text-dark border me-1" title="${repo.pushed_at ? new Date(repo.pushed_at).toLocaleString() : 'Never'}">${pushedStr}</span>
                        <span class="ci-text-status small me-1"></span>
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

    const refreshRepoPulse = async (repoNames) => {
        if (!repoNames || repoNames.length === 0) return;

        repoNames.forEach(async (repoName) => {
            try {
                const response = await fetch(`/api/repos/${repoName}/pulse`);
                const data = await response.json();
                if (response.ok) {
                    const item = document.querySelector(`.repo-item[data-repo="${repoName}"]`);
                    if (item) {
                        const badgesContainer = item.querySelector('.health-badges');
                        if (badgesContainer) {
                            const m = data.metrics;
                            const t = data.trends;
                            const b = data.benchmarks;

                            const tierClasses = {
                                'Elite': 'bg-primary',
                                'High': 'bg-success',
                                'Medium': 'bg-warning text-dark',
                                'Low': 'bg-danger'
                            };

                            const getTrendArrow = (curr, prev) => {
                                if (curr == null || prev == null || curr === prev) return '';
                                return curr > prev ? '↑' : '↓';
                            };

                            const trendClass = (status) => {
                                if (status === 'improving') return 'text-success';
                                if (status === 'degrading') return 'text-danger';
                                return 'text-muted';
                            };

                            const pm = data.previous_metrics || {};
                            const pulseHtml = `
                                <span class="badge ${tierClasses[b.overall] || 'bg-dark'} ms-1 pulse-badge"
                                      title="DORA Tier: ${escapeHTML(b.overall)}. Metrics: ${escapeHTML(String(m.deployment_frequency))} deploys ${getTrendArrow(m.deployment_frequency, pm.deployment_frequency)}, ${escapeHTML(String(m.lead_time_to_change_hours || '?'))}h lead time ${getTrendArrow(m.lead_time_to_change_hours, pm.lead_time_to_change_hours)}">
                                    📈 ${escapeHTML(String(m.deployment_frequency))} <span class="${trendClass(t.deployment_frequency)}">${getTrendArrow(m.deployment_frequency, pm.deployment_frequency)}</span>
                                </span>
                            `;
                            const existing = badgesContainer.querySelector('.pulse-badge');
                            if (existing) existing.remove();
                            badgesContainer.insertAdjacentHTML('beforeend', pulseHtml);
                        }
                    }
                }
            } catch (e) {
                console.error(`Failed to fetch pulse for ${repoName}:`, e);
            }
        });
    };

    const refreshRepoPolicy = async (repoNames) => {
        if (!repoNames || repoNames.length === 0) return;
        repoNames.forEach(async (repoName) => {
            try {
                const response = await fetch(`/api/repos/${repoName}/governance/policy`);
                const data = await response.json();
                if (response.ok) {
                    const item = document.querySelector(`.repo-item[data-repo="${repoName}"]`);
                    if (item) {
                        const badgeContainer = item.querySelector('.policy-badge');
                        if (badgeContainer) {
                            const badgeClass = data.compliant ? 'bg-success' : 'bg-danger';
                            const title = data.compliant ? 'Policy Compliant' : `Policy Violations: ${data.violations.map(v => v.message).join(', ')}`;
                            badgeContainer.innerHTML = `<span class="badge ${badgeClass} small" title="${escapeHTML(title)}">POL</span>`;
                        }
                    }
                }
            } catch (e) {
                console.error(`Failed to fetch policy for ${repoName}:`, e);
            }
        });
    };

    const refreshRepoHealth = async (repoNames) => {
        if (!repoNames || repoNames.length === 0) return;

        try {
            const response = await fetch(`/api/repos/health?repos=${encodeURIComponent(repoNames.join(','))}`);
            const healthData = await response.json();

            if (response.ok) {
                Object.assign(healthDataCache, healthData);
                document.querySelectorAll('.repo-item').forEach(item => {
                    const repoName = item.dataset.repo;
                    const health = healthDataCache[repoName];
                    if (health) {
                        const badgesContainer = item.querySelector('.health-badges');
                        if (badgesContainer) {
                            let badgesHtml = '';
                            if (health.ci_status) {
                                const ciClass = health.ci_status === 'success' ? 'bg-success' : (health.ci_status === 'failure' ? 'bg-danger' : 'bg-warning text-dark');
                                badgesHtml += `<span class="badge ${ciClass} ms-1 health-ci-badge" title="CI Status: ${escapeHTML(health.ci_status)}">CI: ${escapeHTML(health.ci_status.toUpperCase())}</span>`;

                                const ciTextEl = item.querySelector('.ci-text-status');
                                if (ciTextEl) {
                                    ciTextEl.textContent = health.ci_status === 'success' ? 'Passed CI' : (health.ci_status === 'failure' ? 'Failed CI' : 'CI Pending');
                                    ciTextEl.className = `ci-text-status small me-1 ${health.ci_status === 'failure' ? 'text-danger' : 'text-muted'}`;
                                }
                            }
                            if (health.next_milestone) {
                                const ms = health.next_milestone;
                                const msClass = ms.overdue ? 'bg-danger' : 'bg-primary';
                                const dueStr = new Date(ms.due_on).toLocaleDateString();
                                badgesHtml += `<span class="badge ${msClass} ms-1 health-ms-badge" title="Next Milestone: ${escapeHTML(ms.title)} (Due: ${dueStr})">🎯 ${escapeHTML(ms.title)}</span>`;
                            }
                            if (health.production_status) {
                                badgesHtml += `<span class="badge bg-info text-dark ms-1 health-prod-badge" title="Production Ref: ${health.production_status.ref}">Prod: ${escapeHTML(health.production_status.ref)}</span>`;
                            }

                            if (health.security_status) {
                                const secClass = health.security_status === 'failure' ? 'bg-danger' : (health.security_status === 'warning' ? 'bg-warning text-dark' : 'bg-success');
                                const s = health.security_summary;
                                const title = s ? `Security: ${s.vulnerabilities.critical} Crit, ${s.vulnerabilities.high} High, ${s.secrets.open} Secrets. Click to explore.` : `Security Status: ${health.security_status}. Click to explore.`;
                                badgesHtml += `<span class="badge ${secClass} ms-1 health-sec-badge" style="cursor: pointer;" title="${escapeHTML(title)}" data-repo="${escapeHTML(repoName)}">🛡️</span>`;
                            }

                            badgesContainer.querySelectorAll('.health-ci-badge, .health-ms-badge, .health-prod-badge, .health-sec-badge').forEach(el => el.remove());
                            badgesContainer.insertAdjacentHTML('afterbegin', badgesHtml);
                            badgesContainer.querySelectorAll('.health-sec-badge').forEach(badge => {
                                badge.addEventListener('click', (e) => {
                                    e.stopPropagation();
                                    openSecurityExplorer(badge.dataset.repo);
                                });
                            });
                        }
                    }
                });
            }
        } catch (error) {
            console.error('Failed to fetch repo health:', error);
        }
    };

    const dashboardRepoSearch = document.getElementById('dashboardRepoSearch');
    if (dashboardRepoSearch) {
        let timeout = null;
        dashboardRepoSearch.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            if (timeout) clearTimeout(timeout);

            // Client-side filtering (Search + Health)
            renderRepoList(allRepos.filter(r => r.full_name.toLowerCase().includes(query) || (r.description && r.description.toLowerCase().includes(query))));

            // Debounced server-side search if needed
            timeout = setTimeout(() => {
                const queryFiltered = allRepos.filter(r => r.full_name.toLowerCase().includes(query) || (r.description && r.description.toLowerCase().includes(query)));
                if (query && queryFiltered.length < 5) {
                    refreshDashboardRepos(query);
                }
            }, 500);
        });
    }

    document.querySelectorAll('.health-filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.health-filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentHealthFilter = btn.dataset.filter;
            renderRepoList(allRepos);
        });
    });

    let lastPortfolioData = null;
    const refreshWorkspacePortfolio = async () => {
        const portfolioList = document.getElementById('activeWorkspacesList');
        if (!portfolioList) return;

        try {
            const response = await fetch('/api/workspace/portfolio');
            const data = await response.json();
            lastPortfolioData = data;

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

                let ciBadge = '';
                if (item.ci_status) {
                    const ciClass = item.ci_status === 'success' ? 'bg-success' : (item.ci_status === 'failure' ? 'bg-danger' : 'bg-warning text-dark');
                    ciBadge = `<span class="badge ${ciClass} ms-1" title="CI Status: ${item.ci_status}">CI</span>`;
                }

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
                                ${aheadBadge}${behindBadge}${ciBadge}
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

            refreshPortfolioPulse();
            refreshPortfolioSecurity();
        } catch (error) {
            portfolioList.innerHTML = `<p class="text-danger p-3">Error: ${escapeHTML(error.message)}</p>`;
        }
    };

    const refreshPortfolioPulse = async () => {
        const card = document.getElementById('portfolioPulseCard');
        if (!card) return;

        if (!lastPortfolioData || lastPortfolioData.length === 0) {
            card.style.display = 'none';
            return;
        }

        card.style.display = 'block';
        const repoNames = lastPortfolioData.map(item => item.full_name).filter(Boolean);
        if (repoNames.length === 0) return;

        try {
            const response = await fetch(`/api/workspace/portfolio/pulse?repos=${encodeURIComponent(repoNames.join(','))}`);
            const data = await response.json();
            if (response.ok) {
                const m = data.metrics;
                const t = data.trends;
                const b = data.benchmarks;

                const tierClasses = {
                    'Elite': 'bg-primary',
                    'High': 'bg-success',
                    'Medium': 'bg-warning text-dark',
                    'Low': 'bg-danger'
                };

                const tierEl = document.getElementById('portfolioOverallTier');
                if (tierEl) {
                    tierEl.textContent = `Overall Performance: ${b.overall}`;
                    tierEl.className = `badge rounded-pill ${tierClasses[b.overall] || 'bg-secondary'} fs-6`;
                }

                const pm = data.previous_metrics || {};
                const renderMetric = (id, val, prevVal, trend, suffix = '') => {
                    const el = document.getElementById(id);
                    const trendEl = document.getElementById(`${id}Trend`);
                    if (el) el.textContent = val !== null ? val + suffix : '-';
                    if (trendEl) {
                        let arrow = '';
                        if (val !== null && prevVal !== null) {
                            if (val > prevVal) arrow = '↑';
                            else if (val < prevVal) arrow = '↓';
                        }
                        trendEl.textContent = arrow;
                        trendEl.className = `small fw-bold ${trend === 'improving' ? 'text-success' : (trend === 'degrading' ? 'text-danger' : 'text-muted')}`;
                    }
                };

                renderMetric('portfolioFreq', m.deployment_frequency, pm.deployment_frequency, t.deployment_frequency);
                renderMetric('portfolioLead', m.lead_time_to_change_hours, pm.lead_time_to_change_hours, t.lead_time_to_change_hours);
                renderMetric('portfolioCFR', m.change_failure_rate_percent, pm.change_failure_rate_percent, t.change_failure_rate_percent, '%');
                renderMetric('portfolioRestore', m.time_to_restore_hours, pm.time_to_restore_hours, t.time_to_restore_hours);
                renderMetric('portfolioMTTR', m.security_mttr_hours, pm.security_mttr_hours, t.security_mttr_hours);
                renderMetric('portfolioFreshness', m.dependency_freshness_index, null, null, '%');
            }
        } catch (e) {
            console.error('Failed to fetch portfolio pulse:', e);
        }
    };

    const refreshPortfolioPulseBtn = document.getElementById('refreshPortfolioPulseBtn');
    if (refreshPortfolioPulseBtn) {
        refreshPortfolioPulseBtn.addEventListener('click', () => {
            toggleLoading(refreshPortfolioPulseBtn, true);
            refreshPortfolioPulse().finally(() => toggleLoading(refreshPortfolioPulseBtn, false));
        });
    }

    const refreshPortfolioBtn = document.getElementById('refreshPortfolioBtn');
    if (refreshPortfolioBtn) {
        refreshPortfolioBtn.addEventListener('click', () => {
            toggleLoading(refreshPortfolioBtn, true);
            refreshWorkspacePortfolio().finally(() => toggleLoading(refreshPortfolioBtn, false));
        });
    }

    const refreshPortfolioSecurity = async () => {
        const container = document.getElementById('portfolioSecurityContainer');
        const card = document.getElementById('portfolioSecurityCard');
        if (!container || !card) return;

        if (!lastPortfolioData || lastPortfolioData.length === 0) {
            card.style.display = 'none';
            return;
        }

        const vulnerableRepos = lastPortfolioData.filter(repo => {
            const health = healthDataCache[repo.full_name];
            return health && (health.security_status === 'failure' || health.security_status === 'warning');
        });

        if (vulnerableRepos.length === 0) {
            card.style.display = 'none';
            return;
        }

        card.style.display = 'block';
        container.innerHTML = '';

        // Calculate aggregated totals
        let totalCrit = 0;
        let totalHigh = 0;
        let totalSecrets = 0;

        vulnerableRepos.forEach(repo => {
            const health = healthDataCache[repo.full_name];
            if (health && health.security_summary) {
                totalCrit += health.security_summary.vulnerabilities.critical || 0;
                totalHigh += health.security_summary.vulnerabilities.high || 0;
                totalSecrets += health.security_summary.secrets.open || 0;
            }
        });

        // Add summary header
        const summaryDiv = document.createElement('div');
        summaryDiv.className = 'col-12 mb-3';
        summaryDiv.innerHTML = `
            <div class="alert alert-danger d-flex justify-content-around align-items-center py-2 mb-0 shadow-sm">
                <div class="text-center">
                    <div class="h4 mb-0 fw-bold">${totalCrit}</div>
                    <small class="text-uppercase fw-bold" style="font-size: 0.7rem;">Critical</small>
                </div>
                <div class="vr"></div>
                <div class="text-center">
                    <div class="h4 mb-0 fw-bold text-warning">${totalHigh}</div>
                    <small class="text-uppercase fw-bold text-muted" style="font-size: 0.7rem;">High Risk</small>
                </div>
                <div class="vr"></div>
                <div class="text-center">
                    <div class="h4 mb-0 fw-bold">${totalSecrets}</div>
                    <small class="text-uppercase fw-bold text-muted" style="font-size: 0.7rem;">Secrets</small>
                </div>
            </div>
        `;
        container.appendChild(summaryDiv);

        vulnerableRepos.forEach(repo => {
            const health = healthDataCache[repo.full_name];
            if (!health || !health.security_status) return;
            const s = health.security_summary || { vulnerabilities: { critical: 0, high: 0 }, secrets: { open: 0 } };
            const col = document.createElement('div');
            col.className = 'col';

            const badgeClass = health.security_status === 'failure' ? 'bg-danger' : 'bg-warning text-dark';

            col.innerHTML = `
                <div class="card h-100 shadow-sm border-0 security-repo-card" style="cursor: pointer;" data-repo="${escapeHTML(repo.full_name)}">
                    <div class="card-body p-3">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="card-title mb-0 text-truncate" title="${escapeHTML(repo.full_name)}">${escapeHTML(repo.full_name)}</h6>
                            <span class="badge ${badgeClass} security-explorer-trigger" style="cursor: pointer;" data-repo="${escapeHTML(repo.full_name)}" title="Explore alerts">🛡️ ${escapeHTML(health.security_status.toUpperCase())}</span>
                        </div>
                        <div class="row text-center g-1">
                            <div class="col-4">
                                <div class="fw-bold text-danger">${s.vulnerabilities.critical}</div>
                                <div class="small text-muted" style="font-size: 0.6rem;">CRIT</div>
                            </div>
                            <div class="col-4 border-start">
                                <div class="fw-bold text-warning">${s.vulnerabilities.high}</div>
                                <div class="small text-muted" style="font-size: 0.6rem;">HIGH</div>
                            </div>
                            <div class="col-4 border-start">
                                <div class="fw-bold ${s.secrets.open > 0 ? 'text-danger' : 'text-muted'}">${s.secrets.open}</div>
                                <div class="small text-muted" style="font-size: 0.6rem;">SECRETS</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            col.querySelector('.security-explorer-trigger').addEventListener('click', (e) => {
                e.stopPropagation();
                openSecurityExplorer(repo.full_name);
            });

            col.querySelector('.security-repo-card').addEventListener('click', async () => {
                try {
                    await fetch('/api/workspace/activate', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({repo_name: repo.name})
                    });
                    bootstrap.Tab.getOrCreateInstance(document.getElementById('workspace-tab')).show();
                    refreshExplorer();
                } catch (e) {}
            });

            container.appendChild(col);
        });
    };

    const refreshPortfolioSecurityBtn = document.getElementById('refreshPortfolioSecurityBtn');
    if (refreshPortfolioSecurityBtn) {
        refreshPortfolioSecurityBtn.addEventListener('click', async () => {
            toggleLoading(refreshPortfolioSecurityBtn, true);
            try {
                const repoNames = lastPortfolioData ? lastPortfolioData.map(item => item.full_name).filter(Boolean) : [];
                if (repoNames.length > 0) {
                    await refreshRepoHealth(repoNames);
                }
                await refreshPortfolioSecurity();
            } finally {
                toggleLoading(refreshPortfolioSecurityBtn, false);
            }
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
            const params = new URLSearchParams();
            if (currentOrg) params.set('org_name', currentOrg);
            if (currentTeamSlug) params.set('team_slug', currentTeamSlug);
            if (currentTeamId) params.set('team_id', currentTeamId);
            const milestoneFilter = document.getElementById('taskMilestoneFilter');
            if (milestoneFilter && milestoneFilter.value) {
                params.set('milestone', milestoneFilter.value);
            }
            const securityToggle = document.getElementById('securityOnlyToggle');
            if (securityToggle && securityToggle.checked) {
                params.set('category', 'security_vulnerability');
            }

            const url = params.toString() ? `/api/tasks?${params.toString()}` : '/api/tasks';
            const response = await fetch(url);
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

                const typeIcon = task.type === 'pr' ? '🌿' : (task.type === 'security_vulnerability' ? '🛡️' : '🎫');
                const categoryBadge = task.category === 'review_requested' ?
                    '<span class="badge bg-danger">Action Required</span>' :
                    (task.category === 'assigned' ? '<span class="badge bg-primary">In Progress</span>' :
                    (task.category === 'waiting_deployment' ? '<span class="badge bg-warning text-dark">Waiting Deployment</span>' :
                    (task.category === 'security_vulnerability' ? '<span class="badge bg-danger">Security Alert</span>' :
                    (task.category === 'team_unassigned' ? '<span class="badge bg-info text-dark">Team Unassigned</span>' : '<span class="badge bg-secondary">My PR</span>'))));

                let statusBadges = '';
                if (task.ci_status) {
                    const ciClass = task.ci_status === 'success' ? 'bg-success' : (task.ci_status === 'failure' ? 'bg-danger' : 'bg-warning text-dark');
                    statusBadges += `<span class="badge ${ciClass} ms-1">CI: ${escapeHTML(task.ci_status.toUpperCase())}</span>`;
                }
                if (task.review_status) {
                    const revClass = task.review_status === 'approved' ? 'bg-success' : (task.review_status === 'changes_requested' ? 'bg-danger' : 'bg-warning text-dark');
                    statusBadges += `<span class="badge ${revClass} ms-1">Review: ${task.review_status.replace('_', ' ').toUpperCase()}</span>`;
                }

                if (task.milestone) {
                    const isOverdue = task.milestone.is_overdue;
                    const msClass = isOverdue ? 'bg-danger' : 'bg-primary';
                    const dueStr = task.milestone.due_on ? ` (Due: ${new Date(task.milestone.due_on).toLocaleDateString()})` : '';
                    statusBadges += `<span class="badge ${msClass} ms-1" title="Milestone: ${escapeHTML(task.milestone.title)}${dueStr}">🎯 ${escapeHTML(task.milestone.title)}</span>`;
                }

                let actionBtn = task.type === 'pr' ?
                    `<button class="btn btn-sm btn-outline-primary review-task-btn" data-repo="${escapeHTML(task.repo)}" data-number="${escapeHTML(String(task.number))}">Review</button>` :
                    `<button class="btn btn-sm btn-outline-success fix-task-btn" data-repo="${escapeHTML(task.repo)}" data-number="${escapeHTML(String(task.number))}">Fix</button>`;

                if (task.type === 'security_vulnerability') {
                    actionBtn = `<button class="btn btn-sm btn-outline-danger fix-task-btn" data-repo="${escapeHTML(task.repo)}" data-number="${escapeHTML(String(task.number))}">Patch</button>`;
                }

                if (task.category === 'waiting_deployment') {
                    if (task.pending_run_id) {
                        actionBtn = `
                            <div class="d-flex gap-1">
                                <button class="btn btn-sm btn-success approve-deploy-btn" data-repo="${escapeHTML(task.repo)}" data-run-id="${task.pending_run_id}">Approve</button>
                                <button class="btn btn-sm btn-danger reject-deploy-btn" data-repo="${escapeHTML(task.repo)}" data-run-id="${task.pending_run_id}">Reject</button>
                            </div>
                        `;
                    } else {
                        actionBtn = `<button class="btn btn-sm btn-outline-primary deploy-task-btn" data-repo="${escapeHTML(task.repo)}" data-ref="${escapeHTML(task.id.split('#')[1])}">Deploy</button>`;
                    }
                }

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
                    const isPatch = btn.textContent.trim() === 'Patch';
                    toggleLoading(btn, true);
                    try {
                        const endpoint = isPatch ? '/api/workspace/setup-security-fix' : '/api/workspace/setup-issue-fix';
                        const payload = isPatch ? {
                            repo_full_name: btn.dataset.repo,
                            alert_number: btn.dataset.number
                        } : {
                            repo_full_name: btn.dataset.repo,
                            issue_number: btn.dataset.number
                        };

                        const resp = await fetch(endpoint, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(payload)
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

            inbox.querySelectorAll('.deploy-task-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const repo = btn.dataset.repo;
                    document.querySelectorAll('.repo-full-name-input').forEach(input => input.value = repo);
                    const envTab = document.getElementById('environments-tab');
                    bootstrap.Tab.getOrCreateInstance(envTab).show();
                    refreshEnvironments(repo);
                });
            });

            inbox.querySelectorAll('.approve-deploy-btn').forEach(btn => {
                btn.addEventListener('click', async () => {
                    if (!confirm('Approve this deployment?')) return;
                    toggleLoading(btn, true);
                    try {
                        const response = await fetch(`/api/repos/${btn.dataset.repo}/actions/runs/${btn.dataset.run_id}/review`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ event: 'approve' })
                        });
                        const result = await response.json();
                        if (response.ok) {
                            showAlert(result.message);
                            refreshTaskInbox();
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

            inbox.querySelectorAll('.reject-deploy-btn').forEach(btn => {
                btn.addEventListener('click', async () => {
                    if (!confirm('Reject this deployment?')) return;
                    toggleLoading(btn, true);
                    try {
                        const response = await fetch(`/api/repos/${btn.dataset.repo}/actions/runs/${btn.dataset.run_id}/review`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ event: 'reject' })
                        });
                        const result = await response.json();
                        if (response.ok) {
                            showAlert(result.message);
                            refreshTaskInbox();
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

    const refreshPortfolioRoadmap = async () => {
        const container = document.getElementById('portfolioRoadmapContainer');
        if (!container) return;

        container.innerHTML = '<div class="col-12 text-center p-3"><span class="spinner-border spinner-border-sm" role="status"></span></div>';

        try {
            const response = await fetch('/api/workspace/portfolio/milestones');
            const milestones = await response.json();

            if (response.ok) {
                container.innerHTML = '';
                if (milestones.length === 0) {
                    container.innerHTML = '<p class="text-muted p-2 mb-0">No open milestones in active workspaces.</p>';
                    return;
                }

                milestones.forEach(ms => {
                    const col = document.createElement('div');
                    col.className = 'col';
                    const dueDate = ms.due_on ? new Date(ms.due_on).toLocaleDateString() : 'No due date';
                    const percent = Math.round(ms.progress);

                    const borderClass = ms.is_overdue ? 'border-danger' : 'border-light';
                    const badgeClass = ms.is_overdue ? 'bg-danger' : 'bg-info text-dark';

                    col.innerHTML = `
                        <div class="card h-100 shadow-sm ${borderClass} portfolio-milestone-card"
                             style="cursor: pointer;"
                             data-repo-name="${escapeHTML(ms.repo_name)}"
                             data-full-name="${escapeHTML(ms.full_name)}">
                            <div class="card-body p-3">
                                <div class="d-flex justify-content-between align-items-start mb-2">
                                    <h6 class="card-title mb-0 text-truncate" title="${escapeHTML(ms.title)}">${escapeHTML(ms.title)}</h6>
                                    <span class="badge ${badgeClass} small">${escapeHTML(ms.repo_name)}</span>
                                </div>
                                <div class="small ${ms.is_overdue ? 'text-danger fw-bold' : 'text-muted'} mb-2">
                                    <i class="bi bi-calendar"></i> Due: ${escapeHTML(dueDate)}
                                    ${ms.is_overdue ? ' <span class="badge bg-danger">OVERDUE</span>' : ''}
                                </div>
                                <div class="progress mb-1" style="height: 6px;">
                                    <div class="progress-bar bg-success" role="progressbar" style="width: ${percent}%;" aria-valuenow="${percent}" aria-valuemin="0" aria-valuemax="100"></div>
                                </div>
                                <div class="d-flex justify-content-between small text-muted">
                                    <span>${percent}%</span>
                                    <span>${ms.open_issues} open</span>
                                </div>
                            </div>
                        </div>
                    `;

                    col.querySelector('.portfolio-milestone-card').addEventListener('click', async () => {
                        const repoName = ms.repo_name;
                        try {
                            const activateResp = await fetch('/api/workspace/activate', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({repo_name: repoName})
                            });
                            if (activateResp.ok) {
                                showAlert(`Switched to workspace: ${repoName}`);
                                // Switch to workspace tab
                                const workspaceTab = document.getElementById('workspace-tab');
                                bootstrap.Tab.getOrCreateInstance(workspaceTab).show();
                                refreshExplorer();
                            } else {
                                const err = await activateResp.json();
                                showAlert(err.error || 'Failed to activate workspace', 'danger');
                            }
                        } catch (e) {
                            showAlert(e.message, 'danger');
                        }
                    });

                    container.appendChild(col);
                });
            } else {
                container.innerHTML = `<p class="text-danger p-2 mb-0">Error: ${escapeHTML(milestones.error)}</p>`;
            }
        } catch (error) {
            container.innerHTML = `<p class="text-danger p-2 mb-0">Error: ${escapeHTML(error.message)}</p>`;
        }
    };

    const refreshRoadmapBtn = document.getElementById('refreshRoadmapBtn');
    if (refreshRoadmapBtn) {
        refreshRoadmapBtn.addEventListener('click', () => {
            toggleLoading(refreshRoadmapBtn, true);
            refreshPortfolioRoadmap().finally(() => toggleLoading(refreshRoadmapBtn, false));
        });
    }

    const taskMilestoneFilter = document.getElementById('taskMilestoneFilter');
    if (taskMilestoneFilter) {
        taskMilestoneFilter.addEventListener('change', () => {
            refreshTaskInbox();
        });
    }

    const securityOnlyToggle = document.getElementById('securityOnlyToggle');
    if (securityOnlyToggle) {
        securityOnlyToggle.addEventListener('change', () => {
            refreshTaskInbox();
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
                                <button class="btn btn-sm btn-outline-secondary assign-issue-milestone-btn" data-number="${escapeHTML(String(issue.number))}" aria-label="Assign milestone to issue #${escapeHTML(String(issue.number))}">Assign</button>
                                ${issue.state === 'open' ? `<button class="btn btn-sm btn-outline-primary fix-issue-btn" data-number="${escapeHTML(String(issue.number))}" aria-label="Fix issue #${escapeHTML(String(issue.number))}">Fix</button>` : ''}
                                ${triageBtn}
                            </div>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });

                document.querySelectorAll('.assign-issue-milestone-btn').forEach(btn => {
                    btn.addEventListener('click', () => {
                        openAssignMilestone(repoFull, btn.getAttribute('data-number'));
                    });
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
                const [prResponse, policyResponse] = await Promise.all([
                    fetch(`/api/repos/${repoFull}/prs?state=${state}`),
                    fetch(`/api/repos/${repoFull}/governance/policy`)
                ]);
                const prs = await prResponse.json();
                const policy = await policyResponse.json();

                if (!prResponse.ok) {
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
                                <button class="btn btn-sm btn-outline-secondary assign-pr-milestone-btn" data-number="${escapeHTML(String(pr.number))}" aria-label="Assign milestone to PR #${escapeHTML(String(pr.number))}">Assign</button>
                                ${pr.state === 'open' ? `<button class="btn btn-sm ${policy.compliant ? 'btn-success' : 'btn-outline-danger'} merge-btn" data-number="${escapeHTML(String(pr.number))}" aria-label="Merge pull request #${escapeHTML(String(pr.number))}" ${policy.compliant ? '' : 'title="Policy Violation: ' + escapeHTML(policy.violations.map(v => v.message).join(', ')) + '"'}>${policy.compliant ? 'Merge' : '⚠ Blocked'}</button>` : ''}
                                ${pr.state === 'open' ? `<button class="btn btn-sm btn-primary review-btn" data-number="${escapeHTML(String(pr.number))}" aria-label="Review pull request #${escapeHTML(String(pr.number))}">Review</button>` : ''}
                                ${triageBtn}
                            </div>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
                document.querySelectorAll('.assign-pr-milestone-btn').forEach(btn => {
                    btn.addEventListener('click', () => {
                        openAssignMilestone(repoFull, btn.getAttribute('data-number'));
                    });
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
                            <div class="d-flex align-items-center gap-2">
                                <button class="btn btn-sm btn-outline-info manage-assets-btn" data-id="${r.id}" data-name="${escapeHTML(r.name || r.tag_name)}" data-repo="${escapeHTML(repoFull)}">Assets (${r.assets_count})</button>
                                <small class="text-muted font-monospace">${escapeHTML(r.tag_name)}</small>
                            </div>
                        </div>
                        <p class="mb-1 small text-truncate" style="max-width: 90%;">${escapeHTML(r.body || 'No description provided.')}</p>
                        <small class="text-muted">${r.published_at ? new Date(r.published_at).toLocaleString() : 'Not published yet'}</small>
                    `;
                    list.appendChild(div);
                });

                list.querySelectorAll('.manage-assets-btn').forEach(btn => {
                    btn.addEventListener('click', () => {
                        openReleaseAssets(btn.dataset.repo, btn.dataset.id, btn.dataset.name);
                    });
                });
            } catch (error) {
                showAlert(error.message, 'danger');
            } finally {
                toggleLoading(listBtn, false);
            }
        });
    }

    const openReleaseAssets = async (repoFull, releaseId, releaseName) => {
        const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('releaseAssetsModal'));
        document.getElementById('assetModalReleaseName').textContent = releaseName;
        document.getElementById('assetModalRepoName').textContent = repoFull;
        document.getElementById('assetReleaseId').value = releaseId;

        refreshReleaseAssets(repoFull, releaseId);
        modal.show();
    };

    const refreshReleaseAssets = async (repoFull, releaseId) => {
        const listEl = document.getElementById('releaseAssetsList');
        listEl.innerHTML = '<div class="text-center p-3"><span class="spinner-border spinner-border-sm" role="status"></span></div>';

        try {
            const response = await fetch(`/api/repos/${repoFull}/releases/${releaseId}/assets`);
            const assets = await response.json();

            if (response.ok) {
                listEl.innerHTML = '';
                if (assets.length === 0) {
                    listEl.innerHTML = '<p class="text-muted p-2 mb-0">No assets attached to this release.</p>';
                } else {
                    assets.forEach(asset => {
                        const item = document.createElement('div');
                        item.className = 'list-group-item d-flex justify-content-between align-items-center';
                        const sizeKb = Math.round(asset.size / 1024);
                        item.innerHTML = `
                            <div class="text-truncate me-2">
                                <div class="fw-bold small">${escapeHTML(asset.name)} ${asset.label ? `<span class="text-muted">(${escapeHTML(asset.label)})</span>` : ''}</div>
                                <small class="text-muted">${sizeKb} KB | ${asset.download_count} downloads | Created ${timeAgo(asset.created_at)}</small>
                            </div>
                            <div class="d-flex gap-1">
                                <a href="${escapeHTML(asset.browser_download_url)}" target="_blank" class="btn btn-sm btn-outline-secondary">Download</a>
                                <button class="btn btn-sm btn-outline-danger delete-asset-btn" data-id="${asset.id}">Delete</button>
                            </div>
                        `;
                        listEl.appendChild(item);
                    });

                    listEl.querySelectorAll('.delete-asset-btn').forEach(btn => {
                        btn.addEventListener('click', async () => {
                            if (!confirm('Are you sure you want to delete this asset?')) return;
                            toggleLoading(btn, true);
                            try {
                                const resp = await fetch(`/api/repos/${repoFull}/releases/assets/${btn.dataset.id}`, {
                                    method: 'DELETE'
                                });
                                const res = await resp.json();
                                if (resp.ok) {
                                    showAlert(res.message);
                                    refreshReleaseAssets(repoFull, releaseId);
                                } else {
                                    showAlert(res.error, 'danger');
                                }
                            } catch (err) {
                                showAlert(err.message, 'danger');
                            } finally {
                                toggleLoading(btn, false);
                            }
                        });
                    });
                }
            } else {
                listEl.innerHTML = `<p class="text-danger p-2 mb-0">Error: ${escapeHTML(assets.error)}</p>`;
            }
        } catch (error) {
            listEl.innerHTML = `<p class="text-danger p-2 mb-0">Error: ${escapeHTML(error.message)}</p>`;
        }
    };

    const uploadAssetForm = document.getElementById('uploadAssetForm');
    if (uploadAssetForm) {
        uploadAssetForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = document.getElementById('confirmUploadAssetBtn');
            const repoFull = document.getElementById('assetModalRepoName').textContent;
            const releaseId = document.getElementById('assetReleaseId').value;

            toggleLoading(submitBtn, true);
            const formData = new URLSearchParams(new FormData(uploadAssetForm));
            try {
                const response = await fetch(`/api/repos/${repoFull}/releases/${releaseId}/assets`, {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                if (response.ok) {
                    showAlert(result.message);
                    uploadAssetForm.reset();
                    refreshReleaseAssets(repoFull, releaseId);
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

    const pickWorkspaceAssetBtn = document.getElementById('pickWorkspaceAssetBtn');
    if (pickWorkspaceAssetBtn) {
        pickWorkspaceAssetBtn.addEventListener('click', () => {
            // Switch to Workspace tab and alert user
            const workspaceTab = document.getElementById('workspace-tab');
            bootstrap.Tab.getOrCreateInstance(workspaceTab).show();
            showAlert('Pick a file from the explorer and copy its path back to the release asset form.', 'info');
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

    // Global keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Global '/' to focus search based on context
        if (e.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
            const activeTabEl = document.querySelector('#mainTabs .nav-link.active');
            if (!activeTabEl) return;

            const activeTab = activeTabEl.id;
            let searchInput = null;

            if (activeTab === 'dashboard-tab') {
                searchInput = document.getElementById('dashboardRepoSearch');
            } else if (activeTab === 'workspace-tab') {
                searchInput = document.getElementById('workspaceOmniSearch');
            } else if (activeTab === 'actions-tab') {
                searchInput = document.getElementById('runSearch');
            }

            if (searchInput) {
                e.preventDefault();
                searchInput.focus();
            }
        }
    });

    // Modal focus management
    const modalFocusMap = {
        'fileModal': '#fileContentEditor',
        'searchModal': '#searchResultsList .list-group-item:first-child',
        'dispatchModal': '#dispatchRef',
        'publishTemplateModal': '#publishRepoName',
        'templateParamsModal': '#dynamicParamsContainer input:first-child',
        'historyModal': '#historyList .list-group-item:first-child',
        'conversationModal': '#commentBody',
        'diffModal': '#copyDiffBtn'
    };

    Object.keys(modalFocusMap).forEach(modalId => {
        const modalEl = document.getElementById(modalId);
        if (modalEl) {
            modalEl.addEventListener('shown.bs.modal', () => {
                const target = modalEl.querySelector(modalFocusMap[modalId]);
                if (target) target.focus();
            });
        }
    });

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

    const refreshEnvironments = async (repoFull) => {
        const cardContainer = document.getElementById('environmentsCards');
        const depList = document.getElementById('deploymentsList');
        if (!cardContainer || !depList) return;

        cardContainer.innerHTML = '<div class="col-12 text-center p-4"><span class="spinner-border" role="status"></span></div>';
        depList.innerHTML = '<div class="text-center p-3"><span class="spinner-border spinner-border-sm" role="status"></span></div>';

        try {
            const envResponse = await fetch(`/api/repos/${repoFull}/environments`);
            const envs = await envResponse.json();

            if (envResponse.ok) {
                cardContainer.innerHTML = '';
                const datalist = document.getElementById('environmentsDatalist');
                if (datalist) datalist.innerHTML = '';

                if (envs.length === 0) {
                    cardContainer.innerHTML = '<div class="col-12 w-100"><p class="text-muted p-4 text-center border rounded bg-light">No environments defined for this repository.</p></div>';
                } else {
                    envs.forEach(env => {
                        const col = document.createElement('div');
                        col.className = 'col';

                        const ld = env.latest_deployment;
                        const status = ld ? ld.latest_status : null;
                        const state = status ? status.state : 'unknown';
                        const statusClass = state === 'success' ? 'bg-success' : (state === 'failure' ? 'bg-danger' : 'bg-secondary');

                        col.innerHTML = `
                            <div class="card h-100 border-0 shadow-sm env-card" data-env="${escapeHTML(env.name)}">
                                <div class="card-header d-flex justify-content-between align-items-center py-2">
                                    <h6 class="mb-0 fw-bold">${escapeHTML(env.name)}</h6>
                                    <span class="badge ${statusClass}">${escapeHTML(state.toUpperCase())}</span>
                                </div>
                                <div class="card-body py-3">
                                    ${ld ? `
                                        <div class="mb-2">
                                            <div class="small text-muted mb-1">Current Version</div>
                                            <div class="d-flex align-items-center gap-2">
                                                <span class="badge bg-light text-dark border">${escapeHTML(ld.ref)}</span>
                                                <code class="small">${escapeHTML(ld.sha.substring(0, 7))}</code>
                                            </div>
                                        </div>
                                        <div class="small text-muted text-truncate" title="${escapeHTML(status ? status.description : '')}">
                                            ${escapeHTML(status ? status.description : 'No description')}
                                        </div>
                                    ` : `
                                        <p class="text-muted small mb-0">No deployments found</p>
                                    `}
                                </div>
                                <div class="card-footer bg-transparent border-top-0 d-flex justify-content-between align-items-center py-2">
                                    <small class="text-muted" style="font-size: 0.7rem;">${ld ? timeAgo(ld.created_at) : 'Never'}</small>
                                    <div class="btn-group btn-group-sm">
                                        <button class="btn btn-outline-primary deploy-to-env-btn" data-env="${escapeHTML(env.name)}">Deploy</button>
                                        <button class="btn btn-outline-secondary view-env-history-btn" data-env="${escapeHTML(env.name)}">History</button>
                                    </div>
                                </div>
                            </div>
                        `;
                        cardContainer.appendChild(col);

                        if (datalist) {
                            const opt = document.createElement('option');
                            opt.value = env.name;
                            datalist.appendChild(opt);
                        }
                    });

                    cardContainer.querySelectorAll('.view-env-history-btn').forEach(btn => {
                        btn.addEventListener('click', () => {
                            const envName = btn.dataset.env;
                            document.getElementById('historyEnvFilter').textContent = `Showing environment: ${envName}`;
                            refreshDeployments(repoFull, envName);
                        });
                    });

                    cardContainer.querySelectorAll('.deploy-to-env-btn').forEach(btn => {
                        btn.addEventListener('click', () => {
                            document.getElementById('deployEnv').value = btn.dataset.env;
                            document.getElementById('newDeploymentBtn').click();
                        });
                    });
                }
            } else {
                cardContainer.innerHTML = `<div class="col-12"><p class="text-danger p-3 small">${escapeHTML(envs.error)}</p></div>`;
            }

            await refreshDeployments(repoFull);

        } catch (error) {
            showAlert(error.message, 'danger');
        }
    };

    const refreshDeployments = async (repoFull, environment = '') => {
        const depList = document.getElementById('deploymentsList');
        const url = environment ? `/api/repos/${repoFull}/deployments?environment=${encodeURIComponent(environment)}` : `/api/repos/${repoFull}/deployments`;

        try {
            const response = await fetch(url);
            const deployments = await response.json();

            if (response.ok) {
                depList.innerHTML = '';
                if (deployments.length === 0) {
                    depList.innerHTML = '<p class="text-muted p-3 text-center">No deployments found.</p>';
                } else {
                    deployments.forEach(d => {
                        const item = document.createElement('div');
                        item.className = 'list-group-item';
                        const status = d.latest_status;
                        const statusBadge = status ?
                            `<span class="badge ${status.state === 'success' ? 'bg-success' : (status.state === 'failure' ? 'bg-danger' : 'bg-secondary')} ms-2">${escapeHTML(status.state.toUpperCase())}</span>` :
                            '<span class="badge bg-light text-dark border ms-2">PENDING</span>';

                        item.innerHTML = `
                            <div class="d-flex justify-content-between align-items-start">
                                <div class="text-truncate deployment-info">
                                    <h6 class="mb-1 small">
                                        <strong>${escapeHTML(d.environment)}</strong>
                                        ${statusBadge}
                                    </h6>
                                    <div class="small text-muted mb-1">
                                        <span class="badge bg-light text-dark border me-1">${escapeHTML(d.ref)}</span>
                                        <code>${escapeHTML(d.sha.substring(0, 7))}</code>
                                    </div>
                                    <p class="mb-0 small text-truncate" title="${escapeHTML(d.description || '')}">${escapeHTML(d.description || 'No description')}</p>
                                </div>
                                <div class="text-end">
                                    <div class="btn-group btn-group-sm mb-1">
                                        <button class="btn btn-outline-primary promote-dep-btn"
                                                data-sha="${escapeHTML(d.sha)}"
                                                data-ref="${escapeHTML(d.ref)}"
                                                data-env="${escapeHTML(d.environment)}"
                                                title="Promote to another environment">Promote</button>
                                        <button class="btn btn-outline-secondary redeploy-dep-btn"
                                                data-sha="${escapeHTML(d.sha)}"
                                                data-ref="${escapeHTML(d.ref)}"
                                                data-env="${escapeHTML(d.environment)}"
                                                title="Redeploy to this environment">Redeploy</button>
                                    </div>
                                    <small class="text-muted d-block" style="font-size: 0.7rem;">${timeAgo(d.created_at)}</small>
                                    <small class="text-muted" style="font-size: 0.7rem;">by ${escapeHTML(d.creator)}</small>
                                </div>
                            </div>
                        `;
                        depList.appendChild(item);
                    });

                    depList.querySelectorAll('.promote-dep-btn').forEach(btn => {
                        btn.addEventListener('click', () => {
                            const sha = btn.dataset.sha;
                            const ref = btn.dataset.ref;
                            const env = btn.dataset.env;

                            document.getElementById('deployRef').value = sha;
                            document.getElementById('deployDescription').value = `Promoted from ${env} (${ref})`;

                            const indicator = document.getElementById('promotionIndicator');
                            if (indicator) {
                                indicator.innerHTML = `<div class="alert alert-info py-1 small mb-3">🚀 Promoting deployment <strong>${escapeHTML(ref)}</strong> from <strong>${escapeHTML(env)}</strong></div>`;
                                indicator.style.display = 'block';
                            }

                            const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('deploymentModal'));
                            modal.show();
                        });
                    });

                    depList.querySelectorAll('.redeploy-dep-btn').forEach(btn => {
                        btn.addEventListener('click', () => {
                            const sha = btn.dataset.sha;
                            const ref = btn.dataset.ref;
                            const env = btn.dataset.env;

                            document.getElementById('deployRef').value = sha;
                            document.getElementById('deployEnv').value = env;
                            document.getElementById('deployDescription').value = `Redeploying ${ref}`;

                            const indicator = document.getElementById('promotionIndicator');
                            if (indicator) {
                                indicator.innerHTML = `<div class="alert alert-secondary py-1 small mb-3">♻️ Redeploying <strong>${escapeHTML(ref)}</strong> to <strong>${escapeHTML(env)}</strong></div>`;
                                indicator.style.display = 'block';
                            }

                            const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('deploymentModal'));
                            modal.show();
                        });
                    });
                }
            } else {
                depList.innerHTML = `<p class="text-danger p-3 small">${escapeHTML(deployments.error)}</p>`;
            }
        } catch (error) {
            depList.innerHTML = `<p class="text-danger p-3 small">${escapeHTML(error.message)}</p>`;
        }
    };

    const listDeploymentsForm = document.getElementById('listDeploymentsForm');
    if (listDeploymentsForm) {
        listDeploymentsForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const repoFull = document.getElementById('deploymentsRepoFullName').value;
            if (repoFull) refreshEnvironments(repoFull);
        });
    }

    const newDeploymentBtn = document.getElementById('newDeploymentBtn');
    if (newDeploymentBtn) {
        newDeploymentBtn.addEventListener('click', () => {
            // Clear promotion indicator when creating a fresh deployment
            const indicator = document.getElementById('promotionIndicator');
            if (indicator) {
                indicator.innerHTML = '';
                indicator.style.display = 'none';
            }
            const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('deploymentModal'));
            modal.show();
        });
    }

    const confirmDeploymentBtn = document.getElementById('confirmDeploymentBtn');
    if (confirmDeploymentBtn) {
        confirmDeploymentBtn.addEventListener('click', async () => {
            const repoFull = document.getElementById('deploymentsRepoFullName').value;
            const ref = document.getElementById('deployRef').value;
            const environment = document.getElementById('deployEnv').value;
            const description = document.getElementById('deployDescription').value;
            const auto_merge = document.getElementById('deployAutoMerge').checked;

            if (!repoFull || !ref || !environment) return showAlert('Repo, Ref and Environment are required', 'warning');

            toggleLoading(confirmDeploymentBtn, true);
            try {
                const response = await fetch(`/api/repos/${repoFull}/deployments`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ref, environment, description, auto_merge })
                });
                const result = await response.json();
                if (response.ok) {
                    showAlert(result.message);
                    bootstrap.Modal.getInstance(document.getElementById('deploymentModal')).hide();
                    setTimeout(() => refreshDeployments(repoFull, environment), 2000);
                } else {
                    showAlert(result.error, 'danger');
                }
            } catch (error) {
                showAlert(error.message, 'danger');
            } finally {
                toggleLoading(confirmDeploymentBtn, false);
            }
        });
    }

    const refreshMilestones = async (repoFull) => {
        const container = document.getElementById('milestonesContainer');
        const filter = document.getElementById('taskMilestoneFilter');
        if (!container) return;

        container.innerHTML = '<div class="col-12 text-center p-4"><span class="spinner-border" role="status"></span></div>';

        try {
            const response = await fetch(`/api/repos/${repoFull}/milestones`);
            const milestones = await response.json();

            if (response.ok) {
                container.innerHTML = '';
                if (filter) {
                    // Update task inbox milestone filter
                    const currentVal = filter.value;
                    filter.innerHTML = '<option value="">All Milestones</option>';
                    milestones.forEach(ms => {
                        const opt = document.createElement('option');
                        opt.value = ms.title;
                        opt.textContent = ms.title;
                        filter.appendChild(opt);
                    });
                    filter.value = currentVal;
                }

                if (milestones.length === 0) {
                    container.innerHTML = '<div class="col-12 w-100"><p class="text-muted p-4 text-center border rounded bg-light">No milestones found for this repository.</p></div>';
                } else {
                    milestones.forEach(ms => {
                        const total = ms.open_issues + ms.closed_issues;
                        const percent = total > 0 ? Math.round((ms.closed_issues / total) * 100) : 0;
                        const dueDate = ms.due_on ? new Date(ms.due_on).toLocaleDateString() : 'No due date';

                        const col = document.createElement('div');
                        col.className = 'col';
                        col.innerHTML = `
                            <div class="card h-100 shadow-sm border-0">
                                <div class="card-header bg-transparent border-0 d-flex justify-content-between align-items-start pt-3 pb-0">
                                    <div>
                                        <h5 class="card-title mb-1"><a href="${escapeHTML(ms.html_url)}" target="_blank" rel="noopener noreferrer" class="text-decoration-none">${escapeHTML(ms.title)}</a></h5>
                                        <small class="text-muted"><i class="bi bi-calendar"></i> ${escapeHTML(dueDate)}</small>
                                    </div>
                                    <span class="badge ${ms.state === 'open' ? 'bg-success' : 'bg-secondary'}">${escapeHTML(ms.state.toUpperCase())}</span>
                                </div>
                                <div class="card-body">
                                    <p class="card-text small text-muted mb-3" style="min-height: 3em;">${escapeHTML(ms.description || 'No description provided.')}</p>
                                    <div class="d-flex justify-content-between small mb-1">
                                        <span>${percent}% complete</span>
                                        <span>${ms.open_issues} open, ${ms.closed_issues} closed</span>
                                    </div>
                                    <div class="progress" style="height: 10px;">
                                        <div class="progress-bar bg-success" role="progressbar" style="width: ${percent}%;" aria-valuenow="${percent}" aria-valuemin="0" aria-valuemax="100"></div>
                                    </div>
                                </div>
                                <div class="card-footer bg-transparent border-0 pt-0 pb-3">
                                    <div class="d-grid">
                                        <button class="btn btn-sm btn-outline-primary assign-to-milestone-btn" data-number="${ms.number}" data-title="${escapeHTML(ms.title)}">Focus Milestone</button>
                                    </div>
                                </div>
                            </div>
                        `;
                        container.appendChild(col);
                    });

                    container.querySelectorAll('.assign-to-milestone-btn').forEach(btn => {
                        btn.addEventListener('click', () => {
                            if (filter) {
                                filter.value = btn.dataset.title;
                                filter.dispatchEvent(new Event('change'));
                                bootstrap.Tab.getOrCreateInstance(document.getElementById('dashboard-tab')).show();
                            }
                        });
                    });
                }
            } else {
                container.innerHTML = `<div class="col-12"><p class="text-danger p-3 small">${escapeHTML(milestones.error)}</p></div>`;
            }
        } catch (error) {
            container.innerHTML = `<div class="col-12"><p class="text-danger p-3 small">${escapeHTML(error.message)}</p></div>`;
        }
    };

    const listMilestonesForm = document.getElementById('listMilestonesForm');
    if (listMilestonesForm) {
        listMilestonesForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const repoFull = document.getElementById('milestonesRepoFullName').value;
            if (repoFull) refreshMilestones(repoFull);
        });
    }

    const newMilestoneBtn = document.getElementById('newMilestoneBtn');
    if (newMilestoneBtn) {
        newMilestoneBtn.addEventListener('click', () => {
            const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('milestoneModal'));
            modal.show();
        });
    }

    const confirmMilestoneBtn = document.getElementById('confirmMilestoneBtn');
    if (confirmMilestoneBtn) {
        confirmMilestoneBtn.addEventListener('click', async () => {
            const repoFull = document.getElementById('milestonesRepoFullName').value;
            const title = document.getElementById('milestoneTitle').value;
            const description = document.getElementById('milestoneDescription').value;
            const due_on = document.getElementById('milestoneDueOn').value;

            if (!repoFull || !title) return showAlert('Repo and Title are required', 'warning');

            toggleLoading(confirmMilestoneBtn, true);
            try {
                const response = await fetch(`/api/repos/${repoFull}/milestones`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title, description, due_on: due_on ? new Date(due_on).toISOString() : null })
                });
                const result = await response.json();
                if (response.ok) {
                    showAlert(result.message);
                    bootstrap.Modal.getInstance(document.getElementById('milestoneModal')).hide();
                    refreshMilestones(repoFull);
                } else {
                    showAlert(result.error, 'danger');
                }
            } catch (error) {
                showAlert(error.message, 'danger');
            } finally {
                toggleLoading(confirmMilestoneBtn, false);
            }
        });
    }

    const openAssignMilestone = async (repoFull, number) => {
        document.getElementById('assignMilestoneRepo').value = repoFull;
        document.getElementById('assignMilestoneNumber').value = number;
        const select = document.getElementById('milestoneSelect');
        select.innerHTML = '<option value="">No Milestone (Clear)</option><option disabled>Loading...</option>';

        const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('assignMilestoneModal'));
        modal.show();

        try {
            const response = await fetch(`/api/repos/${repoFull}/milestones`);
            const milestones = await response.json();
            if (response.ok) {
                select.innerHTML = '<option value="">No Milestone (Clear)</option>';
                milestones.forEach(ms => {
                    const opt = document.createElement('option');
                    opt.value = ms.number;
                    opt.textContent = ms.title;
                    select.appendChild(opt);
                });
            } else {
                select.innerHTML = '<option value="">No Milestone (Clear)</option><option disabled>Error loading milestones</option>';
            }
        } catch (error) {
            select.innerHTML = '<option value="">No Milestone (Clear)</option><option disabled>Error loading milestones</option>';
        }
    };

    const openSecurityExplorer = async (repoFullName) => {
        const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('securityAlertsModal'));
        const nameEl = document.getElementById('securityAlertsRepoName');
        const summaryEl = document.getElementById('securityAlertsSummary');
        const listEl = document.getElementById('securityAlertsList');

        nameEl.textContent = repoFullName;
        summaryEl.innerHTML = '';
        listEl.innerHTML = `
            <div class="text-center p-4">
                <span class="spinner-border text-danger" role="status"></span>
                <p class="mt-2 text-muted">Fetching detailed alerts for ${escapeHTML(repoFullName)}...</p>
            </div>
        `;

        modal.show();

        try {
            const response = await fetch(`/api/repos/${repoFullName}/security/alerts`);
            const data = await response.json();

            if (response.ok) {
                const s = data.summary;
                summaryEl.innerHTML = `
                    <span class="badge bg-danger">${s.vulnerabilities.critical} Critical</span>
                    <span class="badge bg-warning text-dark">${s.vulnerabilities.high} High</span>
                    <span class="badge bg-dark">${s.secrets.open} Secrets</span>
                    <span class="badge bg-secondary">${s.code_scanning.errors} Code Errors</span>
                `;

                listEl.innerHTML = '';
                if (data.alerts.length === 0) {
                    listEl.innerHTML = '<div class="p-4 text-center text-muted">No active security alerts found.</div>';
                } else {
                    data.alerts.forEach(alert => {
                        const item = document.createElement('div');
                        item.className = 'list-group-item';

                        let icon = '🛡️';
                        let badgeClass = 'bg-secondary';
                        let detail = '';

                        if (alert.type === 'dependabot') {
                            icon = '📦';
                            badgeClass = alert.severity === 'critical' ? 'bg-danger' : (alert.severity === 'high' ? 'bg-warning text-dark' : 'bg-info text-dark');
                            detail = `Vulnerability in <strong>${escapeHTML(alert.package)}</strong>${alert.fixed_in ? `. Fixed in <strong>${escapeHTML(alert.fixed_in)}</strong>` : ''}`;
                        } else if (alert.type === 'secret') {
                            icon = '🔑';
                            badgeClass = 'bg-danger';
                            detail = `Exposed secret detected: <strong>${escapeHTML(alert.secret_type)}</strong>`;
                        } else if (alert.type === 'code_scanning') {
                            icon = '🔍';
                            badgeClass = alert.severity === 'error' ? 'bg-danger' : 'bg-warning text-dark';
                            detail = `Code Scanning issue: <strong>${escapeHTML(alert.rule)}</strong>`;
                        }

                        item.innerHTML = `
                            <div class="d-flex justify-content-between align-items-start">
                                <div class="d-flex gap-2">
                                    <span class="fs-5">${icon}</span>
                                    <div>
                                        <div class="mb-1">
                                            <span class="badge ${badgeClass} small">${escapeHTML((alert.severity || alert.type).toUpperCase())}</span>
                                            <span class="text-muted small ms-1">${escapeHTML(alert.type)}</span>
                                        </div>
                                        <div class="small">${detail}</div>
                                    </div>
                                </div>
                                <div class="d-flex gap-1">
                                    <a href="${escapeHTML(alert.html_url)}" target="_blank" class="btn btn-sm btn-outline-secondary">View on GitHub</a>
                                    ${alert.type === 'dependabot' ? `<button class="btn btn-sm btn-outline-success patch-security-btn" data-repo="${escapeHTML(repoFullName)}" data-number="${alert.number}" data-package="${escapeHTML(alert.package)}">Patch</button>` : ''}
                                </div>
                            </div>
                        `;
                        listEl.appendChild(item);
                    });

                    listEl.querySelectorAll('.patch-security-btn').forEach(btn => {
                        btn.addEventListener('click', async () => {
                            toggleLoading(btn, true);
                            try {
                                const response = await fetch('/api/workspace/setup-security-fix', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                        repo_full_name: btn.dataset.repo,
                                        alert_number: btn.dataset.number
                                    })
                                });
                                const result = await response.json();
                                if (response.ok) {
                                    modal.hide();
                                    showAlert(result.message);
                                    bootstrap.Tab.getOrCreateInstance(document.getElementById('workspace-tab')).show();
                                    refreshExplorer();
                                } else {
                                    showAlert(result.error, 'danger');
                                }
                            } catch (err) {
                                showAlert(err.message, 'danger');
                            } finally {
                                toggleLoading(btn, false);
                            }
                        });
                    });
                }
            } else {
                listEl.innerHTML = `<div class="p-4 text-danger text-center">Error: ${escapeHTML(data.error)}</div>`;
            }
        } catch (error) {
            listEl.innerHTML = `<div class="p-4 text-danger text-center">Error: ${escapeHTML(error.message)}</div>`;
        }
    };

    const confirmAssignMilestoneBtn = document.getElementById('confirmAssignMilestoneBtn');
    if (confirmAssignMilestoneBtn) {
        confirmAssignMilestoneBtn.addEventListener('click', async () => {
            const repoFull = document.getElementById('assignMilestoneRepo').value;
            const number = document.getElementById('assignMilestoneNumber').value;
            const milestoneNumber = document.getElementById('milestoneSelect').value;

            toggleLoading(confirmAssignMilestoneBtn, true);
            try {
                const response = await fetch(`/api/repos/${repoFull}/issues/${number}/milestone`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ milestone_number: milestoneNumber ? parseInt(milestoneNumber) : null })
                });
                const result = await response.json();
                if (response.ok) {
                    showAlert(result.message);
                    bootstrap.Modal.getInstance(document.getElementById('assignMilestoneModal')).hide();
                    // Refresh active list
                    if (document.getElementById('issues-tab').classList.contains('active')) {
                        document.getElementById('listIssuesBtn').click();
                    } else if (document.getElementById('prs-tab').classList.contains('active')) {
                        document.getElementById('listPrsBtn').click();
                    }
                } else {
                    showAlert(result.error, 'danger');
                }
            } catch (error) {
                showAlert(error.message, 'danger');
            } finally {
                toggleLoading(confirmAssignMilestoneBtn, false);
            }
        });
    }
});
