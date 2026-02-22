# PythonProject

This repository contains Behave-based E2E tests for API and systems.

## Quickstart

1. 安装依赖（建议使用现有 `.venv`）:
   ```bash
   pip install -r requirements.txt
   ```
2. 运行所有用例:
   ```bash
   behave
   ```
3. 仅运行 API 场景:
   ```bash
   behave --tags @api
   ```

## 资源管理与能力型 Tags
- 资源注册表：`context.resources` (ResourceRegistry) 统一管理 api/auth/ui/db/kafka 资源，按场景启用并在 after_scenario 自动回收。
- Tags 触发：
  - `@auth` → TokenManager (resources["auth"], context.token_manager)
  - `@api` → HttpClientFactory + ClientRegistry (resources["api"], context.clients/http_client_factory/systems)
  - `@ui` → driver (resources["ui"], context.ui/driver，禁止放入 shared_data)
  - `@db` → DbClient (resources["db"], context.db_client)
  - `@kafka` → KafkaClient (resources["kafka"], context.kafka_client)
- environment.py 仅调度 hooks；具体初始化在 hooks/resources/*.py，能力映射在 hooks/tag_router.py。

## API 测试使用方法（Behave）

### 核心共享数据
每个场景都会初始化 `context.data` (ScenarioData) 和分区化的 `shared_data`：
- `common.entities` / `common.vars`：业务实体与字符串变量，可在 API 与 UI 间共享。
- `api.responses`：按 alias 存储 HTTP 响应，默认 alias=`last`。
- UI driver/session **禁止**存放在 shared_data，放在 `context.ui` 等专用位置。

### 基础配置 Steps
```gherkin
Given I clear request context
Given I use service "crds"           # 从 config 读取 crds.http.base_url
Given I use base URL "https://api.example.com"   # 直接指定 base_url
Given I set request header "Authorization" to "Bearer {token}"
Given I set query param "locale" to "en_US"
Given I set JSON field "trace_id" to "{trace_id}"
```

### 三类通用 API 调用 Step 示例
1) 纯路径调用
```gherkin
Given I clear request context
Given I use service "crds"
When I send "GET" request to "/users"
Then HTTP status should be 200
```
2) 查询参数 + 命名响应
```gherkin
When I send "GET" request to "/users" with params:
  | field | value |
  | q     | alice |
Then response "last" status should be 200
When I send "GET" request to "/users/{q}" as "detail" response
Then response "detail" status should be 200
```
3) JSON Body + 占位符
```gherkin
Given I set JSON field "email" to "{user_email}"
When I send "POST" request to "/users" with body:
  | field | value        |
  | name  | Alice Smith  |
  | email | {user_email} |
Then HTTP status should be 201
Then I save response "last" field "id" as "user_id"
```
`I send "{method}" request to "{path}" with body:` 适合临时构造 JSON 请求，body 来自 DataTable。

使用封装客户端的 body 版：
```gherkin
When I call "create_user" on "crds_user" client with body:
  | field | value        |
  | email | {user_email} |
Then HTTP status should be 201
```
`I call "{method_name}" on "{client_name}" client with body:` 会把 DataTable 转为 payload/字典后传给指定客户端方法。

### 使用客户端方法（client_steps）
适用于已有封装客户端（如 `context.clients["crds_user"]`）：
```gherkin
When I call "create_user" on "crds_user" client with body:
  | field | value        |
  | email | {user_email} |
Then HTTP status should be 201
When I call "query_user" on "crds_user" client as "user_detail" response
Then response "user_detail" status should be 200
```

### 响应别名与断言
- 默认最近响应写入 `api.responses["last"]`。
- 使用 `as "alias" response` 命名响应：
  ```gherkin
  When I send "GET" request to "/users/{user_id}" as "user_detail" response
  Then response "user_detail" status should be 200
  Then response "user_detail" field "id" should be "{user_id}"
  ```
- 直接断言 last：
  ```gherkin
  Then HTTP status should be 201
  Then response should contain field "id"
  ```

### 变量与占位符
- `{name}` 优先查 `common.entities`，其次 `common.vars`。
- DataTable、路径、headers、body 均自动占位符替换。

### 保存字段到实体/变量
```gherkin
Then I save response "create_user" field "id" as "user_id"
```
写入 `common.entities.user_id` 与 `common.vars.user_id`。

## 示例场景
- `features/examples/resource_tags_demo.feature`：演示 @api @auth tag 触发资源，并断言 resources 内包含 api/auth。
  ```gherkin
  @api @auth
  Scenario: API runtime is wired via tag hooks
    Given I use service "crds"
    When I send "GET" request to "/health"
    Then HTTP status should be 200
    Then resources should include api, auth
  ```
- `features/multi_response_example.feature`：演示多响应 alias、占位符替换与跨调用断言。
