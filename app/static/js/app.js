document.addEventListener('DOMContentLoaded', () => {
    const showAlert = (message, type = 'success') => {
        const container = document.getElementById('alertContainer');
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
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
    handleForm('commitForm', '/api/workspace/commit');
    const refreshTemplates = async () => {
        try {
            const response = await fetch('/api/workspace/templates');
            const templates = await response.json();
            const select = document.getElementById('templateSelect');
            if (select) {
                // Keep the first "None" option
                select.innerHTML = '<option value="">None (Empty Repository)</option>';
                templates.forEach(t => {
                    const opt = document.createElement('option');
                    opt.value = t;
                    opt.textContent = t;
                    select.appendChild(opt);
                });
            }
        } catch (error) {
            console.error('Failed to fetch templates:', error);
        }
    };

    refreshTemplates();
    handleForm('saveTemplateForm', '/api/workspace/save-template', 'POST', false, refreshTemplates);

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
