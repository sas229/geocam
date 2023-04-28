:orphan:

:py:mod:`geocam.communicator`
=============================

.. py:module:: geocam.communicator


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   geocam.communicator.ListeningRPi
   geocam.communicator.Receiver
   geocam.communicator.Sender




.. py:class:: ListeningRPi(device: str = 'controller', mcast_grp: str = '224.1.1.1', mcast_port: int = 9998, tcp_port: int = 47822)

   Bases: :py:obj:`Receiver`

   _summary_

   :param Communicator: _description_
   :type Communicator: _type_

   .. py:method:: stream()

      - Stream video to a ip address



.. py:class:: Receiver(device: str = 'controller', mcast_grp: str = '224.1.1.1', mcast_port: int = 9998, tcp_port: int = 47822)

   Bases: :py:obj:`Communicator`

   _summary_

   :param Communicator: _description_
   :type Communicator: _type_


.. py:class:: Sender(device: str = 'controller', mcast_grp: str = '224.1.1.1', mcast_port: int = 9998, tcp_port: int = 47822)

   Bases: :py:obj:`Communicator`

   - They should only be one type of sender: computers.

   :param Communicator: _description_
   :type Communicator: _type_


