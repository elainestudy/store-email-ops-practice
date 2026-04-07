Feature: Campaign sending
  Internal operators can send campaigns asynchronously and inspect the results.

  Scenario: Creating a campaign stores it as a draft
    Given a valid campaign creation request
    When the operator creates the campaign
    Then the response status code is 201
    And the created campaign status is "draft"
    And the created campaign name is "Spring Member Event"

  Scenario: Sending a campaign records delivery attempts and audit logs
    Given an existing campaign with valid and invalid recipients
    When the operator sends the campaign
    And the async worker processes the queued send request
    Then the campaign status becomes "partially_failed"
    And 2 delivery attempts are recorded
    And the audit log contains 3 entries
    And at least 1 delivery attempt has status "sent"
    And at least 1 delivery attempt has status "failed"
