[![Code Style & Upload](https://github.com/Techwolf12/pretix-regid/actions/workflows/style-upload.yml/badge.svg)](https://github.com/Techwolf12/pretix-regid/actions/workflows/style-upload.yml)

Registration ID
==========================

This is a plugin for `pretix`_. 

Adds an automatic registration ID to approved orders. When enabling this plugin it will automatically create registration ID's on the event it is enabled. It has to be enabled from the start to work correctly, otherwise you will have users without registration ID.  

  
To install:
```
pip3 install pretix-regid && python3 -m pretix migrate && python3 -m pretix rebuild && service pretix-web restart
```

Then just activate it in your event config.

Development setup
-----------------

1. Make sure that you have a working `pretix development setup`_.

2. Clone this repository.

3. Activate the virtual environment you use for pretix development.

4. Execute ``python setup.py develop`` within this directory to register this application with pretix's plugin registry.

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
