Feature: Todo list
  The demo app falls back to built-in todos when no API is reachable.

  Background:
    Given I navigate to "index.html"
    When I fill "Email" with "ada@example.com"
    And I fill "Password" with "secret"
    And I click "Sign in"

  Scenario: Default todos are shown
    Then I should see "Write tests"
    And I should see "2 items left"

  Scenario: Add and complete a todo
    When I fill "New todo" with "Read the changelog"
    And I click "Add"
    Then I should see "Read the changelog"
    And I should see "3 items left"
    When I check "Read the changelog"
    Then I should see "2 items left"
