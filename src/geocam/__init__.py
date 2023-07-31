import geocam.log
import geocam.controller
import logging

# Initialise log at default settings.
level = logging.INFO
geocam.log.initialise(level)
log = logging.getLogger(__name__)
log.debug("Initialised geocam log.")