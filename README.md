# behave-playwright

BDD web testing with [Behave](https://behave.readthedocs.io/) and [Playwright](https://playwright.dev/python/) — reusable Gherkin step definitions and browser lifecycle hooks, no boilerplate.

```gherkin
Feature: Login
  Scenario: Successful login
    Given I navigate to "/login"
    When I fill "Email" with "user@test.com"
    And I fill "Password" with "secret"
    And I click "Sign in"
    Then I should see "Welcome back"
```

## Status

Work in progress — first release coming soon.

## Install

```bash
pip install behave-playwright
playwright install
```

## License

MIT
