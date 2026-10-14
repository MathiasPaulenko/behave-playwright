Feature: File upload and download

  Scenario: Upload a file
    Given I navigate to "/"
    When I upload the file "features/fixtures/hello.txt" to "css=#upload"
    Then I should see "hello.txt"

  Scenario: Download a file
    Given I navigate to "/"
    When I click "Download report" and download the file
    Then the file "report.txt" was downloaded
