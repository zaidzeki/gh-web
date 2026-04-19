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

    const handleForm = (formId, endpoint, method = 'POST', isMultipart = false) => {
        const form = document.getElementById(formId);
        if (!form) return;
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
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
                } else {
                    showAlert(result.error || 'Operation failed', 'danger');
                }
            } catch (error) {
                showAlert(error.message, 'danger');
            }
        });
    };

    handleForm('loginForm', '/login');
    handleForm('createRepoForm', '/api/repos');
    handleForm('cloneForm', '/api/workspace/clone');
    handleForm('downloadForm', '/api/workspace/download');
    handleForm('uploadFileForm', '/api/workspace/modify/upload', 'POST', true);
    handleForm('uploadArchiveForm', '/api/workspace/modify/archive', 'POST', true);
    handleForm('applyPatchForm', '/api/workspace/modify/patch', 'POST', true);
    handleForm('commitForm', '/api/workspace/commit');

    const createPrForm = document.getElementById('createPrForm');
    if (createPrForm) {
        createPrForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const repoFull = document.getElementById('repoFullName').value;
            if (!repoFull) return showAlert('Repo Full Name is required', 'danger');
            const formData = new URLSearchParams(new FormData(createPrForm));
            const response = await fetch(`/api/repos/${repoFull}/prs`, {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            if (response.ok) showAlert(result.message);
            else showAlert(result.error, 'danger');
        });
    }

    const listPrsBtn = document.getElementById('listPrsBtn');
    if (listPrsBtn) {
        listPrsBtn.addEventListener('click', async () => {
            const repoFull = document.getElementById('repoFullName').value;
            if (!repoFull) return showAlert('Repo Full Name is required', 'danger');
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
                        const resp = await fetch(`/api/repos/${repoFull}/prs/${num}/merge`, {
                            method: 'POST',
                            body: new URLSearchParams({commit_message: 'Merged via GH-Web'})
                        });
                        const res = await resp.json();
                        if (resp.ok) showAlert(res.message);
                        else showAlert(res.error, 'danger');
                    });
                });
            } catch (error) {
                showAlert(error.message, 'danger');
            }
        });
    }
});
