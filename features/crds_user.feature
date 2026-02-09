Feature: CRDS User API

  Background:
    Given I am authenticated as CRDS user

  Scenario: Create CRDS user with custom attributes
    When I create a CRDS user with attributes as "create_user" response:
      | risk_level | HIGH |
      | country    | US   |
      | name       | VIP  |
    Then HTTP status should be 201
    And response should contain field "id"
