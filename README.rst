Registration ID
==========================

This is a plugin for `pretix`_. 

Adds an automatic, sequential registration ID (1, 2, 3, ...) to orders. The ID is shown on the order page in the
backend and to the customer.

Configure it under *Settings → Registration ID* in your event:

* Select the products that should get a registration ID. Orders that contain none of them don't get one.
* Choose when the ID is assigned: when the order is placed, approved or paid. You can additionally have it assigned
  when an order is changed.

Nothing is assigned until at least one product and a moment to assign it are selected. Orders placed before the plugin was
configured don't get a registration ID retroactively.

REST API
--------

Look up an order by its registration ID::

    GET /api/v1/organizers/<organizer>/events/<event>/regid/<registration ID>/

The response is the same as pretix's ``GET .../orders/<code>/`` (including positions with their question answers),
with an additional ``regid`` field. The ``include`` and ``exclude`` query parameters of the order endpoint work here
too. It requires the "view orders" permission and works with team API tokens, OAuth and devices with full device
access. Devices with a pretixSCAN security profile are not allowed to use it.

Look up the registration ID of an order by its order code::

    GET /api/v1/organizers/<organizer>/events/<event>/regid/by-order/<order code>/

This returns ``{"order": "<order code>", "regid": 42}``, or ``"regid": null`` if the order has no registration ID.
Unknown order codes return 404. The same permissions apply as above.

To install:
``pip3 install pretix-regid && python3 -m pretix migrate && python3 -m pretix rebuild && service pretix-web restart``

Then just activate it in your event config.

Development setup
-----------------

1. Make sure that you have a working `pretix development setup`_.

2. Clone this repository.

3. Activate the virtual environment you use for pretix development.

4. Execute ``pip3 install -e .`` within this directory to register this application with pretix's plugin registry.

5. Execute ``make`` within this directory to compile translations.

6. Restart your local pretix server. You can now use the plugin from this repository for your events by enabling it in
   the 'plugins' tab in the settings.

This plugin has CI set up to enforce a few code style rules. To check locally, you need these packages installed::

    pip install flake8 isort black docformatter

To check your plugin for rule violations, run::

    docformatter --check -r .
    black --check .
    isort -c .
    flake8 .

You can auto-fix some of these issues by running::

    docformatter -r .
    isort .
    black .

To automatically check for these issues before you commit, you can run ``.install-hooks``.


License
-------


Copyright 2022 Christiaan de Die le Clercq (techwolf12)

Released under the terms of the Apache License 2.0



.. _pretix: https://github.com/pretix/pretix
.. _pretix development setup: https://docs.pretix.eu/en/latest/development/setup.html
