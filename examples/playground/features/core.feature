Feature: Core interaction
  Forms, clicks, fields and assertions — all resolved through the locator
  cascade (labels, placeholders, roles, text, css).

  Scenario: Fill, submit and assert
    Given I navigate to "/"
    When I fill "Email" with "ada@lovelace.dev"
    And I fill "Password" with "s3cret"
    And I type "Ada" in "Pick a nick"
    And I select "Banana" from "Fruit"
    And I check "Accept terms"
    And I press "Enter" on "Pick a nick"
    Then I should see "Form sent for ada@lovelace.dev"
    And the url should contain "127.0.0.1"
    And the title should be "Playground"
    And the title should contain "Play"
    And the "css=#disabled" element should be disabled
    And the "css=#btn" element should be enabled
    And the "Accept terms" element should be checked

  Scenario: Fill the form from a data table
    Given I navigate to "/"
    When I fill the form:
      | field    | value            |
      | Email    | grace@hopper.dev |
      | Password | cobalt           |
    And I click "Sign in"
    Then I should see "Form sent for grace@hopper.dev"

  Scenario: Keyboard press on the focused field
    Given I navigate to "/"
    When I fill "Email" with "key@board.dev"
    And I fill "Password" with "x"
    And I press the "Enter" key
    Then I should see "Form sent for key@board.dev"

  Scenario: Click, double click and hover
    Given I navigate to "/"
    When I click "Click me"
    Then I should see "Clicked!"
    When I double click "Double me"
    Then I should see "Double clicked!"
    When I hover over "Hover me"
    Then I should see "Hovered!"

  Scenario: Text, count, attribute and value assertions
    Given I navigate to "/"
    Then I should see 3 "css=#items li" elements
    And the "css=#items" element should contain "Item two"
    And the "css=h1" element should have text "Playground"
    And the "css=#btn" element should have attribute "id" with value "btn"
    And the "css=#ghost" element should be hidden
    When I fill "Email" with "check@me.dev"
    Then the "Email" field should have value "check@me.dev"
    And I should not see "no such text"

  Scenario: Scroll, drag and explicit waits
    Given I navigate to "/"
    When I scroll to "css=#bottom"
    Then the "css=#bottom" element should be visible
    When I drag "css=#src" to "css=#zone"
    Then I should see "Dropped!"
    When I wait for the "css=#items li" element
    And I wait for the page to load
    And I wait 0.1 seconds

  Scenario: Manual screenshots
    Given I navigate to "/"
    When I take a screenshot
    And I take a screenshot of "css=#form"

  Scenario: Back, forward and reload
    Given I navigate to "/"
    And I navigate to "/docs.html"
    Then the title should be "Docs"
    When I go back
    Then the title should be "Playground"
    When I go forward
    Then the title should be "Docs"
    When I reload the page
    Then the title should be "Docs"
