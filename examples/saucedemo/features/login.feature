Feature: Login
  The classic swag labs login — covered only with bundled steps.
  Fields are matched by placeholder, the button by role + name.

  Scenario: Standard user logs in
    Given I navigate to "/"
    When I fill "Username" with "standard_user"
    And I fill "Password" with "secret_sauce"
    And I click "Login"
    Then the url should contain "inventory"
    And I should see "Products"

  Scenario: Locked out user sees an error
    Given I navigate to "/"
    When I fill "Username" with "locked_out_user"
    And I fill "Password" with "secret_sauce"
    And I click "Login"
    Then I should see "Sorry, this user has been locked out"
    And the "css=[data-test='error']" element should be visible
