Feature: Basic I/O
  Author: cmj <cmj@cmj.tw>
  General I/O for the Papyrus library.
  Load the instance from the exists config and then test the basic I/O.

  Background: Load the papyrus instance
    Given load the papyrus settings
    When load the papyrus instance
    Then the papyrus instance should be loaded

  Scenario: Test Insert Latest and Revision
    Given generate the random data as VAR_CASE_1
    When insert data VAR_CASE_1 to the papyrus instance
    Then the data VAR_CASE_1 should be exists in the papyrus instance
    And the data VAR_CASE_1 should be within the revision in the papyrus instance

  Scenario: Test Insert Latest and Revision
    Given generate the random data as VAR_CASE_2
    When insert data VAR_CASE_2 to the papyrus instance
    And delete key from data VAR_CASE_2 on the papyrus instance
    Then the data VAR_CASE_2 should not be exists in the papyrus instance
    And the data VAR_CASE_2 should be within the revision in the papyrus instance
