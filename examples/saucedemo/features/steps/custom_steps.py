"""Custom steps for the demo — composing bundled steps via execute_steps."""

from behave import given


@given("I am logged in as the standard user")
def step_logged_in_standard_user(context):
    context.execute_steps(
        """
        Given I navigate to "/"
        When I fill "Username" with "standard_user"
        And I fill "Password" with "secret_sauce"
        And I click "Login"
        """
    )
