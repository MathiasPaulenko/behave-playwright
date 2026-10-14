Feature: Sessions, storage state, devices, console and cookies

  Scenario: No session means forbidden
    Given I navigate to "/dashboard.html"
    Then I should see "Forbidden"

  Scenario: Save and restore a session
    Given I navigate to "/"
    When I click "Log me in"
    When I save the storage state to "auth/tester.json"
    And I use the storage state "auth/tester.json"
    And I navigate to "/dashboard.html"
    Then I should see "Secret area"

  Scenario: Pre-stored identity via convention
    Given I am logged in as "admin"
    When I navigate to "/dashboard.html"
    Then I should see "Secret area"

  Scenario: Device emulation
    Given I emulate device "iPhone 12"
    When I navigate to "/"
    Then the "css=h1" element should be visible

  Scenario: Cookie assertions
    Given I navigate to "/"
    When I click "Log me in"
    Then the "session" cookie should exist
    And the "session" cookie should have value "abc123"

  Scenario: A clean page has no console errors
    Given I navigate to "/"
    Then there should be no console errors

  Scenario: Known console noise can be ignored
    Given I navigate to "/"
    When I click "Break console"
    Then there should be no console errors except "boom.*"
