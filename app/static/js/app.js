document.addEventListener('DOMContentLoaded', () => {
    const showAlert = (message, type = 'success') => {
        const container = document.getElementById('alertContainer');
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.setAttribute('role', type === 'danger' ? 'alert' : 'status');
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        container.appendChild(alert);
        setTimeout(() => alert.remove(), 5000);
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
            const submitBtn = form.querySelector('button[type="submit"]');
            toggleLoading(submitBtn, true);
            const formData = isMultipart ? new FormData(form) : new URLSearchParams(new FormData(form));
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
                } else {
                    showAlert(result.error || 'Operation failed', 'danger');
                }
            } catch (error) {
                showAlert(error.message, 'danger');
            } finally {
                toggleLoading(submitBtn, false);
            }
        });
    };

    // Expose handleForm for testing or dynamic forms
    window.handleForm = handleForm;

    handleForm('loginForm', '/login');
    handleForm('createRepoForm', '/api/repos');
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
                        <button class="btn btn-sm btn-outline-danger delete-template-btn" data-template="${t}">Delete</button>
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

    const applyTemplateBtn = document.getElementById('applyTemplateBtn');
    if (applyTemplateBtn) {
        applyTemplateBtn.addEventListener('click', async () => {
            const templateName = document.getElementById('workspaceTemplateSelect').value;
            if (!templateName) return showAlert('Please select a template', 'danger');

            toggleLoading(applyTemplateBtn, true);
            try {
                const response = await fetch('/api/workspace/apply-template', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ template_name: templateName })
                });
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
                toggleLoading(applyTemplateBtn, false);
            }
        });
    }

    const refreshStatus = async () => {
        const branchBadge = document.getElementById('branchBadge');
        const statusBadge = document.getElementById('statusBadge');
        if (!branchBadge || !statusBadge) return;

        try {
            const response = await fetch('/api/workspace/status');
            const data = await response.json();
            if (response.ok && data.is_git) {
                branchBadge.textContent = data.branch;
                branchBadge.style.display = 'inline-block';
                if (data.is_dirty || data.untracked) {
                    statusBadge.textContent = 'Modified';
                    statusBadge.className = 'badge bg-warning text-dark';
                } else {
                    statusBadge.textContent = 'Clean';
                    statusBadge.className = 'badge bg-success';
                }
                statusBadge.style.display = 'inline-block';
            } else {
                branchBadge.style.display = 'none';
                statusBadge.style.display = 'none';
            }
        } catch (error) {
            console.error('Failed to fetch workspace status:', error);
        }
    };

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
                              data-path="${node.path}"
                              data-type="${node.type}"
                              ${isFile ? `tabindex="0" role="button" aria-label="View file ${node.name}"` : ''}>
                            ${node.name}
                        </span>
                        <button class="btn btn-sm text-danger delete-file-btn ms-2"
                                data-path="${node.path}"
                                style="padding: 0 5px;"
                                aria-label="Delete ${node.name}"
                                title="Delete ${node.name}">&times;</button>
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
    handleForm('commitForm', '/api/workspace/commit', 'POST', false, refreshExplorer);
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
                                    <h6 class="mb-1 text-truncate">${commit.message}</h6>
                                    <small class="text-muted font-monospace">${commit.hash.substring(0, 7)}</small>
                                </div>
                                <p class="mb-1 small">By <strong>${commit.author}</strong></p>
                                <small class="text-muted">${new Date(commit.date).toLocaleString()}</small>
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

    const listPrsBtn = document.getElementById('listPrsBtn');
    if (listPrsBtn) {
        listPrsBtn.addEventListener('click', async () => {
            const repoFull = document.getElementById('repoFullName').value;
            if (!repoFull) return showAlert('Repo Full Name is required', 'danger');

            toggleLoading(listPrsBtn, true);
            try {
                const response = await fetch(`/api/repos/${repoFull}/prs`);
                const prs = await response.json();
                const tbody = document.querySelector('#prsTable tbody');
                tbody.innerHTML = '';
                prs.forEach(pr => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${pr.number}</td>
                        <td><a href="${pr.html_url}" target="_blank">${pr.title}</a></td>
                        <td>${pr.state}</td>
                        <td>
                            <button class="btn btn-sm btn-success merge-btn" data-number="${pr.number}">Merge</button>
                        </td>
                    `;
                    tbody.appendChild(tr);
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
            } catch (error) {
                showAlert(error.message, 'danger');
            } finally {
                toggleLoading(listPrsBtn, false);
            }
        });
    }
});
