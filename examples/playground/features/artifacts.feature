@wip
Feature: Failure artifacts
  Excluded by default. Run with:
    behave --tags=@wip -D record_video=true
  Produces a screenshot, a Playwright trace and a video in their dirs.

  Scenario: Deliberate failure captures everything
    When I enable tracing
    And I navigate to "/"
    Then I should see "this text does not exist"
