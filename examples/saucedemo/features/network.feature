Feature: Network
  Playwright-exclusive steps on a real site. Saucedemo is an SPA, so
  navigation after login is client-side — captured requests are static
  assets and telemetry, which is what these scenarios assert.

  Scenario: Mock a whole page
    Given I intercept "**/inventory.html" and return:
      """
      <html><body><h1>Mocked inventory</h1></body></html>
      """
    When I navigate to "/inventory.html"
    Then I should see "Mocked inventory"

  Scenario: Requests are captured per scenario
    Given I am logged in as the standard user
    Then a "GET" request was made to "**/assets/*.js"
    And a "GET" request was made to "**/assets/*.css"

  Scenario: Telemetry requests can be blocked
    Given I intercept "**/events.backtrace.io/**" and abort
    And I am logged in as the standard user
    Then a request was made to "**/events.backtrace.io/**"
