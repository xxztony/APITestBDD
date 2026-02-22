Feature: Resource tag router demo
  # 注意：需要 crds.http.base_url 指向可访问的本地/测试环境服务；无可用服务时可暂时跳过本场景。
  @api @auth
  Scenario: API call with shared_data context
    Given I use service "crds"
    When I send "GET" request to "/health"
    Then HTTP status should be 200
    Then resources should include api, auth
