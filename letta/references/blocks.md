---
pipeline-status:
  - new
---
# Letta - Blocks

**Pages:** 11

---

## Detach Identity From Block

**URL:** llms-txt#detach-identity-from-block

**Contents:**
- OpenAPI Specification
- SDK Code Examples

PATCH https://api.letta.com/v1/blocks/{block_id}/identities/detach/{identity_id}

Detach an identity from a block.

Reference: https://docs.letta.com/api-reference/blocks/identities/detach

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: Detach Identity From Block
  version: endpoint_blocks/identities.detach
paths:
  /v1/blocks/{block_id}/identities/detach/{identity_id}:
    patch:
      operationId: detach
      summary: Detach Identity From Block
      description: Detach an identity from a block.
      tags:
        - - subpackage_blocks
          - subpackage_blocks/identities
      parameters:
        - name: block_id
          in: path
          required: true
          schema:
            type: string
        - name: identity_id
          in: path
          description: The ID of the block in the format 'block-<uuid4>'
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
          description: Successful Response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BlockResponse'
        '422':
          description: Validation Error
          content: {}
components:
  schemas:
    BlockResponse:
      type: object
      properties:
        value:
          type: string
        limit:
          type: integer
        project_id:
          type:
            - string
            - 'null'
        template_name:
          type:
            - string
            - 'null'
        is_template:
          type: boolean
        template_id:
          type:
            - string
            - 'null'
        base_template_id:
          type:
            - string
            - 'null'
        deployment_id:
          type:
            - string
            - 'null'
        entity_id:
          type:
            - string
            - 'null'
        preserve_on_migration:
          type:
            - boolean
            - 'null'
        label:
          type:
            - string
            - 'null'
        read_only:
          type: boolean
        description:
          type:
            - string
            - 'null'
        metadata:
          type:
            - object
            - 'null'
          additionalProperties:
            description: Any type
        hidden:
          type:
            - boolean
            - 'null'
        id:
          type: string
        created_by_id:
          type:
            - string
            - 'null'
        last_updated_by_id:
          type:
            - string
            - 'null'
      required:
        - value
        - id
```

Example 2 (python):
```python
import requests

url = "https://api.letta.com/v1/blocks/block_id/identities/detach/identity_id"

headers = {"Authorization": "Bearer <token>"}

response = requests.patch(url, headers=headers)

