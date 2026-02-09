@api @crds
Feature: CRDS User Lifecycle (System-Based)

  Background:
    Given I am authenticated as "crds"
    And I use service "crds"

  Scenario: Manage CRDS user lifecycle
    When I send "POST" request to "/users" with body:
      | field        | value                |
      | username     | e2e_user             |
      | email        | e2e_user@example.com |
      | status       | ACTIVE               |
      | display_name | E2E User             |
    Then HTTP status should be 201
    And response should contain field "id"
    And I store response field "id" as "user_id"
    When I send "GET" request to "/users/{user_id}"
    Then HTTP status should be 200
    When I send "DELETE" request to "/users/{user_id}"
    Then HTTP status should be one of "200,204"
