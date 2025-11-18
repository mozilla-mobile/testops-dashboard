# Confluence Page Updater

This module updates Confluence pages based on structured configuration files in **YAML** and **XML** formats. Each format supports a different use case and is handled by a distinct parsing approach.

## Supported Config Formats

### Looker Graph Page (YAML) Configs

YAML is used for simple, uniform, and scalable page generation where Looker graphs are mirrored to Confluence tables in bulk.

- Each YAML file maps to one Confluence page with a standard table layout.
- Designed for high-volume updates with minimal effort.
- Currently, supports pages for the `MTE` and `DTE` team.
  - The team name can be specified by changing the `TEAM_ID` environment variable.
- To add new pages, simply drop additional files into the `config/confluence/yaml/` directory — no code changes required.
  - For pages own by `DTE`, use the `config/confluence/yaml/DTE/` directory.
- The YAML parser processes all files in this directory and writes one Confluence page per file. 

### Looker Folder Configuration

Each team's metrics are stored in separate Looker folders. The folder IDs are:

- **MTE**: 1820 (default)
- **DTE**: 1946

**Note:** To change the looker folder, you can set the environment variable `LOOKER_FOLDER_ID` to the desired folder id before running the script.


**Finding Looker Folder IDs:**
1. Navigate to the folder in Looker's web interface
2. Check the browser URL: `https://mozilla.cloud.looker.com/folders/{FOLDER_ID}`
3. Or refer to `config/looker/folder_ids.yaml` for all team folder IDs

### Custom Page (XML) Configs

XML is used for more complex, page-specific templates that require flexible layout control.

- Each file is a Jinja-based XML fragment, often copied from existing Confluence pages.
- Templates are re-parameterized with new data at runtime.
- Ideal for pages with rich formatting or non-standard layouts.
- The XML parser loads the template, applies parameters, and updates a specific Confluence page — prioritizing flexibility and fidelity to existing designs.

## Usage

Run from the project root using the appropriate flag for your update type:

### Bulk YAML page updates

```bash
python ./__main__.py --confluence-updates yaml
```


### Single XML page updates

```bash
python ./__main__.py --confluence-build-validation
```