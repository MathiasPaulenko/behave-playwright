@wip
Feature: behave-playwright dogfooding example

  Scenario: Navigate and interact
    Given I navigate to "/"
    When I fill "Email" with "user@test.com"
    And I click "Sign in"
    Then I should see "Welcome back"
