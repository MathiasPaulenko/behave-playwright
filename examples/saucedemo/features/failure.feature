@wip
Feature: Failure artifacts
  Excluded by default (see behave.ini). Run with `behave --tags=@wip`:
  the scenario fails and a screenshot lands in screenshots/.

  Scenario: Deliberate failure
    Given I navigate to "/"
    Then I should see "This text does not exist"
