@api @crds
Feature: CRDS User Lifecycle (Client-Aware)

  Background:
    Given I am authenticated as "crds"

  Scenario: Manage CRDS user via client-aware API
    When I call "create_user" on "crds_user" client with body:
      | username | tony |
      | email    | tony@example.com |
    And I call "get_user" on "crds_user" client with params:
      | user_id | <from previous step> |
    And I call "delete_user" on "crds_user" client with params:
      | user_id | <from previous step> |
    Then HTTP status should be one of "200,204"
