# Letta - Deployment

**Pages:** 22

---

## Set current template from snapshot (Cloud-only)

**URL:** llms-txt#set-current-template-from-snapshot-(cloud-only)

**Contents:**
- OpenAPI Specification
- SDK Code Examples

PUT https://api.letta.com/v1/templates/{project_id}/{template_version}/snapshot
Content-Type: application/json

Updates the current working version of a template from a snapshot

Reference: https://docs.letta.com/api-reference/templates/setcurrenttemplatefromsnapshot

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: Set current template from snapshot (Cloud-only)
  version: endpoint_templates.setcurrenttemplatefromsnapshot
paths:
  /v1/templates/{project_id}/{template_version}/snapshot:
    put:
      operationId: setcurrenttemplatefromsnapshot
      summary: Set current template from snapshot (Cloud-only)
      description: Updates the current working version of a template from a snapshot
      tags:
        - - subpackage_templates
      parameters:
        - name: project_id
          in: path
          description: The project id
          required: true
          schema:
            type: string
        - name: template_version
          in: path
          description: The template name with :dev version (e.g., my-template:dev)
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: '200'
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/templates_setcurrenttemplatefromsnapshot_Response_200
        '400':
          description: '400'
          content: {}
        '404':
          description: '404'
          content: {}
        '500':
          description: '500'
          content: {}
      requestBody:
        description: Body
        content:
          application/json:
            schema:
              description: Any type
