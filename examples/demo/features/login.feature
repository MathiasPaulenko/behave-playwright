Feature: Login
  The demo app's sign-in flow, covered only with bundled steps.

  Scenario: Successful login
    Given I navigate to "index.html"
    When I fill "Email" with "ada@example.com"
    And I fill "Password" with "secret"
    And I click "Sign in"
    Then I should see "Welcome back"

  Scenario: Login requires email and password
    Given I navigate to "index.html"
    When I click "Sign in"
    Then I should see "Invalid credentials"
    And the "css=#error" element should be visible
