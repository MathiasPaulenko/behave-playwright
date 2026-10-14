Feature: Network interception and request assertions

  Scenario: Mocked API data
    Given I intercept "**/api/items" and return:
      """
      ["Mocked alpha", "Mocked beta"]
      """
    When I navigate to "/"
    Then I should see "Mocked alpha"
    And I should see 2 "css=#items li" elements
    And a "GET" request was made to "**/api/items"

  Scenario: Aborted request shows the error state
    Given I intercept "**/api/items" and abort
    When I navigate to "/"
    Then I should see "Could not load items"

  Scenario: Custom status code
    Given I intercept "**/api/items" and respond with status 503
    When I navigate to "/"
    Then I should see "Could not load items"

  Scenario: POST request assertion
    Given I navigate to "/"
    When I fill "Email" with "a@b.c"
    And I fill "Password" with "x"
    And I click "Sign in"
    Then a "POST" request was made to "**/api/submit"
