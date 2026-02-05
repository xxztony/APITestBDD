@api @crds
Feature: CRDS User Lifecycle (System-Based)

  Background:
    Given I am authenticated as "crds"

  Scenario: Manage CRDS user lifecycle
    When I create a CRDS user
    And I query the CRDS user
    And I delete the CRDS user
    Then HTTP status should be one of "200,204"
