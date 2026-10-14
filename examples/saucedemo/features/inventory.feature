Feature: Product inventory
  Sorting, cart flow and product detail — see custom_steps.py for the
  "I am logged in" setup step composed from bundled steps.

  Background:
    Given I am logged in as the standard user

  Scenario: Products are listed
    Then I should see 6 "css=.inventory_item" elements
    And the "css=.product_sort_container" element should be visible

  Scenario: Sort by price, low to high
    When I select "Price (low to high)" from "css=.product_sort_container"
    Then the "css=.inventory_item_price" element should have text "$7.99"

  Scenario: Add an item to the cart
    When I click "Add to cart"
    Then the "css=.shopping_cart_badge" element should have text "1"
    When I click "css=.shopping_cart_link"
    Then the url should contain "cart"
    And I should see "Sauce Labs Backpack"
    When I click "Remove"
    Then the "css=.shopping_cart_badge" element should not be visible

  Scenario: Product detail page
    When I click "Sauce Labs Backpack"
    Then the url should contain "inventory-item"
    And I should see "$29.99"
