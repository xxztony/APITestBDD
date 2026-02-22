Feature: API responses can be named and reused
  @api
  Scenario: Create and query CRDS user with multiple response aliases
    Given I clear request context
    Given I use service "crds"
    When I create a CRDS user as "create_user" response
    Then response "create_user" status should be 201
    Then I save response "create_user" field "id" as "user_id"
    Given I set request header "X-User-Id" to "{user_id}"
    When I query the CRDS user as "query_user" response
    Then response "query_user" status should be 200
    Then response "query_user" field "id" should be "{user_id}"
    When I send "GET" request to "/users/{user_id}" with params:
      | field   | value     |
      | user_id | {user_id} |
    Then HTTP status should be 200