components:
  schemas:
    templates_setcurrenttemplatefromsnapshot_Response_200:
      type: object
      properties:
        success:
          type: boolean
        message:
          type: string
      required:
        - success
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.templates.setcurrenttemplatefromsnapshot(
    project_id="project_id",
    template_version="template_version",
    request={"key": "value"},
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.templates.setcurrenttemplatefromsnapshot("project_id", "template_version", {
    "key": "value"
});
```

Example 4 (go):
```go
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.letta.com/v1/templates/project_id/template_version/snapshot"

	payload := strings.NewReader("null")

	req, _ := http.NewRequest("PUT", url, payload)

	req.Header.Add("Authorization", "Bearer <token>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## Save template version (Cloud-only)

**URL:** llms-txt#save-template-version-(cloud-only)

**Contents:**
- OpenAPI Specification
- SDK Code Examples

POST https://api.letta.com/v1/templates/{project_id}/{template_name}
Content-Type: application/json

Saves the current version of the template as a new version

Reference: https://docs.letta.com/api-reference/templates/savetemplateversion

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: Save template version (Cloud-only)
  version: endpoint_templates.savetemplateversion
paths:
  /v1/templates/{project_id}/{template_name}:
    post:
      operationId: savetemplateversion
      summary: Save template version (Cloud-only)
      description: Saves the current version of the template as a new version
      tags:
        - - subpackage_templates
      parameters:
        - name: project_id
          in: path
          description: The project id
          required: true
          schema:
            type: string
        - name: template_name
          in: path
          description: >-
            The template version, formatted as {template-name}, any version
            appended will be ignored
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: '200'
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/templates_savetemplateversion_Response_200
        '400':
          description: '400'
          content: {}
      requestBody:
        description: Body
        content:
          application/json:
            schema:
              type: object
              properties:
                preserve_environment_variables_on_migration:
                  type: boolean
                preserve_core_memories_on_migration:
                  type: boolean
                migrate_agents:
                  type: boolean
                message:
                  type: string
components:
  schemas:
    templates_savetemplateversion_Response_200:
      type: object
      properties:
        name:
          type: string
        id:
          type: string
        project_id:
          type: string
        project_slug:
          type: string
        latest_version:
          type: string
        description:
          type: string
        template_deployment_slug:
          type: string
        updated_at:
          type: string
      required:
        - name
        - id
        - project_id
        - project_slug
        - latest_version
        - template_deployment_slug
        - updated_at
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.templates.savetemplateversion(
    project_id="project_id",
    template_name="template_name",
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.templates.savetemplateversion("project_id", "template_name");
```

Example 4 (go):
```go
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.letta.com/v1/templates/project_id/template_name"

	payload := strings.NewReader("{}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("Authorization", "Bearer <token>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## Rename template (Cloud-only)

**URL:** llms-txt#rename-template-(cloud-only)

**Contents:**
- OpenAPI Specification
- SDK Code Examples

PATCH https://api.letta.com/v1/templates/{project_id}/{template_name}/name
Content-Type: application/json

Renames all versions of a template with the specified name. Versions are automatically stripped from the current template name if accidentally included.

Reference: https://docs.letta.com/api-reference/templates/renametemplate

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: Rename template (Cloud-only)
  version: endpoint_templates.renametemplate
paths:
  /v1/templates/{project_id}/{template_name}/name:
    patch:
      operationId: renametemplate
      summary: Rename template (Cloud-only)
      description: >-
        Renames all versions of a template with the specified name. Versions are
        automatically stripped from the current template name if accidentally
        included.
      tags:
        - - subpackage_templates
      parameters:
        - name: project_id
          in: path
          description: The project id
          required: true
          schema:
            type: string
        - name: template_name
          in: path
          description: >-
            The current template name (version will be automatically stripped if
            included)
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: '200'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/templates_renametemplate_Response_200'
        '400':
          description: '400'
          content: {}
        '404':
          description: '404'
          content: {}
        '409':
          description: '409'
          content: {}
      requestBody:
        description: Body
        content:
          application/json:
            schema:
              type: object
              properties:
                new_name:
                  type: string
              required:
                - new_name
components:
  schemas:
    templates_renametemplate_Response_200:
      type: object
      properties:
        success:
          type: boolean
      required:
        - success
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.templates.renametemplate(
    project_id="project_id",
    template_name="template_name",
    new_name="new_name",
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.templates.renametemplate("project_id", "template_name", {
    newName: "new_name"
});
```

Example 4 (go):
```go
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.letta.com/v1/templates/project_id/template_name/name"

	payload := strings.NewReader("{\n  \"new_name\": \"string\"\n}")

	req, _ := http.NewRequest("PATCH", url, payload)

	req.Header.Add("Authorization", "Bearer <token>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## Initial Setup and Connection

**URL:** llms-txt#initial-setup-and-connection

**Contents:**
- Web ADE
- Letta Desktop
- Next Steps

> Get started with the Agent Development Environment

The Agent Development Environment (ADE) is your gateway to building, testing, and monitoring stateful agents. This guide will help you access the ADE and connect it to your Letta server, whether it's running locally or deployed remotely.

Letta offers two ways to access the Agent Development Environment: via the browser (the **web ADE**), and **Letta Desktop**.

<Note>
  Letta Cloud is currently in [early access](https://forms.letta.com/early-access), but you do **not** need Letta Cloud access to use the web ADE to connect to self-hosted Letta servers.
</Note>

The browser-based (web) ADE is available at [https://app.letta.com](https://app.letta.com). You can use the web ADE to connect to both Letta Cloud, and agents running on your own self-hosted Letta deployments (both on `localhost`, and remotely).

To use the web ADE to connect to your own self-hosted Letta server, simply go to [https://app.letta.com](https://app.letta.com), sign in with any of the supported login methods, then navigate to the `Self-hosted` tab on the left panel.

[Read the full web ADE setup guide →](/guides/ade/browser)

<Warning>
  Letta Desktop is currently in beta and has known installation issues. If you are running into problems, please report your bug on [Discord](https://discord.gg/letta), or try using the web ADE instead.
</Warning>

[Letta Desktop](/guides/desktop/install) provides an all-in-one solution that includes both the Letta server and the ADE in a single application.

Key features of Letta Desktop:

* Combines the Letta server and ADE in one application
* Automatically establishes connection between components
* Ideal for offline development (no internet connection required)
* Runs on Windows (x64), macOS (M-series), and Linux (x64)

[Install Letta Desktop on MacOS, Windows, or Linux →](/guides/desktop/install)

Now that you've connected the ADE to your Letta server, you're ready to start building agents! Here are some recommended next steps:

1. **Create your first agent** using the "Create Agent" button
2. **Explore the [Agent Simulator](/guides/ade/simulator)** to interact with your agent
3. **Learn about [Tools](/guides/ade/tools)** to extend your agent's capabilities
4. **Configure [Core Memory](/guides/ade/core-memory)** to give your agent persistent in-context knowledge

---

## List Projects (Cloud-only)

**URL:** llms-txt#list-projects-(cloud-only)

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.letta.com/v1/projects

Reference: https://docs.letta.com/api-reference/projects/list

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: List Projects (Cloud-only)
  version: endpoint_projects.list
paths:
  /v1/projects:
    get:
      operationId: list
      summary: List Projects (Cloud-only)
      description: List all projects
      tags:
        - - subpackage_projects
      parameters:
        - name: name
          in: query
          required: false
          schema:
            type: string
        - name: offset
          in: query
          required: false
          schema:
            $ref: '#/components/schemas/V1ProjectsGetParametersOffset'
        - name: limit
          in: query
          required: false
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: '200'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/projects_list_Response_200'
components:
  schemas:
    V1ProjectsGetParametersOffset:
      oneOf:
        - type: string
        - type: number
          format: double
    V1ProjectsGetResponsesContentApplicationJsonSchemaProjectsItems:
      type: object
      properties:
        name:
          type: string
        slug:
          type: string
        id:
          type: string
      required:
        - name
        - slug
        - id
    projects_list_Response_200:
      type: object
      properties:
        projects:
          type: array
          items:
            $ref: >-
              #/components/schemas/V1ProjectsGetResponsesContentApplicationJsonSchemaProjectsItems
        hasNextPage:
          type: boolean
      required:
        - projects
        - hasNextPage
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.projects.list(
    name="name",
    offset="offset",
    limit="limit",
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.projects.list({
    name: "name",
    offset: "offset",
    limit: "limit"
});
```

Example 4 (go):
```go
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.letta.com/v1/projects"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## Get template snapshot (Cloud-only)

**URL:** llms-txt#get-template-snapshot-(cloud-only)

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.letta.com/v1/templates/{project_id}/{template_version}/snapshot

Get a snapshot of the template version, this will return the template state at a specific version

Reference: https://docs.letta.com/api-reference/templates/gettemplatesnapshot

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: Get template snapshot (Cloud-only)
  version: endpoint_templates.gettemplatesnapshot
paths:
  /v1/templates/{project_id}/{template_version}/snapshot:
    get:
      operationId: gettemplatesnapshot
      summary: Get template snapshot (Cloud-only)
      description: >-
        Get a snapshot of the template version, this will return the template
        state at a specific version
      tags:
        - - subpackage_templates
      parameters:
        - name: project_id
          in: path
          description: The project id
          required: true
          schema:
            type: string
        - name: template_version
          in: path
          description: >-
            The template version, formatted as {template-name}:{version-number}
            or {template-name}:latest
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: '200'
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/templates_gettemplatesnapshot_Response_200
components:
  schemas:
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsMemoryVariablesDataItems:
      type: object
      properties:
        key:
          type: string
        defaultValue:
          type:
            - string
            - 'null'
        type:
          type: string
      required:
        - key
        - type
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsMemoryVariables:
      type: object
      properties:
        version:
          type: string
        data:
          type: array
          items:
            $ref: >-
              #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsMemoryVariablesDataItems
      required:
        - version
        - data
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolVariablesDataItems:
      type: object
      properties:
        key:
          type: string
        defaultValue:
          type:
            - string
            - 'null'
        type:
          type: string
      required:
        - key
        - type
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolVariables:
      type: object
      properties:
        version:
          type: string
        data:
          type: array
          items:
            $ref: >-
              #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolVariablesDataItems
      required:
        - version
        - data
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItemsOneOf0Type:
      type: string
      enum:
        - value: constrain_child_tools
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItemsOneOf0ChildArgNodesItems:
      type: object
      properties:
        name:
          type: string
        args:
          type:
            - object
            - 'null'
          additionalProperties:
            description: Any type
      required:
        - name
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItems0:
      type: object
      properties:
        tool_name:
          type: string
        type:
          $ref: >-
            #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItemsOneOf0Type
        prompt_template:
          type:
            - string
            - 'null'
        children:
          type: array
          items:
            type: string
        child_arg_nodes:
          type:
            - array
            - 'null'
          items:
            $ref: >-
              #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItemsOneOf0ChildArgNodesItems
      required:
        - tool_name
        - children
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItemsOneOf1Type:
      type: string
      enum:
        - value: run_first
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItems1:
      type: object
      properties:
        tool_name:
          type: string
        type:
          $ref: >-
            #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItemsOneOf1Type
        prompt_template:
          type:
            - string
            - 'null'
        args:
          type:
            - object
            - 'null'
          additionalProperties:
            description: Any type
      required:
        - tool_name
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItemsOneOf2Type:
      type: string
      enum:
        - value: exit_loop
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItems2:
      type: object
      properties:
        tool_name:
          type: string
        type:
          $ref: >-
            #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItemsOneOf2Type
        prompt_template:
          type:
            - string
            - 'null'
      required:
        - tool_name
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItemsOneOf3Type:
      type: string
      enum:
        - value: conditional
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItems3:
      type: object
      properties:
        tool_name:
          type: string
        type:
          $ref: >-
            #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItemsOneOf3Type
        prompt_template:
          type:
            - string
            - 'null'
        default_child:
          type:
            - string
            - 'null'
        child_output_mapping:
          type: object
          additionalProperties:
            type: string
        require_output_mapping:
          type: boolean
      required:
        - tool_name
        - child_output_mapping
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItemsOneOf4Type:
      type: string
      enum:
        - value: continue_loop
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItems4:
      type: object
      properties:
        tool_name:
          type: string
        type:
          $ref: >-
            #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItemsOneOf4Type
        prompt_template:
          type:
            - string
            - 'null'
      required:
        - tool_name
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItemsOneOf5Type:
      type: string
      enum:
        - value: required_before_exit
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItems5:
      type: object
      properties:
        tool_name:
          type: string
        type:
          $ref: >-
            #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItemsOneOf5Type
        prompt_template:
          type:
            - string
            - 'null'
      required:
        - tool_name
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItemsOneOf6Type:
      type: string
      enum:
        - value: max_count_per_step
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItems6:
      type: object
      properties:
        tool_name:
          type: string
        type:
          $ref: >-
            #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItemsOneOf6Type
        prompt_template:
          type:
            - string
            - 'null'
        max_count_limit:
          type: number
          format: double
      required:
        - tool_name
        - max_count_limit
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItemsOneOf7Type:
      type: string
      enum:
        - value: parent_last_tool
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItems7:
      type: object
      properties:
        tool_name:
          type: string
        type:
          $ref: >-
            #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItemsOneOf7Type
        prompt_template:
          type:
            - string
            - 'null'
        children:
          type: array
          items:
            type: string
      required:
        - tool_name
        - children
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItemsOneOf8Type:
      type: string
      enum:
        - value: requires_approval
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItems8:
      type: object
      properties:
        tool_name:
          type: string
        type:
          $ref: >-
            #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItemsOneOf8Type
        prompt_template:
          type:
            - string
            - 'null'
      required:
        - tool_name
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItems:
      oneOf:
        - $ref: >-
            #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItems0
        - $ref: >-
            #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItems1
        - $ref: >-
            #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItems2
        - $ref: >-
            #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItems3
        - $ref: >-
            #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItems4
        - $ref: >-
            #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItems5
        - $ref: >-
            #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItems6
        - $ref: >-
            #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItems7
        - $ref: >-
            #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItems8
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsAgentType:
      type: string
      enum:
        - value: letta_v1_agent
        - value: memgpt_agent
        - value: memgpt_v2_agent
        - value: react_agent
        - value: workflow_agent
        - value: split_thread_agent
        - value: sleeptime_agent
        - value: voice_convo_agent
        - value: voice_sleeptime_agent
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItems:
      type: object
      properties:
        model:
          type: string
        systemPrompt:
          type: string
        toolIds:
          type:
            - array
            - 'null'
          items:
            type: string
        sourceIds:
          type:
            - array
            - 'null'
          items:
            type: string
        memoryVariables:
          oneOf:
            - $ref: >-
                #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsMemoryVariables
            - type: 'null'
        toolVariables:
          oneOf:
            - $ref: >-
                #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolVariables
            - type: 'null'
        tags:
          type:
            - array
            - 'null'
          items:
            type: string
        identityIds:
          type:
            - array
            - 'null'
          items:
            type: string
        toolRules:
          type:
            - array
            - 'null'
          items:
            $ref: >-
              #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsToolRulesItems
        agentType:
          $ref: >-
            #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItemsAgentType
        properties:
          oneOf:
            - $ref: >-
                #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItems
            - type: 'null'
        entityId:
          type: string
        name:
          type: string
      required:
        - model
        - systemPrompt
        - toolIds
        - sourceIds
        - memoryVariables
        - toolVariables
        - tags
        - identityIds
        - toolRules
        - agentType
        - properties
        - entityId
        - name
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaBlocksItems:
      type: object
      properties:
        entityId:
          type: string
        label:
          type: string
        value:
          type: string
        limit:
          type: number
          format: double
        description:
          type: string
        preserveOnMigration:
          type:
            - boolean
            - 'null'
        readOnly:
          type: boolean
      required:
        - entityId
        - label
        - value
        - limit
        - description
        - preserveOnMigration
        - readOnly
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaRelationshipsItems:
      type: object
      properties:
        agentEntityId:
          type: string
        blockEntityId:
          type: string
      required:
        - agentEntityId
        - blockEntityId
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaConfiguration:
      type: object
      properties:
        managerAgentEntityId:
          type: string
        managerType:
          type: string
        terminationToken:
          type: string
        maxTurns:
          type: number
          format: double
        sleeptimeAgentFrequency:
          type: number
          format: double
        maxMessageBufferLength:
          type: number
          format: double
        minMessageBufferLength:
          type: number
          format: double
    V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaType:
      type: string
      enum:
        - value: classic
        - value: cluster
        - value: sleeptime
        - value: round_robin
        - value: supervisor
        - value: dynamic
        - value: voice_sleeptime
    templates_gettemplatesnapshot_Response_200:
      type: object
      properties:
        agents:
          type: array
          items:
            $ref: >-
              #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaAgentsItems
        blocks:
          type: array
          items:
            $ref: >-
              #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaBlocksItems
        relationships:
          type: array
          items:
            $ref: >-
              #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaRelationshipsItems
        configuration:
          $ref: >-
            #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaConfiguration
        type:
          $ref: >-
            #/components/schemas/V1TemplatesProjectIdTemplateVersionSnapshotGetResponsesContentApplicationJsonSchemaType
        version:
          type: string
      required:
        - agents
        - blocks
        - relationships
        - configuration
        - type
        - version
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.templates.gettemplatesnapshot(
    project_id="project_id",
    template_version="template_version",
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.templates.gettemplatesnapshot("project_id", "template_version");
```

Example 4 (go):
```go
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.letta.com/v1/templates/project_id/template_version/snapshot"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## Update template description (Cloud-only)

**URL:** llms-txt#update-template-description-(cloud-only)

**Contents:**
- OpenAPI Specification
- SDK Code Examples

PATCH https://api.letta.com/v1/templates/{project_id}/{template_name}/description
Content-Type: application/json

Updates the description for all versions of a template with the specified name. Versions are automatically stripped from the current template name if accidentally included.

Reference: https://docs.letta.com/api-reference/templates/updatetemplatedescription

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: Update template description (Cloud-only)
  version: endpoint_templates.updatetemplatedescription
paths:
  /v1/templates/{project_id}/{template_name}/description:
    patch:
      operationId: updatetemplatedescription
      summary: Update template description (Cloud-only)
      description: >-
        Updates the description for all versions of a template with the
        specified name. Versions are automatically stripped from the current
        template name if accidentally included.
      tags:
        - - subpackage_templates
      parameters:
        - name: project_id
          in: path
          description: The project id
          required: true
          schema:
            type: string
        - name: template_name
          in: path
          description: >-
            The template name (version will be automatically stripped if
            included)
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: '200'
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/templates_updatetemplatedescription_Response_200
        '400':
          description: '400'
          content: {}
        '404':
          description: '404'
          content: {}
      requestBody:
        description: Body
        content:
          application/json:
            schema:
              type: object
              properties:
                description:
                  type: string
components:
  schemas:
    templates_updatetemplatedescription_Response_200:
      type: object
      properties:
        success:
          type: boolean
      required:
        - success
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.templates.updatetemplatedescription(
    project_id="project_id",
    template_name="template_name",
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.templates.updatetemplatedescription("project_id", "template_name");
```

Example 4 (go):
```go
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.letta.com/v1/templates/project_id/template_name/description"

	payload := strings.NewReader("{}")

	req, _ := http.NewRequest("PATCH", url, payload)

	req.Header.Add("Authorization", "Bearer <token>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## connect to a local server

**URL:** llms-txt#connect-to-a-local-server

client = Letta(base_url="http://localhost:8283")

---

## Letta Cloud

**URL:** llms-txt#letta-cloud

**Contents:**
- The fastest way to bring stateful agents to production
- Model agnostic with zero provider lock-in
- Next steps

> Deploy stateful agents at scale in the cloud

Letta Cloud is our fully-managed service for stateful agents. While Letta can be self-hosted, Letta Cloud eliminates all infrastructure management, server optimization, and system administration so you can focus entirely on building agents.

## The fastest way to bring stateful agents to production

**Develop faster with any model and 24/7 agent uptime**: Access to OpenAI, Anthropic Claude, and Google Gemini with high rate limits. Our platform automatically scales to meet demand and ensures 24/7 uptime of your agents. Your agents' state, memory, and conversation history are securely persisted.

**Features designed to help you scale to hundreds of agents**: Letta Cloud includes features designed for applications managing large numbers of agents: agent templates, template versioning, memory variables injected on agent creation, and advanced tooling for managing thousands of agents across many users.

## Model agnostic with zero provider lock-in

Your agent state is stored in a model-agnostic format, allowing you to easily migrate your agents (and their memories, message history, reasoning traces, tool execution traces, etc.) from one model provider to another.

Letta Cloud also supports [agent file](/guides/agents/agent-file), which allows you to move your agents freely between self-hosted instances of Letta and Letta Cloud.

You can upload local agents to Cloud by importing their `.af` files, and run Cloud agents locally by downloading and importing them into your self-hosted server.

<CardGroup>
  <Card title="Create an API key" icon="fa-sharp fa-light fa-key" href="/guides/cloud/letta-api-key">
    Access Letta Cloud through APIs and SDKs using an API key
  </Card>

<Card title="Plans & Pricing" icon="fa-sharp fa-light fa-credit-card" href="/guides/cloud/plans">
    Learn about pricing plans and features
  </Card>
</CardGroup>

---

## Delete template (Cloud-only)

**URL:** llms-txt#delete-template-(cloud-only)

**Contents:**
- OpenAPI Specification
- SDK Code Examples

DELETE https://api.letta.com/v1/templates/{project_id}/{template_name}
Content-Type: application/json

Deletes all versions of a template with the specified name

Reference: https://docs.letta.com/api-reference/templates/deletetemplate

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: Delete template (Cloud-only)
  version: endpoint_templates.deletetemplate
paths:
  /v1/templates/{project_id}/{template_name}:
    delete:
      operationId: deletetemplate
      summary: Delete template (Cloud-only)
      description: Deletes all versions of a template with the specified name
      tags:
        - - subpackage_templates
      parameters:
        - name: project_id
          in: path
          description: The project id
          required: true
          schema:
            type: string
        - name: template_name
          in: path
          description: The template name (without version)
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: '200'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/templates_deletetemplate_Response_200'
        '404':
          description: '404'
          content: {}
      requestBody:
        description: Body
        content:
          application/json:
            schema:
              type: object
              properties: {}
components:
  schemas:
    templates_deletetemplate_Response_200:
      type: object
      properties:
        success:
          type: boolean
      required:
        - success
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.templates.deletetemplate(
    project_id="project_id",
    template_name="template_name",
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.templates.deletetemplate("project_id", "template_name");
```

Example 4 (go):
```go
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.letta.com/v1/templates/project_id/template_name"

	payload := strings.NewReader("{}")

	req, _ := http.NewRequest("DELETE", url, payload)

	req.Header.Add("Authorization", "Bearer <token>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## Accessing the web ADE

**URL:** llms-txt#accessing-the-web-ade

**Contents:**
- Understanding Connection Types
- Connecting to a Local Server
- Connecting to a Remote Server
- Managing Server Connections
  - Saving Server Connections
  - Switching Between Servers

> Connect to both self-hosted and cloud agents from the web ADE

The web ADE is available at [https://app.letta.com](https://app.letta.com). You can use the browser-based ADE to connect to both Letta Cloud, and agents running on your own Letta deployments.

## Understanding Connection Types

The ADE can connect to different types of Letta servers:

1. **Local Server**: A Letta server running on your local machine (`localhost`)
2. **Remote Server**: A self-hosted Letta server running on a remote address
3. **Letta Cloud**: Letta's managed cloud service for hosting agents

All connections use the Letta REST API to communicate between the ADE and the server. For remote servers (non-`localhost`), HTTPS is required.

## Connecting to a Local Server

Connecting to a local Letta server is the simplest setup and ideal for development:

1. **Start your Letta server** using [Docker](/guides/selfhosting)
2. **Access the ADE** by visiting [https://app.letta.com](https://app.letta.com)
3. **Select "Local server"** from the server list in the left panel

The ADE will automatically detect your local Letta server running on `localhost:8283` and establish a connection.

<img src="https://raw.githubusercontent.com/letta-ai/letta/refs/heads/main/assets/example_ade_screenshot_agents_light.png" />

<img src="https://raw.githubusercontent.com/letta-ai/letta/refs/heads/main/assets/example_ade_screenshot_agents.png" />

## Connecting to a Remote Server

For production environments or team collaboration, you may want to connect to a Letta server running on a remote machine:

<Warning>
  The cloud/web ADE does **not support** connecting to `http` (non-`https`) IP addresses, *except* for `localhost`.

For example, if your server is running on a home address like `http://192.168.1.10:8283`, the ADE (when running on a browser on another device on the network) will not be able to connect to your server because it is not using `https`.

For more information on setting up `https` proxies, see the [remote deployment guide](/guides/server/remote).
</Warning>

To connect to a remote Letta server:

1. **Deploy your Letta server** on your preferred hosting service (EC2, Railway, etc.)
2. **Ensure HTTPS access** is configured for your server
3. **In the ADE, click "Add remote server"**
4. **Enter the connection details**:
   * Server name: A friendly name to identify this server
   * Server URL: The full URL including `https://` and port if needed
   * Server password: If you've configured API authentication, enter the password

<img src="file:4028bbe6-ed6b-43c5-be44-52095ff11593" />

<img src="file:b6630dd7-773b-4383-991e-fd5e9a44c87b" />

## Managing Server Connections

The ADE allows you to manage multiple server connections:

### Saving Server Connections

Once you add a remote server, it will be saved in your browser's local storage for easy access in future sessions. To manage saved connections:

1. Click on the server dropdown in the left panel
2. Select "Manage servers" to view all saved connections
3. Use the options to edit or remove servers from your list

### Switching Between Servers

You can easily switch between different Letta servers:

1. Click on the current server name in the left panel
2. Select a different server from the dropdown list
3. The ADE will connect to the selected server and display its agents

This flexibility allows you to work with development, staging, and production environments from a single ADE interface.

---

## List template versions (Cloud-only)

**URL:** llms-txt#list-template-versions-(cloud-only)

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.letta.com/v1/templates/{project_id}/{name}/versions

List all versions of a specific template

Reference: https://docs.letta.com/api-reference/templates/listtemplateversions

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: List template versions (Cloud-only)
  version: endpoint_templates.listtemplateversions
paths:
  /v1/templates/{project_id}/{name}/versions:
    get:
      operationId: listtemplateversions
      summary: List template versions (Cloud-only)
      description: List all versions of a specific template
      tags:
        - - subpackage_templates
      parameters:
        - name: project_id
          in: path
          description: The project id
          required: true
          schema:
            type: string
        - name: name
          in: path
          description: The template name (without version)
          required: true
          schema:
            type: string
        - name: offset
          in: query
          required: false
          schema:
            $ref: >-
              #/components/schemas/V1TemplatesProjectIdNameVersionsGetParametersOffset
        - name: limit
          in: query
          required: false
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: '200'
          content:
            application/json:
              schema:
                $ref: >-
                  #/components/schemas/templates_listtemplateversions_Response_200
        '404':
          description: '404'
          content: {}
components:
  schemas:
    V1TemplatesProjectIdNameVersionsGetParametersOffset:
      oneOf:
        - type: string
        - type: number
          format: double
    V1TemplatesProjectIdNameVersionsGetResponsesContentApplicationJsonSchemaVersionsItems:
      type: object
      properties:
        version:
          type: string
        created_at:
          type: string
        message:
          type: string
        is_latest:
          type: boolean
      required:
        - version
        - created_at
        - is_latest
    templates_listtemplateversions_Response_200:
      type: object
      properties:
        versions:
          type: array
          items:
            $ref: >-
              #/components/schemas/V1TemplatesProjectIdNameVersionsGetResponsesContentApplicationJsonSchemaVersionsItems
        has_next_page:
          type: boolean
        total_count:
          type: number
          format: double
      required:
        - versions
        - has_next_page
        - total_count
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.templates.listtemplateversions(
    project_id="project_id",
    name="name",
    offset="offset",
    limit="limit",
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.templates.listtemplateversions("project_id", "name", {
    offset: "offset",
    limit: "limit"
});
```

Example 4 (go):
```go
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.letta.com/v1/templates/project_id/name/versions"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## Deploying a Letta server remotely

**URL:** llms-txt#deploying-a-letta-server-remotely

**Contents:**
- Connecting the cloud/web ADE to your remote server
  - Using a reverse proxy to generate an `https` address
  - Port forwarding to localhost
- Securing your Letta server
- Connecting to a persistent database volume
- Connecting to an external Postgres database

The Letta server can be deployed remotely, for example on cloud services like [Railway](https://railway.com/), or also on your own self-hosted infrastructure.
For an example guide on how to remotely deploy the Letta server, see our [Railway deployment guide](/guides/server/railway).

## Connecting the cloud/web ADE to your remote server

<Warning>
  The cloud/web ADE can only connect to remote servers running on `https`.
</Warning>

The cloud (web) ADE is only able to connect to remote servers running on `https` - the only exception is `localhost`, for which `http` is allowed (except for Safari, where it is also blocked).

Most cloud services have ingress tools that will handle certificate management for you and you will automatically be provisioned an `https` address (for example Railway will automatically generate a static `https` address for your deployment).

### Using a reverse proxy to generate an `https` address

If you are running your Letta server on self-hosted infrastructure, you may need to manually create an `https` address for your server.
This can be done in numerous ways using reverse proxies:

1. Use a service like [ngrok](https://ngrok.com/) to get an `https` address (on ngrok) for your server
2. Use [Caddy](https://github.com/caddyserver/caddy) or [Traefik](https://github.com/traefik/traefik) as a reverse proxy (which will manage the certificates for you)
3. Use [nginx](https://nginx.org/) with [Let's Encrypt](https://letsencrypt.org/) as a reverse proxy (manage the certificates yourself)

### Port forwarding to localhost

Alternatively, you can also forward your server's `http` address to `localhost`, since the `https` restriction does not apply to `localhost` (on browsers other than Safari):

If you use the port forwarding approach, then you will not need to "Add remote server" in the ADE, instead the server will be accessible under "Local server".

## Securing your Letta server

<Warning>
  Do not expose your Letta server to the public internet unless it is password protected (either via the `SECURE` environment variable, or your own protection mechanism).
</Warning>

If you are running your Letta server on a cloud service (like Railway) that exposes your server via a static IP address, you will likely want to secure your Letta server with a password by using the `SECURE` environment variable.
For more information, see our [password guide](/guides/server/docker#password-protection-advanced).

Note that the `SECURE` variable does **not** have anything to do with `https`, it simply turns on basic password protection to the API requests going to your Letta server. Make sure to also enable [tool sandboxing](/guides/selfhosting#tool-sandboxing) if you are allowing untrusted users to create tools on your Letta server.

## Connecting to a persistent database volume

<Warning>
  If you do not mount a persistent database volume, your agent data will be lost when your Docker container restarts.
</Warning>

The Postgres database inside the Letta Docker image will look attempt to store data at `/var/lib/postgresql/data`, so to make sure your state persists across container restarts, you need to mount a volume (with a persistent data store) to that directory.

For example, the recommend `docker run` command includes `-v ~/.letta/.persist/pgdata:/var/lib/postgresql/data` as a flag, which mounts your local directory `~/.letta/.persist/pgdata` to the container's `/var/lib/postgresql/data` directory (so all your agent data is stored at `~/.letta/.persist/pgdata`).

Different cloud infrastructure platforms will handle mounting differently. You can view our [Railway deployment guide](/guides/server/railway) for an example of how to do this.

## Connecting to an external Postgres database

<Tip>
  Unless you have a specific reason to use an external database, we recommend using the internal database provided by the Letta Docker image, and simply mounting a volume to make sure your database is persistent across restarts.
</Tip>

You can connect Letta to an external Postgres database by setting the `LETTA_PG_URI` environment variable to the connection string of your Postgres database.
To have the server connect to the external Postgres properly, you will need to use `alembic` or manually create the database and tables.

**Examples:**

Example 1 (sh):
```sh
ssh -L 8283:localhost:8283 your_server_username@your_server_ip
```

---

## List templates (Cloud-only)

**URL:** llms-txt#list-templates-(cloud-only)

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.letta.com/v1/templates

Reference: https://docs.letta.com/api-reference/templates/list

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: List templates (Cloud-only)
  version: endpoint_templates.list
paths:
  /v1/templates:
    get:
      operationId: list
      summary: List templates (Cloud-only)
      description: List all templates
      tags:
        - - subpackage_templates
      parameters:
        - name: offset
          in: query
          required: false
          schema:
            $ref: '#/components/schemas/V1TemplatesGetParametersOffset'
        - name: exact
          in: query
          description: Whether to search for an exact name match
          required: false
          schema:
            type: string
        - name: limit
          in: query
          required: false
          schema:
            type: string
        - name: version
          in: query
          description: >-
            Specify the version you want to return, otherwise will return the
            latest version
          required: false
          schema:
            type: string
        - name: template_id
          in: query
          required: false
          schema:
            type: string
        - name: name
          in: query
          required: false
          schema:
            type: string
        - name: search
          in: query
          required: false
          schema:
            type: string
        - name: project_slug
          in: query
          required: false
          schema:
            type: string
        - name: project_id
          in: query
          required: false
          schema:
            type: string
        - name: sort_by
          in: query
          required: false
          schema:
            $ref: '#/components/schemas/V1TemplatesGetParametersSortBy'
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: '200'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/templates_list_Response_200'
components:
  schemas:
    V1TemplatesGetParametersOffset:
      oneOf:
        - type: string
        - type: number
          format: double
    V1TemplatesGetParametersSortBy:
      type: string
      enum:
        - value: updated_at
        - value: created_at
    V1TemplatesGetResponsesContentApplicationJsonSchemaTemplatesItems:
      type: object
      properties:
        name:
          type: string
        id:
          type: string
        project_id:
          type: string
        project_slug:
          type: string
        latest_version:
          type: string
        description:
          type: string
        template_deployment_slug:
          type: string
        updated_at:
          type: string
      required:
        - name
        - id
        - project_id
        - project_slug
        - latest_version
        - template_deployment_slug
        - updated_at
    templates_list_Response_200:
      type: object
      properties:
        templates:
          type: array
          items:
            $ref: >-
              #/components/schemas/V1TemplatesGetResponsesContentApplicationJsonSchemaTemplatesItems
        has_next_page:
          type: boolean
      required:
        - templates
        - has_next_page
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.templates.list(
    offset="offset",
    exact="exact",
    limit="limit",
    version="version",
    template_id="template_id",
    name="name",
    search="search",
    project_slug="project_slug",
    project_id="project_id",
    sort_by="updated_at",
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.templates.list({
    offset: "offset",
    exact: "exact",
    limit: "limit",
    version: "version",
    templateId: "template_id",
    name: "name",
    search: "search",
    projectSlug: "project_slug",
    projectId: "project_id",
    sortBy: "updated_at"
});
```

Example 4 (go):
```go
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.letta.com/v1/templates"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## Migrate deployment to template version (Cloud-only)

**URL:** llms-txt#migrate-deployment-to-template-version-(cloud-only)

**Contents:**
- OpenAPI Specification
- SDK Code Examples

POST https://api.letta.com/v1/templates/{project_id}/{template_name}/deployments/{deployment_id}/migrate
Content-Type: application/json

Migrates a deployment to a specific template version

Reference: https://docs.letta.com/api-reference/templates/migratedeployment

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: Migrate deployment to template version (Cloud-only)
  version: endpoint_templates.migratedeployment
paths:
  /v1/templates/{project_id}/{template_name}/deployments/{deployment_id}/migrate:
    post:
      operationId: migratedeployment
      summary: Migrate deployment to template version (Cloud-only)
      description: Migrates a deployment to a specific template version
      tags:
        - - subpackage_templates
      parameters:
        - name: project_id
          in: path
          description: The project id
          required: true
          schema:
            type: string
        - name: template_name
          in: path
          description: The template name (without version)
          required: true
          schema:
            type: string
        - name: deployment_id
          in: path
          description: The deployment ID to migrate
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: '200'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/templates_migratedeployment_Response_200'
        '400':
          description: '400'
          content: {}
        '404':
          description: '404'
          content: {}
        '500':
          description: '500'
          content: {}
      requestBody:
        description: Body
        content:
          application/json:
            schema:
              type: object
              properties:
                version:
                  type: string
                preserve_tool_variables:
                  type: boolean
                preserve_core_memories:
                  type: boolean
                memory_variables:
                  type: object
                  additionalProperties:
                    type: string
              required:
                - version
components:
  schemas:
    templates_migratedeployment_Response_200:
      type: object
      properties:
        success:
          type: boolean
        message:
          type: string
      required:
        - success
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.templates.migratedeployment(
    project_id="project_id",
    template_name="template_name",
    deployment_id="deployment_id",
    version="version",
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.templates.migratedeployment("project_id", "template_name", "deployment_id", {
    version: "version"
});
```

Example 4 (go):
```go
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.letta.com/v1/templates/project_id/template_name/deployments/deployment_id/migrate"

	payload := strings.NewReader("{\n  \"version\": \"string\"\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("Authorization", "Bearer <token>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## Scheduling

**URL:** llms-txt#scheduling

**Contents:**
- Common Use Cases
- Option 1: Simple Loop
- Option 2: System Cron Jobs

**Scheduling** is a technique for triggering Letta agents at regular intervals.
Many real-world applications require proactive behavior, such as checking emails every few hours or scraping news sites.
Scheduling can support autonomous agents with the capability to manage ongoing processes.

<Note>
  Native scheduling functionality is on the Letta Cloud roadmap. The approaches described in this guide are temporary solutions that work with both self-hosted and cloud deployments.
</Note>

When building autonomous agents with Letta, you often need to trigger them at regular intervals for tasks like:

* **System Monitoring**: Health checks that adapt based on historical patterns
* **Data Processing**: Intelligent ETL processes that handle edge cases contextually
* **Memory Maintenance**: Agents that optimize their own knowledge base over time
* **Proactive Notifications**: Context-aware alerts that consider user preferences and timing
* **Continuous Learning**: Agents that regularly ingest new information and update their understanding

This guide covers simple approaches to implement scheduled agent interactions.

## Option 1: Simple Loop

The most straightforward approach for development and testing:

**Pros:** Simple, easy to debug
**Cons:** Blocks terminal, stops if process dies

## Option 2: System Cron Jobs

For production deployments, use cron for reliability:

Add to crontab with `crontab -e`:

```bash
*/5 * * * * /usr/bin/python3 /path/to/send_message.py >> /var/log/letta_cron.log 2>&1

**Examples:**

Example 1 (unknown):
```unknown

```

Example 2 (unknown):
```unknown
</CodeGroup>

**Pros:** Simple, easy to debug
**Cons:** Blocks terminal, stops if process dies

## Option 2: System Cron Jobs

For production deployments, use cron for reliability:

<CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>

Add to crontab with `crontab -e`:
```

---

## Installing Letta Desktop

**URL:** llms-txt#installing-letta-desktop

**Contents:**
- Download Letta Desktop
- Adding LLM backends
- Configuration Modes
- Support

> Install Letta Desktop on your MacOS, Windows, or Linux machine

<Note>
  Letta Desktop is currently in **beta**.
  For a more stable development experience, we recommend using the [cloud ADE](/guides/ade/browser) with [Docker](/guides/selfhosting), or [Letta Cloud](/guides/cloud/overview).

For support, join our community [Discord server](https://discord.gg/letta).
</Note>

<img src="file:4972da30-ea4a-48b2-b9e7-a3b2450b41d1" />

<img src="file:3961c3bc-d07f-47f4-8ddb-7f2d662750db" />

**Letta Desktop** allows you to run the ADE (Agent Development Environment) as a local application.
Letta Desktop also bundles a built-in Letta server, so can run Letta Desktop standalone, or you can connect it to a self-hosted Letta server.

## Download Letta Desktop

<CardGroup>
  <Card title="Download Letta Desktop for Mac (Apple Silicon)" icon="fa-brands fa-apple" iconPosition="left" href="https://downloads.letta.com/mac/dmg/arm64" />

<Card title="Download Letta Desktop for Windows (x64)" icon="fa-brands fa-windows" iconPosition="left" href="https://downloads.letta.com/windows/nsis/x64" />

<Card title="Download Letta Desktop for Linux (x64)" icon="fa-brands fa-linux" iconPosition="left" href="https://downloads.letta.com/linux/appImage/x64" />
</CardGroup>

## Adding LLM backends

<Note>
  The integrations page is only available when using the embedded Letta server.
  If you are using a self-hosted Letta server, you can add LLM backends by editing the environment variables when you launch your server.
  See [self-hosting](/guides/selfhosting) for more information.
</Note>

The Letta server can be connected to various LLM API backends.
You can add additional LLM API backends by opening the integrations panel (clicking the <Icon icon="square-rss" /> icon).
When you configure a new integration (by setting the environment variable in the dialog), the Letta server will be restarted to load the new LLM API backend.

<img src="file:ddc7d856-b458-465d-a9d7-ff2d0b929684" />

You can also edit the environment variable file directly, located at `~/.letta/env`.

For this quickstart demo, we'll add an OpenAI API key (once we enter our key and **click confirm**, the Letta server will automatically restart):

<img src="file:34560909-987d-4288-bccf-a4ed1bdcc6b5" />

## Configuration Modes

Letta Desktop can run in two primary modes, which can be configured from the settings menu in the app, or by manually editing the `~/.letta/desktop_config.json` file.

<AccordionGroup>
  <Accordion title="Embedded server mode" icon="database">
    In this mode Letta Desktop runs its own embedded Letta server with a SQLite database.
    No additional setup is required - just install Letta Desktop and start creating stateful agents!

<Tabs>
      <Tab title="Configuration">
        To manually configure embedded mode, create or edit `~/.letta/desktop_config.json`:

</Tab>
    </Tabs>
  </Accordion>

<Accordion title="Self-Hosted server mode (recommended)" icon="server">
    Connect Letta Desktop to your own self-hosted Letta server.
    You can use this mode to connect to a Letta server running locally (e.g. on `localhost:8283` via Docker), or to a Letta server running on a remote machine.

<Tabs>
      <Tab title="Local Server">
        For a Letta server running locally on your machine:

<Tab title="Remote Server">
        For a password-protected Letta server on a remote machine:

<Note>
          If your server is [password protected](/guides/selfhosting), include the `token` field. Otherwise, omit it.
        </Note>
      </Tab>
    </Tabs>
  </Accordion>

<Accordion title="Embedded PostgreSQL (deprecated)" icon="triangle-exclamation">
    <Warning>
      This mode is deprecated and will be removed in a future release. See our migration guide if you have existing data in PostgreSQL from Letta Desktop you want to preserve.
    </Warning>

<Tabs>
      <Tab title="Configuration">
        For backwards compatibility, you can still run the embedded server with PostgreSQL:

<Tab title="Migration Guide">
        If you have existing data in the embedded PostgreSQL database, you can migrate to a Docker-based Letta server that reads from your existing data:

1. First, locate your PostgreSQL data directory (by default for old versions of Letta Desktop this is `~/.letta/desktop_data`)

2. Launch a Docker Letta server with your existing data mounted:

3. Update your Letta Desktop configuration to connect to this self-hosted server:

Your agents and data will be preserved and accessible through the Docker-based server.
      </Tab>
    </Tabs>
  </Accordion>
</AccordionGroup>

For bug reports and feature requests, contact us on [Discord](https://discord.gg/letta).

**Examples:**

Example 1 (json):
```json
{
          "version": "1",
          "databaseConfig": {
            "type": "embedded",
            "embeddedType": "sqlite"
          }
        }
```

Example 2 (json):
```json
{
          "version": "1",
          "databaseConfig": {
            "type": "local",
            "url": "http://localhost:8283"
          }
        }
```

Example 3 (json):
```json
{
          "version": "1",
          "databaseConfig": {
            "type": "local",
            "url": "https://remote-machine.com",
            "token": "your-password"
          }
        }
```

Example 4 (json):
```json
{
          "version": "1",
          "databaseConfig": {
            "type": "embedded",
            "embeddedType": "pgserver"
          }
        }
```

---

## Fork template (Cloud-only)

**URL:** llms-txt#fork-template-(cloud-only)

**Contents:**
- OpenAPI Specification
- SDK Code Examples

POST https://api.letta.com/v1/templates/{project_id}/{template_version}/fork
Content-Type: application/json

Forks a template version into a new template

Reference: https://docs.letta.com/api-reference/templates/forktemplate

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: Fork template (Cloud-only)
  version: endpoint_templates.forktemplate
paths:
  /v1/templates/{project_id}/{template_version}/fork:
    post:
      operationId: forktemplate
      summary: Fork template (Cloud-only)
      description: Forks a template version into a new template
      tags:
        - - subpackage_templates
      parameters:
        - name: project_id
          in: path
          description: The project id
          required: true
          schema:
            type: string
        - name: template_version
          in: path
          description: >-
            The template version, formatted as {template-name}:{version-number}
            or {template-name}:latest
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: '200'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/templates_forktemplate_Response_200'
        '400':
          description: '400'
          content: {}
      requestBody:
        description: Body
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
components:
  schemas:
    templates_forktemplate_Response_200:
      type: object
      properties:
        name:
          type: string
        id:
          type: string
        project_id:
          type: string
        project_slug:
          type: string
        latest_version:
          type: string
        description:
          type: string
        template_deployment_slug:
          type: string
        updated_at:
          type: string
      required:
        - name
        - id
        - project_id
        - project_slug
        - latest_version
        - template_deployment_slug
        - updated_at
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.templates.forktemplate(
    project_id="project_id",
    template_version="template_version",
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.templates.forktemplate("project_id", "template_version");
```

Example 4 (go):
```go
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.letta.com/v1/templates/project_id/template_version/fork"

	payload := strings.NewReader("{}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("Authorization", "Bearer <token>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## Exit code 0 = pass (continue deployment)

**URL:** llms-txt#exit-code-0-=-pass-(continue-deployment)

---

## Deploy Letta Server on Railway

**URL:** llms-txt#deploy-letta-server-on-railway

**Contents:**
- Deploying the Letta Railway template
- Accessing the deployment via the ADE
- Accessing the deployment via the Letta API
  - Adding additional environment variables

<Tip>
  [Railway](https://railway.app)

is a service that allows you to easily deploy services (such as Docker containers) to the cloud. The following example uses Railway, but the same general principles around deploying the Letta Docker image on a cloud service and connecting it to the ADE) are generally applicable to other cloud services beyond Railway.
</Tip>

## Deploying the Letta Railway template

We've prepared a Letta Railway template that has the necessary environment variables set and mounts a persistent volume for database storage.
You can access the template by clicking the "Deploy on Railway" button below:

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.app/template/jgUR1t?referralCode=kdR8zc)

<Frame caption="The deployment screen will give you the opportunity to specify some basic environment variables such as your OpenAI API key. You can also specify these after deployment in the variables section in the Railway viewer.">
  <img src="file:215efbce-764a-4bd5-a02d-81ea522075fb" />
</Frame>

<Frame caption="If the deployment is successful, it will be shown as 'Active', and you can click 'View logs'.">
  <img src="file:5e2e2d22-d9b5-4be3-870d-0361cc4b7a75" />
</Frame>

<Frame caption="Clicking 'View logs' will reveal the static IP address of the deployment (ending in 'railway.app').">
  <img src="file:e4ede09b-43f2-427e-ae16-1b6c09557692" />
</Frame>

## Accessing the deployment via the ADE

Now that the Railway deployment is active, all we need to do to access it via the ADE is add it to as a new remote Letta server.
The default password set in the template is `password`, which can be changed at the deployment stage or afterwards in the 'variables' page on the Railway deployment.

Click "Add remote server", then enter the details from Railway (use the static IP address shown in the logs, and use the password set via the environment variables):

<img src="file:4028bbe6-ed6b-43c5-be44-52095ff11593" />

<img src="file:b6630dd7-773b-4383-991e-fd5e9a44c87b" />

## Accessing the deployment via the Letta API

Accessing the deployment via the [Letta API](https://docs.letta.com/api-reference) is simple, we just need to swap the base URL of the endpoint with the IP address from the Railway deployment.

For example if the Railway IP address is `https://MYSERVER.up.railway.app` and the password is `banana`, to create an agent on the deployment, we can use the following shell command:

This will create an agent with two memory blocks, configured to use `gpt-4o-mini` as the LLM model, and `text-embedding-3-small` as the embedding model.

If the Letta server is not password protected, we can omit the `X-BARE-PASSWORD` header.

<Check>
  That's it! Now you should be able to create and interact with agents on your remote Letta server (deployed on Railway) via the Letta ADE and API. 👾 ☄️
</Check>

### Adding additional environment variables

To help you get started, when you deploy the template you have the option to fill in the example environment variables `OPENAI_API_KEY` (to connect your Letta agents to GPT models) and `ANTHROPIC_API_KEY` (to connect your Letta agents to Claude models).

There are many more providers you can enable on the Letta server via additional environment variables (for example vLLM, Ollama, etc). For more information on available providers, see [our documentation](/guides/server/docker).

To connect Letta to an additional API provider, you can go to your Railway deployment (after you've deployed the template), click `Variables` to see the current environment variables, then click `+ New Variable` to add a new variable. Once you've saved a new variable, you will need to restart the server for the changes to take effect.

**Examples:**

Example 1 (sh):
```sh
curl --request POST \
  --url https://MYSERVER.up.railway.app/v1/agents/ \
  --header 'X-BARE-PASSWORD: password banana' \
  --header 'Content-Type: application/json' \
  --data '{
  "memory_blocks": [
    {
      "label": "human",
      "value": "The human'\''s name is Bob the Builder"
    },
    {
      "label": "persona",
      "value": "My name is Sam, the all-knowing sentient AI."
    }
  ],
  "llm_config": {
    "model": "gpt-4o-mini",
    "model_endpoint_type": "openai",
    "model_endpoint": "https://api.openai.com/v1",
    "context_window": 16000
  },
  "embedding_config": {
    "embedding_endpoint_type": "openai",
    "embedding_endpoint": "https://api.openai.com/v1",
    "embedding_model": "text-embedding-3-small",
    "embedding_dim": 8191
  }
}'
```

---

## Required for Letta Cloud

**URL:** llms-txt#required-for-letta-cloud

LETTA_API_KEY=your_api_key_here

---

## Self-hosting Letta

**URL:** llms-txt#self-hosting-letta

**Contents:**
- Running the Letta Server
- Enabling model providers

> Learn how to run your own Letta server

<Note>
  The recommended way to use Letta locally is with Docker.
  To install Docker, see [Docker's installation guide](https://docs.docker.com/get-docker/).
  For issues with installing Docker, see [Docker's troubleshooting guide](https://docs.docker.com/desktop/troubleshoot-and-support/troubleshoot/).
  You can also install Letta using `pip`.
</Note>

## Running the Letta Server

You can run a Letta server with Docker (recommended) or pip.

<AccordionGroup>
  <Accordion icon="docker" title="Running with Docker (recommended)" defaultOpen="true">
    To run the server with Docker, run the command:

This will run the Letta server with the OpenAI provider enabled, and store all data in the folder `~/.letta/.persist/pgdata`.

If you have many different LLM API keys, you can also set up a `.env` file instead and pass that to `docker run`:

<Accordion icon="file-code" title="Running with pip">
    You can install the Letta server via `pip` under the `letta` package:

To run the server once installed, simply run the `letta server` command:
    To add LLM API providers, make sure that the environment variables are present in your environment.

Note that the `letta` package only installs the server - if you would like to use the Python SDK (to create and interact with agents on the server in your Python code), then you will also need to install `letta-client` package (see the [quickstart](/quickstart) for an example).
  </Accordion>
</AccordionGroup>

Once the Letta server is running, you can access it via port `8283` (e.g. sending REST API requests to `http://localhost:8283/v1`). You can also connect your server to the [Letta ADE](/guides/ade) to access and manage your agents in a web interface.

## Enabling model providers

The Letta server can be connected to various LLM API backends ([OpenAI](https://docs.letta.com/models/openai), [Anthropic](https://docs.letta.com/models/anthropic), [vLLM](https://docs.letta.com/models/vllm), [Ollama](https://docs.letta.com/models/ollama), etc.). To enable access to these LLM API providers, set the appropriate environment variables when you use `docker run`:

**Examples:**

Example 1 (sh):
```sh
# replace `~/.letta/.persist/pgdata` with wherever you want to store your agent data
    docker run \
      -v ~/.letta/.persist/pgdata:/var/lib/postgresql/data \
      -p 8283:8283 \
      -e OPENAI_API_KEY="your_openai_api_key" \
      letta/letta:latest
```

Example 2 (sh):
```sh
# using a .env file instead of passing environment variables
    docker run \
      -v ~/.letta/.persist/pgdata:/var/lib/postgresql/data \
      -p 8283:8283 \
      --env-file .env \
      letta/letta:latest
```

Example 3 (sh):
```sh
pip install -U letta
```

Example 4 (sh):
```sh
export OPENAI_API_KEY=...
    letta server
```

---
