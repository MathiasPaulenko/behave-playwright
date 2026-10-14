Feature: Tabs, frames and dialogs

  Scenario: Work across tabs
    Given I navigate to "/"
    When I open a new tab with "/docs.html"
    Then the title should be "Docs"
    When I switch to tab 1
    Then the title should be "Playground"
    When I close the current tab
    Then the title should be "Docs"

  Scenario: Popup via target=_blank link
    Given I navigate to "/"
    When I click "Open docs" in a new tab
    Then the title should be "Docs"

  Scenario: Steps act inside an iframe
    Given I navigate to "/"
    When I switch to the "widget" iframe
    Then I should see "frame content"
    And the "Frame button" element should be visible
    When I switch back to the main frame
    Then I should see "Playground"

  Scenario: Accept, dismiss and answer dialogs
    Given I navigate to "/"
    When I accept the next dialog
    And I click "Alert"
    When I dismiss the next dialog
    And I click "Confirm"
    Then I should see "cancelled"
    When I answer the next dialog with "42"
    And I click "Prompt"
    Then I should see "42"
