Changelog
=========

0.3.1 (2026-10-20)
------------------

- Add an option to hide the registration ID from customers. It is still
  assigned and visible in the backend and the API.
- Add Dutch translations and complete the German (formal and informal)
  translations.

0.3.0 (2026-10-20)
------------------

- Add an API endpoint to look up the registration ID of an order:
  ``GET /api/v1/organizers/<org>/events/<event>/regid/by-order/<code>/``.
- Add the registration ID as a text variable for ticket and badge layouts.
- Link to the settings from the plugin list.

0.2.1 (2026-10-18)
------------------

- Add an API endpoint to look up an order by registration ID:
  ``GET /api/v1/organizers/<org>/events/<event>/regid/<id>/``. It returns the
  order in the same format as pretix's order endpoint, plus a ``regid`` field.
- Fix the plugin name shown in the pretix marketplace.

0.2.0 (2026-10-18)
------------------

- Fix registration IDs never being assigned. The plugin read different
  settings than the settings page saved.
- Fix two orders placed at the same time getting the same registration ID.
- Allow searching for orders by registration ID in the backend and the API.
- Choose a single moment to assign the registration ID (never, when the order
  is placed, approved or paid) instead of separate checkboxes. Existing
  settings are migrated.
- Clarify that "Set Registration ID on order changed" only assigns an ID to
  orders that don't have one yet.
- Use pretix's new permission names. The settings are only visible to users
  who can change the event settings.
- Requires pretix 2026.3.0 or newer.

0.1.5 and earlier (2022-10-08 to 2023-11-13)
--------------------------------------------

- Assign an automatic registration ID to orders and show it on the customer's
  order page and in the backend.
- Choose which products get a registration ID and when it is assigned.