print(response.json())
```

Example 3 (javascript):
```javascript
const url = 'https://api.letta.com/v1/blocks/block_id/identities/detach/identity_id';
const options = {method: 'PATCH', headers: {Authorization: 'Bearer <token>'}};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
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

	url := "https://api.letta.com/v1/blocks/block_id/identities/detach/identity_id"

	req, _ := http.NewRequest("PATCH", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## User Identities

**URL:** llms-txt#user-identities

**Contents:**
- Using Identities
  - Using Agent Tags to Identify Users
- Creating and Viewing Tags in the ADE

You may be building a multi-user application with Letta, in which each user is associated with a specific agent.
In this scenario, you can use **Identities** to associate each agent with a user in your application.

Let's assume that you have an application with multiple users that you're building on a [self-hosted Letta server](/guides/server/docker) or [Letta Cloud](/guides/cloud).
Each user has a unique username, starting at `user_1`, and incrementing up as you add more users to the platform.

To associate agents you create in Letta with your users, you can first create an **Identity** object with the user's unique ID as the `identifier_key` for your user, and then specify the **Identity** object ID when creating an agent.

For example, with `user_1`, we would create a new Identity object with `identifier_key="user_1"` and then pass `identity.id` into our [create agent request](/api-reference/agents/create):

Then, if I wanted to search for agents associated with a specific user (e.g. called `user_id`), I could use the `identifier_keys` parameter in the [list agents request](/api-reference/agents/list):

You can also create an identity object and attach it to an existing agent. This can be useful if you want to enable multiple users to interact with a single agent:

### Using Agent Tags to Identify Users

It's also possible to utilize our agent tags feature to associate agents with specific users. To associate agents you create in Letta with your users, you can specify a tag when creating an agent, and set the tag to the user's unique ID.
This example assumes that you have a self-hosted Letta server running on localhost (for example, by running [`docker run ...`](/guides/server/docker)).

<Accordion title="View example SDK code">
  <CodeGroup>

</CodeGroup>
</Accordion>

## Creating and Viewing Tags in the ADE

You can also modify tags in the ADE.
Simply click the **Advanced Settings** tab in the top-left of the ADE to view an agent's tags.
You can create new tags by typing the tag name in the input field and hitting enter.

<img src="file:5ac62622-f5be-4ceb-be2d-2e99beaedd3e" />

**Examples:**

Example 1 (unknown):
```unknown

```

Example 2 (unknown):
```unknown

```

Example 3 (unknown):
```unknown
</CodeBlocks>

Then, if I wanted to search for agents associated with a specific user (e.g. called `user_id`), I could use the `identifier_keys` parameter in the [list agents request](/api-reference/agents/list):

<CodeBlocks>
```

Example 4 (unknown):
```unknown

```

---

## List Blocks

**URL:** llms-txt#list-blocks

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.letta.com/v1/blocks/

Reference: https://docs.letta.com/api-reference/blocks/list

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: List Blocks
  version: endpoint_blocks.list
paths:
  /v1/blocks/:
    get:
      operationId: list
      summary: List Blocks
      tags:
        - - subpackage_blocks
      parameters:
        - name: label
          in: query
          description: Labels to include (e.g. human, persona)
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: templates_only
          in: query
          description: Whether to include only templates
          required: false
          schema:
            type: boolean
        - name: name
          in: query
          description: Name of the block
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: identity_id
          in: query
          description: Search agents by identifier id
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: identifier_keys
          in: query
          description: Search agents by identifier keys
          required: false
          schema:
            type:
              - array
              - 'null'
            items:
              type: string
        - name: project_id
          in: query
          description: Search blocks by project id
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: limit
          in: query
          description: Number of blocks to return
          required: false
          schema:
            type:
              - integer
              - 'null'
        - name: before
          in: query
          description: >-
            Block ID cursor for pagination. Returns blocks that come before this
            block ID in the specified sort order
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: after
          in: query
          description: >-
            Block ID cursor for pagination. Returns blocks that come after this
            block ID in the specified sort order
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: order
          in: query
          description: >-
            Sort order for blocks by creation time. 'asc' for oldest first,
            'desc' for newest first
          required: false
          schema:
            $ref: '#/components/schemas/V1BlocksGetParametersOrder'
        - name: order_by
          in: query
          description: Field to sort by
          required: false
          schema:
            type: string
            enum:
              - type: stringLiteral
                value: created_at
        - name: label_search
          in: query
          description: >-
            Search blocks by label. If provided, returns blocks that match this
            label. This is a full-text search on labels.
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: description_search
          in: query
          description: >-
            Search blocks by description. If provided, returns blocks that match
            this description. This is a full-text search on block descriptions.
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: value_search
          in: query
          description: >-
            Search blocks by value. If provided, returns blocks that match this
            value.
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: connected_to_agents_count_gt
          in: query
          description: >-
            Filter blocks by the number of connected agents. If provided,
            returns blocks that have more than this number of connected agents.
          required: false
          schema:
            type:
              - integer
              - 'null'
        - name: connected_to_agents_count_lt
          in: query
          description: >-
            Filter blocks by the number of connected agents. If provided,
            returns blocks that have less than this number of connected agents.
          required: false
          schema:
            type:
              - integer
              - 'null'
        - name: connected_to_agents_count_eq
          in: query
          description: >-
            Filter blocks by the exact number of connected agents. If provided,
            returns blocks that have exactly this number of connected agents.
          required: false
          schema:
            type:
              - array
              - 'null'
            items:
              type: integer
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/BlockResponse'
        '422':
          description: Validation Error
          content: {}
components:
  schemas:
    V1BlocksGetParametersOrder:
      type: string
      enum:
        - value: asc
        - value: desc
    BlockResponse:
      type: object
      properties:
        value:
          type: string
        limit:
          type: integer
        project_id:
          type:
            - string
            - 'null'
        template_name:
          type:
            - string
            - 'null'
        is_template:
          type: boolean
        template_id:
          type:
            - string
            - 'null'
        base_template_id:
          type:
            - string
            - 'null'
        deployment_id:
          type:
            - string
            - 'null'
        entity_id:
          type:
            - string
            - 'null'
        preserve_on_migration:
          type:
            - boolean
            - 'null'
        label:
          type:
            - string
            - 'null'
        read_only:
          type: boolean
        description:
          type:
            - string
            - 'null'
        metadata:
          type:
            - object
            - 'null'
          additionalProperties:
            description: Any type
        hidden:
          type:
            - boolean
            - 'null'
        id:
          type: string
        created_by_id:
          type:
            - string
            - 'null'
        last_updated_by_id:
          type:
            - string
            - 'null'
      required:
        - value
        - id
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.blocks.list(
    label="label",
    templates_only=True,
    name="name",
    identity_id="identity_id",
    project_id="project_id",
    limit=1,
    before="before",
    after="after",
    order="asc",
    label_search="label_search",
    description_search="description_search",
    value_search="value_search",
    connected_to_agents_count_gt=1,
    connected_to_agents_count_lt=1,
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.blocks.list({
    label: "label",
    templatesOnly: true,
    name: "name",
    identityId: "identity_id",
    projectId: "project_id",
    limit: 1,
    before: "before",
    after: "after",
    order: "asc",
    orderBy: "created_at",
    labelSearch: "label_search",
    descriptionSearch: "description_search",
    valueSearch: "value_search",
    connectedToAgentsCountGt: 1,
    connectedToAgentsCountLt: 1
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

	url := "https://api.letta.com/v1/blocks/"

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

## Delete Block

**URL:** llms-txt#delete-block

**Contents:**
- OpenAPI Specification
- SDK Code Examples

DELETE https://api.letta.com/v1/blocks/{block_id}

Reference: https://docs.letta.com/api-reference/blocks/delete

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: Delete Block
  version: endpoint_blocks.delete
paths:
  /v1/blocks/{block_id}:
    delete:
      operationId: delete
      summary: Delete Block
      tags:
        - - subpackage_blocks
      parameters:
        - name: block_id
          in: path
          description: The ID of the block in the format 'block-<uuid4>'
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
          description: Successful Response
          content:
            application/json:
              schema:
                description: Any type
        '422':
          description: Validation Error
          content: {}
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.blocks.delete(
    block_id="block-123e4567-e89b-42d3-8456-426614174000",
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.blocks.delete("block-123e4567-e89b-42d3-8456-426614174000");
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

	url := "https://api.letta.com/v1/blocks/block_id"

	req, _ := http.NewRequest("DELETE", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## List Identities

**URL:** llms-txt#list-identities

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.letta.com/v1/identities/

Get a list of all identities in the database

Reference: https://docs.letta.com/api-reference/identities/list

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: List Identities
  version: endpoint_identities.list
paths:
  /v1/identities/:
    get:
      operationId: list
      summary: List Identities
      description: Get a list of all identities in the database
      tags:
        - - subpackage_identities
      parameters:
        - name: name
          in: query
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: project_id
          in: query
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: identifier_key
          in: query
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: identity_type
          in: query
          required: false
          schema:
            oneOf:
              - $ref: '#/components/schemas/IdentityType'
              - type: 'null'
        - name: before
          in: query
          description: >-
            Identity ID cursor for pagination. Returns identities that come
            before this identity ID in the specified sort order
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: after
          in: query
          description: >-
            Identity ID cursor for pagination. Returns identities that come
            after this identity ID in the specified sort order
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: limit
          in: query
          description: Maximum number of identities to return
          required: false
          schema:
            type:
              - integer
              - 'null'
        - name: order
          in: query
          description: >-
            Sort order for identities by creation time. 'asc' for oldest first,
            'desc' for newest first
          required: false
          schema:
            $ref: '#/components/schemas/V1IdentitiesGetParametersOrder'
        - name: order_by
          in: query
          description: Field to sort by
          required: false
          schema:
            type: string
            enum:
              - type: stringLiteral
                value: created_at
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Identity'
        '422':
          description: Validation Error
          content: {}
components:
  schemas:
    IdentityType:
      type: string
      enum:
        - value: org
        - value: user
        - value: other
    V1IdentitiesGetParametersOrder:
      type: string
      enum:
        - value: asc
        - value: desc
    IdentityPropertyValue:
      oneOf:
        - type: string
        - type: integer
        - type: number
          format: double
        - type: boolean
        - type: object
          additionalProperties:
            description: Any type
    IdentityPropertyType:
      type: string
      enum:
        - value: string
        - value: number
        - value: boolean
        - value: json
    IdentityProperty:
      type: object
      properties:
        key:
          type: string
        value:
          $ref: '#/components/schemas/IdentityPropertyValue'
        type:
          $ref: '#/components/schemas/IdentityPropertyType'
      required:
        - key
        - value
        - type
    Identity:
      type: object
      properties:
        id:
          type: string
        identifier_key:
          type: string
        name:
          type: string
        identity_type:
          $ref: '#/components/schemas/IdentityType'
        project_id:
          type:
            - string
            - 'null'
        agent_ids:
          type: array
          items:
            type: string
        block_ids:
          type: array
          items:
            type: string
        properties:
          type: array
          items:
            $ref: '#/components/schemas/IdentityProperty'
      required:
        - identifier_key
        - name
        - identity_type
        - agent_ids
        - block_ids
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.identities.list(
    name="name",
    project_id="project_id",
    identifier_key="identifier_key",
    identity_type="org",
    before="before",
    after="after",
    limit=1,
    order="asc",
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.identities.list({
    name: "name",
    projectId: "project_id",
    identifierKey: "identifier_key",
    identityType: "org",
    before: "before",
    after: "after",
    limit: 1,
    order: "asc",
    orderBy: "created_at"
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

	url := "https://api.letta.com/v1/identities/"

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

## Attach Block To Group

**URL:** llms-txt#attach-block-to-group

**Contents:**
- OpenAPI Specification
- SDK Code Examples

PATCH https://api.letta.com/v1/groups/{group_id}/blocks/attach/{block_id}

Attach a block to a group.
This will add the block to the group and all agents within the group.

Reference: https://docs.letta.com/api-reference/groups/attach-block-to-group

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: Attach Block To Group
  version: endpoint_groups.attach_block_to_group
paths:
  /v1/groups/{group_id}/blocks/attach/{block_id}:
    patch:
      operationId: attach-block-to-group
      summary: Attach Block To Group
      description: |-
        Attach a block to a group.
        This will add the block to the group and all agents within the group.
      tags:
        - - subpackage_groups
      parameters:
        - name: block_id
          in: path
          required: true
          schema:
            type: string
        - name: group_id
          in: path
          description: The ID of the group in the format 'group-<uuid4>'
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
          description: Successful Response
          content:
            application/json:
              schema:
                description: Any type
        '422':
          description: Validation Error
          content: {}
```

Example 2 (python):
```python
import requests

url = "https://api.letta.com/v1/groups/group_id/blocks/attach/block_id"

headers = {"Authorization": "Bearer <token>"}

response = requests.patch(url, headers=headers)

print(response.json())
```

Example 3 (javascript):
```javascript
const url = 'https://api.letta.com/v1/groups/group_id/blocks/attach/block_id';
const options = {method: 'PATCH', headers: {Authorization: 'Bearer <token>'}};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
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

	url := "https://api.letta.com/v1/groups/group_id/blocks/attach/block_id"

	req, _ := http.NewRequest("PATCH", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## Detach Block From Group

**URL:** llms-txt#detach-block-from-group

**Contents:**
- OpenAPI Specification
- SDK Code Examples

PATCH https://api.letta.com/v1/groups/{group_id}/blocks/detach/{block_id}

Detach a block from a group.
This will remove the block from the group and all agents within the group.

Reference: https://docs.letta.com/api-reference/groups/detach-block-from-group

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: Detach Block From Group
  version: endpoint_groups.detach_block_from_group
paths:
  /v1/groups/{group_id}/blocks/detach/{block_id}:
    patch:
      operationId: detach-block-from-group
      summary: Detach Block From Group
      description: >-
        Detach a block from a group.

        This will remove the block from the group and all agents within the
        group.
      tags:
        - - subpackage_groups
      parameters:
        - name: block_id
          in: path
          required: true
          schema:
            type: string
        - name: group_id
          in: path
          description: The ID of the group in the format 'group-<uuid4>'
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
          description: Successful Response
          content:
            application/json:
              schema:
                description: Any type
        '422':
          description: Validation Error
          content: {}
```

Example 2 (python):
```python
import requests

url = "https://api.letta.com/v1/groups/group_id/blocks/detach/block_id"

headers = {"Authorization": "Bearer <token>"}

response = requests.patch(url, headers=headers)

print(response.json())
```

Example 3 (javascript):
```javascript
const url = 'https://api.letta.com/v1/groups/group_id/blocks/detach/block_id';
const options = {method: 'PATCH', headers: {Authorization: 'Bearer <token>'}};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
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

	url := "https://api.letta.com/v1/groups/group_id/blocks/detach/block_id"

	req, _ := http.NewRequest("PATCH", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## Exit code 1 = fail (block deployment)

**URL:** llms-txt#exit-code-1-=-fail-(block-deployment)

**Contents:**
  - What Happens When Gates Fail?
- Required Fields
  - metric\_key
  - metric
  - op
  - value
- Optional Fields
  - pass\_op and pass\_value
- Examples
  - Require 80% Average Score

yaml
gate:
  metric: avg_score
  op: gte
  value: 0.85  # Must maintain 85%+ to pass
yaml
gate:
  metric: accuracy
  op: gte
  value: 0.95  # 95% of test cases must pass
text
   ✗ FAILED (0.72/1.00 avg, 72.0% pass rate)
   Gate check failed: avg_score (0.72) not >= 0.80
   bash
   letta-evals run suite.yaml
   echo $?  # Prints 1 if gate failed
   json
   {
     "gate_passed": false,
     "gate_check": {
       "metric": "avg_score",
       "value": 0.72,
       "threshold": 0.80,
       "operator": "gte",
       "passed": false
     },
     "metrics": { ... }
   }
   bash
  #!/bin/bash
  letta-evals run suite.yaml --output results.json

if [ $? -ne 0 ]; then
    echo "❌ Agent evaluation failed - blocking merge"
    exit 1
  else
    echo "✅ Agent evaluation passed - safe to merge"
  fi
  yaml
graders:
  accuracy:  # Grader name
    kind: tool
    function: exact_match
    extractor: last_assistant

gate:
  metric_key: accuracy  # Must match grader name above
  op: gte  # >=
  value: 0.8  # 80% threshold
yaml
gate:
  metric_key: quality  # Check quality grader
  metric: avg_score  # Use average of all scores
  op: gte  # >=
  value: 0.7  # Must average 70%+
yaml
gate:
  metric_key: accuracy  # Check accuracy grader
  metric: accuracy  # Use pass rate, not average
  op: gte  # >=
  value: 0.8  # 80% of samples must pass
yaml
  gate:
    metric_key: quality  # Check quality grader
    op: gte  # >=
    value: 0.7  # 70% threshold (defaults to avg_score)
  yaml
gate:
  metric: avg_score  # Average score
  op: gte  # >=
  value: 0.75  # 75% threshold
yaml
gate:
  metric: accuracy  # Pass rate
  op: gte  # >=
  value: 0.9  # 90% must pass
yaml
gate:
  metric_key: quality  # Check quality grader
  metric: accuracy  # Use pass rate
  op: gte  # >=
  value: 0.8  # 80% must pass
  pass_op: gte  # Sample passes if >=
  pass_value: 0.7  # This threshold (70%)
yaml
gate:
  metric_key: quality  # Check quality grader
  metric: avg_score  # Use average
  op: gte  # >=
  value: 0.8  # 80% average
yaml
gate:
  metric_key: accuracy  # Check accuracy grader
  metric: accuracy  # Use pass rate
  op: gte  # >=
  value: 0.9  # 90% must pass (default: score >= 1.0 to pass)
yaml
gate:
  metric_key: quality  # Check quality grader
  metric: accuracy  # Use pass rate
  op: gte  # >=
  value: 0.75  # 75% must pass
  pass_op: gte  # Sample passes if >=
  pass_value: 0.7  # 70% threshold per sample
yaml
gate:
  metric_key: quality  # Check quality grader
  metric: accuracy  # Use pass rate
  op: gte  # >=
  value: 0.95  # 95% must pass (allows 5% failures)
  pass_op: gt  # Sample passes if >
  pass_value: 0.0  # 0.0 (any non-zero score)
yaml
gate:
  metric_key: quality  # Check quality grader
  metric: accuracy  # Use pass rate
  op: eq  # Exactly equal
  value: 1.0  # 100% (all samples must pass)
yaml
graders:
  accuracy:  # First metric
    kind: tool
    function: exact_match
    extractor: last_assistant

completeness:  # Second metric
    kind: rubric
    prompt_path: completeness.txt
    model: gpt-4o-mini
    extractor: last_assistant

gate:
  metric_key: accuracy  # Only gate on accuracy (completeness still computed)
  metric: avg_score  # Use average
  op: gte  # >=
  value: 0.8  # 80% threshold
text
✓ PASSED (2.25/3.00 avg, 75.0% pass rate)
text
✗ FAILED (1.80/3.00 avg, 60.0% pass rate)
```

The evaluation exit code reflects the gate result:

* 0: Passed
* 1: Failed

For complex gating logic (e.g., "pass if accuracy `>= 80%` OR avg\_score `>= 0.9`"), you'll need to:

1. Run evaluation with one gate
2. Examine the results JSON
3. Apply custom logic in a post-processing script

* [Understanding Results](/evals/results-metrics/understanding-results) - Interpreting evaluation output
* [Multi-Metric Evaluation](/evals/graders/multi-metric-grading) - Using multiple graders
* [Suite YAML Reference](/evals/configuration/suite-yaml-reference) - Complete gate configuration

**Examples:**

Example 1 (unknown):
```unknown
**Regression Testing**: Set a baseline threshold and ensure new changes don't degrade performance:
```

Example 2 (unknown):
```unknown
**Quality Enforcement**: Require agents meet minimum standards before production:
```

Example 3 (unknown):
```unknown
### What Happens When Gates Fail?

When a gate condition is not met:

1. **Console output** shows failure message:
```

Example 4 (unknown):
```unknown
2. **Exit code** is 1 (non-zero indicates failure):
```

---

## Attach Identity To Block

**URL:** llms-txt#attach-identity-to-block

**Contents:**
- OpenAPI Specification
- SDK Code Examples

PATCH https://api.letta.com/v1/blocks/{block_id}/identities/attach/{identity_id}

Attach an identity to a block.

Reference: https://docs.letta.com/api-reference/blocks/identities/attach

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: Attach Identity To Block
  version: endpoint_blocks/identities.attach
paths:
  /v1/blocks/{block_id}/identities/attach/{identity_id}:
    patch:
      operationId: attach
      summary: Attach Identity To Block
      description: Attach an identity to a block.
      tags:
        - - subpackage_blocks
          - subpackage_blocks/identities
      parameters:
        - name: block_id
          in: path
          required: true
          schema:
            type: string
        - name: identity_id
          in: path
          description: The ID of the block in the format 'block-<uuid4>'
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
          description: Successful Response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BlockResponse'
        '422':
          description: Validation Error
          content: {}
components:
  schemas:
    BlockResponse:
      type: object
      properties:
        value:
          type: string
        limit:
          type: integer
        project_id:
          type:
            - string
            - 'null'
        template_name:
          type:
            - string
            - 'null'
        is_template:
          type: boolean
        template_id:
          type:
            - string
            - 'null'
        base_template_id:
          type:
            - string
            - 'null'
        deployment_id:
          type:
            - string
            - 'null'
        entity_id:
          type:
            - string
            - 'null'
        preserve_on_migration:
          type:
            - boolean
            - 'null'
        label:
          type:
            - string
            - 'null'
        read_only:
          type: boolean
        description:
          type:
            - string
            - 'null'
        metadata:
          type:
            - object
            - 'null'
          additionalProperties:
            description: Any type
        hidden:
          type:
            - boolean
            - 'null'
        id:
          type: string
        created_by_id:
          type:
            - string
            - 'null'
        last_updated_by_id:
          type:
            - string
            - 'null'
      required:
        - value
        - id
```

Example 2 (python):
```python
import requests

url = "https://api.letta.com/v1/blocks/block_id/identities/attach/identity_id"

headers = {"Authorization": "Bearer <token>"}

response = requests.patch(url, headers=headers)

print(response.json())
```

Example 3 (javascript):
```javascript
const url = 'https://api.letta.com/v1/blocks/block_id/identities/attach/identity_id';
const options = {method: 'PATCH', headers: {Authorization: 'Bearer <token>'}};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
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

	url := "https://api.letta.com/v1/blocks/block_id/identities/attach/identity_id"

	req, _ := http.NewRequest("PATCH", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## Docker example

**URL:** llms-txt#docker-example

**Contents:**
- When to Use Web Search
- Related Documentation

docker run -e EXA_API_KEY="your_exa_api_key" letta/letta:latest
```

## When to Use Web Search

| Use Case             | Tool              | Why                   |
| -------------------- | ----------------- | --------------------- |
| Current events, news | `web_search`      | Real-time information |
| External research    | `web_search`      | Broad internet access |
| Internal documents   | Archival memory   | Fast, static data     |
| User preferences     | Memory blocks     | In-context, instant   |
| General knowledge    | Pre-trained model | No search needed      |

## Related Documentation

* [Utilities Overview](/guides/agents/prebuilt-tools)
* [Custom Tools](/guides/agents/custom-tools)
* [Tool Variables](/guides/agents/tool-variables)
* [Archival Memory](/guides/agents/archival-memory-overview)

---

## List Blocks For Identity

**URL:** llms-txt#list-blocks-for-identity

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.letta.com/v1/identities/{identity_id}/blocks

Get all blocks associated with the specified identity.

Reference: https://docs.letta.com/api-reference/identities/blocks/list

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: List Blocks For Identity
  version: endpoint_identities/blocks.list
paths:
  /v1/identities/{identity_id}/blocks:
    get:
      operationId: list
      summary: List Blocks For Identity
      description: Get all blocks associated with the specified identity.
      tags:
        - - subpackage_identities
          - subpackage_identities/blocks
      parameters:
        - name: identity_id
          in: path
          description: The ID of the identity in the format 'identity-<uuid4>'
          required: true
          schema:
            type: string
        - name: before
          in: query
          description: >-
            Block ID cursor for pagination. Returns blocks that come before this
            block ID in the specified sort order
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: after
          in: query
          description: >-
            Block ID cursor for pagination. Returns blocks that come after this
            block ID in the specified sort order
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: limit
          in: query
          description: Maximum number of blocks to return
          required: false
          schema:
            type:
              - integer
              - 'null'
        - name: order
          in: query
          description: >-
            Sort order for blocks by creation time. 'asc' for oldest first,
            'desc' for newest first
          required: false
          schema:
            $ref: >-
              #/components/schemas/V1IdentitiesIdentityIdBlocksGetParametersOrder
        - name: order_by
          in: query
          description: Field to sort by
          required: false
          schema:
            type: string
            enum:
              - type: stringLiteral
                value: created_at
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/BlockResponse'
        '422':
          description: Validation Error
          content: {}
components:
  schemas:
    V1IdentitiesIdentityIdBlocksGetParametersOrder:
      type: string
      enum:
        - value: asc
        - value: desc
    BlockResponse:
      type: object
      properties:
        value:
          type: string
        limit:
          type: integer
        project_id:
          type:
            - string
            - 'null'
        template_name:
          type:
            - string
            - 'null'
        is_template:
          type: boolean
        template_id:
          type:
            - string
            - 'null'
        base_template_id:
          type:
            - string
            - 'null'
        deployment_id:
          type:
            - string
            - 'null'
        entity_id:
          type:
            - string
            - 'null'
        preserve_on_migration:
          type:
            - boolean
            - 'null'
        label:
          type:
            - string
            - 'null'
        read_only:
          type: boolean
        description:
          type:
            - string
            - 'null'
        metadata:
          type:
            - object
            - 'null'
          additionalProperties:
            description: Any type
        hidden:
          type:
            - boolean
            - 'null'
        id:
          type: string
        created_by_id:
          type:
            - string
            - 'null'
        last_updated_by_id:
          type:
            - string
            - 'null'
      required:
        - value
        - id
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.identities.blocks.list(
    identity_id="identity-123e4567-e89b-42d3-8456-426614174000",
    before="before",
    after="after",
    limit=1,
    order="asc",
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.identities.blocks.list("identity-123e4567-e89b-42d3-8456-426614174000", {
    before: "before",
    after: "after",
    limit: 1,
    order: "asc",
    orderBy: "created_at"
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

	url := "https://api.letta.com/v1/identities/identity_id/blocks"

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
