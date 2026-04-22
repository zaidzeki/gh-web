# PRD: Dynamic Scaffolding Engine

## 1. Problem Statement
Current workspace templates are static clones of existing files. Complex projects require customization during creation (e.g., project name, port numbers, database credentials, license holders). Static templates force users into a "search and replace" manual phase after bootstrapping, which defeats the purpose of automation.

## 2. Objectives
- **Parameterization:** Transform templates into dynamic generators using Jinja2 or similar engines.
- **Interactive Scaffolding:** Prompt users for input values defined in a template manifest.
- **Structural Dynamism:** Allow placeholders in filenames and directory names (e.g., `src/{{project_name}}/main.py`).

## 3. User Stories
- **As a Developer,** I want to be prompted for my "Project Name" when applying a template so that all files are correctly initialized.
- **As a Developer,** I want to define default values for parameters in a `manifest.json` file so that I only provide what's necessary.
- **As a Developer,** I want a template to automatically create directories based on my input so that my project structure matches my naming conventions.

## 4. Functional Requirements
- **Manifest Support:** Templates can include a `manifest.json` defining variables (name, description, default, type).
- **Transformation Layer:** Backend renders all template files through Jinja2 before copying them to the workspace.
- **Path Rendering:** Placeholders in file and directory paths are resolved using the provided context.
- **Frontend Integration:** Dynamic form generation based on the `manifest.json` when a template is selected.

## 5. Acceptance Criteria
- [ ] Backend identifies `manifest.json` in a template and parses its variables.
- [ ] Backend renders file content with Jinja2 using a dictionary of user-provided values.
- [ ] Backend renames files/folders if their paths contain `{{variable}}` syntax.
- [ ] Frontend displays a dynamic form for parameters when "Apply Template" or "Create Repo" is selected.
- [ ] Standard static templates still work without a `manifest.json`.

## 6. Technical Implementation
- **Rendering:** Use `jinja2.Template` to process strings.
- **Recursion:** The transformation happens during the recursive walk of the template directory.
- **Manifest Schema:**
  ```json
  {
    "variables": [
      {"name": "project_name", "label": "Project Name", "default": "my-app"},
      {"name": "author", "label": "Author", "default": "GH-Web User"}
    ]
  }
  ```
