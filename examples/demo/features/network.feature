Feature: Network mocking
  Playwright-exclusive steps: intercept and request assertions.

  Scenario: Todos served from a mocked API
    Given I intercept "**/api/todos" and return:
      """
      ["Mocked todo", "Intercepted by page.route"]
      """
    When I navigate to "index.html"
    And I fill "Email" with "ada@example.com"
    And I fill "Password" with "secret"
    And I click "Sign in"
    Then I should see "Mocked todo"
    And I should see "Intercepted by page.route"
    And I should not see "Write tests"
    And a "GET" request was made to "**/api/todos"
