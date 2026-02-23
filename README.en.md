# PythonProject (English)

Behave-based test framework for API/UI/system E2E scenarios.

## Quickstart

1. Install dependencies:
```bash
pip install -r requirements.txt
```
2. Run all tests:
```bash
behave
```
3. Run API scenarios only:
```bash
behave --tags @api
```

## API Body Input Patterns

The framework supports three body styles for both HTTP steps and client steps:

1. Flat `field/value` table.
2. Raw JSON payload (docstring).
3. JSON loaded from file.

### HTTP step examples

```gherkin
When I send "POST" request to "/users" with body:
  | field | value |
  | name  | Alice |
  | email | alice@test.com |
```

```gherkin
When I send "POST" request to "/orders" with raw json body
"""
{
  "user_id": "{user_id}",
  "items": [
    {"sku": "SKU-1", "qty": 2},
    {"sku": "SKU-2", "qty": 1}
  ],
  "meta": {"source": "web", "tags": ["vip", "campaign-2024"]}
}
"""
```

```gherkin
When I send "POST" request to "/orders" with body from file "features/data/orders/create_order.json"
```

### Client step examples

```gherkin
When I call "create_user" on "crds_user" client with body:
  | field | value |
  | email | {user_email} |
```

```gherkin
When I call "create_user" on "crds_user" client with raw json body
"""
{"email":"{user_email}","attributes":{"tier":"vip","tags":["new"]}}
"""
```

```gherkin
When I call "create_user" on "crds_user" client with body from file "features/data/crds/create_user.json"
```

### Inline JSON in `field/value`

For nested objects/lists, inline JSON strings are supported in `value`:

```gherkin
When I send "POST" request to "/orders" with body:
  | field   | value                                                            |
  | user_id | {user_id}                                                        |
  | items   | [{"sku":"SKU-1","qty":2},{"sku":"SKU-2","qty":1}]   |
  | meta    | {"source":"web","tags":["vip","campaign-2024"]}       |
```

## Using factory_boy for Complex Payloads

For complex request payloads, use `factory_boy` to compose nested test data in Python, then pass the generated dict/json into Behave steps.

Example:

```python
import factory

class ItemFactory(factory.DictFactory):
    sku = factory.Sequence(lambda n: f"SKU-{n}")
    qty = 1


class OrderPayloadFactory(factory.DictFactory):
    user_id = "u-1001"
    items = factory.LazyFunction(lambda: [ItemFactory(), ItemFactory(qty=2)])
    meta = {"source": "web", "tags": ["vip", "campaign-2024"]}
```

Then serialize and feed the payload to a `with raw json body` step (or write it to a JSON file and use `with body from file`).

Official docs: https://factoryboy.readthedocs.io/en/stable/

## datamodel-code-generator for API Client Codegen

We use `datamodel-code-generator` in our API client generation pipeline:
- Generate typed request/response models from OpenAPI/JSON Schema.
- Build thin API clients on top of generated models + existing `HttpClient`.
- Keep clients in sync with schema changes with repeatable codegen commands.

Example command:

```bash
datamodel-codegen --input openapi.yaml --output src/types/generated_models.py
```

Official docs:
- https://koxudaxi.github.io/datamodel-code-generator/
- https://github.com/koxudaxi/datamodel-code-generator
