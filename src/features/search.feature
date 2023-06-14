Feature: Tag search
  Author: cmj <cmj@cmj.tw>
  The tag search feature of papyrus

  Background: Load the papyrus instance
    Given load the papyrus settings
    When load the papyrus instance
    Then the papyrus instance should be loaded

  Scenario Outline: Test saerch single tag
    Given generate the random data as VAR with <amount> amount and tag <tag_name>=<tag_value>
    When insert data VAR to the papyrus instance
    Then the data VAR should be exists in the papyrus instance
    And the data VAR should be within the revision in the papyrus instance
    And search tag <tag_name>=<tag_value> and the data VAR primary key should be belongs to the result

    Examples: random tag
      | amount | tag_name | tag_value |
      | 1      | x        | 1         |
      | 4      | y        | 2         |
      | 8      | z        | 3         |
      | 16     | random   | 12345678  |

  Scenario Outline: Test saerch tag non exists
    Given generate the random data as VAR with <amount> amount and tag <tag_name>=<tag_value>
    Then search tag <tag_name>=<tag_value> and the data VAR primary key should not be belongs to the result

    Examples: random tag
      | amount | tag_name | tag_value |
      | 1      | x        | 1         |
      | 4      | y        | 2         |
      | 8      | z        | 3         |
      | 16     | random   | 12345678  |
