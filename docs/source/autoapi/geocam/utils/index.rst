:orphan:

:py:mod:`geocam.utils`
======================

.. py:module:: geocam.utils


Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   geocam.utils.create_json
   geocam.utils.get_host_ip
   geocam.utils.get_host_name
   geocam.utils.is_local_ip_address
   geocam.utils.network_status
   geocam.utils.ping
   geocam.utils.read_json



.. py:function:: create_json(command: str, arguments: dict) -> str

   _summary_

   :param command: _description_
   :type command: str
   :param arguments: _description_
   :type arguments: str

   :returns: string representing a JSON object
   :rtype: str


.. py:function:: get_host_ip() -> str

   Gets the host IP address

   :returns: IP address
   :rtype: str


.. py:function:: get_host_name() -> str

   No very useful but might become useful, if not discard it

   :returns: _description_
   :rtype: str


.. py:function:: is_local_ip_address(host_ip: str) -> bool

   _summary_

   :param host_ip: _description_
   :type host_ip: str

   :returns: _description_
   :rtype: bool


.. py:function:: network_status(remote_server: str = 'google.com') -> str

   _summary_
   3 status possible:
   - status_1: the device is not on a network
   - status_2: the device is on a network with no access to internet
   - status_3: the device is on a network with access to internet

   :param remote_server: Sexternal server that the device will try to reach to test the internet connection,
                         by default "google.com"
   :type remote_server: str, optional


.. py:function:: ping(target: str) -> bool

   This method is used to ping the network

   :param host: Host to ping
   :type host: str

   :returns: True if we have an answer or False if no answer
   :rtype: bool


.. py:function:: read_json(json_string: str) -> dict

   Don't do much for now but might become usefull later

   :param json_string: _description_
   :type json_string: str

   :returns: _description_
   :rtype: dict


