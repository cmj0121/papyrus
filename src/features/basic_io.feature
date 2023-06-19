Feature: Basic I/O
  Author: cmj <cmj@cmj.tw>
  General I/O for the Papyrus library.
  Load the instance from the exists config and then test the basic I/O.

  Background: Load the papyrus instance
    Given load the papyrus settings
    When load the papyrus instance
    Then the papyrus instance should be loaded

  Scenario Outline: Test Insert Latest and Revision
    Given generate the random data as VAR with <amount> amount
    When insert data VAR to the papyrus instance
    Then the data VAR should be exists in the papyrus instance

    Examples: random data amount
      | amount |
      | 1      |
      | 16     |

  Scenario Outline: Test Delete
    Given generate the random data as VAR with <amount> amount
    When insert data VAR to the papyrus instance
    And delete key from data VAR on the papyrus instance
    Then the data VAR should not be exists in the papyrus instance

    Examples: random data amount
      | amount |
      | 1      |
      | 16     |
