import pytest
import mock
import builtins
from geocam.communicator import *

""" RESSOURCES 
Test with pytest: https://www.youtube.com/watch?v=YbpKMIUjvK8
Test inputs: https://stackoverflow.com/questions/35851323/how-to-test-a-function-with-input-call

"""

## TESTS ON CLASSES 

@pytest.fixture
def leader():
    return Communicator(Communicator.LEADER)

@pytest.fixture
def agent(): 
    return Communicator(Communicator.AGENT)

@pytest.fixture
def collaborator():
    return Communicator(Communicator.COLLABORATOR)


def test_create_communicators_and_test_there_behavior(leader, agent, collaborator):
    assert isinstance(leader, Communicator)
    assert isinstance(agent, Communicator)
    assert isinstance(collaborator, Communicator)
    assert isinstance(leader.behavior, Leader)
    assert isinstance(agent.behavior, Agent)
    assert isinstance(collaborator.behavior, Collaborator)

def test_str_and_repr_(leader, agent, collaborator):
    assert leader.__str__() == f"Communicator Class instance behaving like a {leader.kind}"
    assert agent.__str__() == f"Communicator Class instance behaving like a {agent.kind}"
    assert collaborator.__str__() == f"Communicator Class instance behaving like a {collaborator.kind}"
    assert leader.__repr__() == f"Communicator(Communicator.{leader.kind.upper()})"
    assert agent.__repr__() == f"Communicator(Communicator.{agent.kind.upper()})"
    assert collaborator.__repr__() == f"Communicator(Communicator.{collaborator.kind.upper()})"

    assert leader.behavior.__str__() == Communicator.LEADER
    assert agent.behavior.__str__() == Communicator.AGENT
    assert collaborator.behavior.__str__() == Communicator.COLLABORATOR
    assert leader.behavior.__repr__() == "Communicator(Comminicator.LEADER)"
    assert agent.behavior.__repr__() == "Communicator(Communicator.AGENT)"
    assert collaborator.behavior.__repr__() == "Communicator(Comminicator.COLLABORATOR)"

def test_change_behavior_method(leader, agent, collaborator):
    leader.change_behavior(Communicator.LEADER)
    assert isinstance(leader.behavior, Leader)
    leader.change_behavior(Communicator.AGENT)
    assert isinstance(leader.behavior, Agent)
    leader.change_behavior(Communicator.COLLABORATOR)
    assert isinstance(leader.behavior, Collaborator)

    agent.change_behavior(Communicator.LEADER)
    assert isinstance(agent.behavior, Leader)
    agent.change_behavior(Communicator.AGENT)
    assert isinstance(agent.behavior, Agent)
    agent.change_behavior(Communicator.COLLABORATOR)
    assert isinstance(agent.behavior, Collaborator)

    collaborator.change_behavior(Communicator.LEADER)
    assert isinstance(collaborator.behavior, Leader)
    collaborator.change_behavior(Communicator.AGENT)
    assert isinstance(collaborator.behavior, Agent)
    collaborator.change_behavior(Communicator.COLLABORATOR)
    assert isinstance(collaborator.behavior, Collaborator)


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_change_all_connections_parameters(leader):
    initial_mcast_grp = Behavior.MCAST_GRP
    initial_mcast_port = Behavior.MCAST_PORT
    initial_tcp_port = Behavior.TCP_PORT
    new_mcast_grp = "224.1.1.2"
    new_mcast_port = 1967
    new_tcp_port = 1643

    with mock.patch.object(builtins, 'input', lambda _: 'n'):
        leader._change_all_mcast_grps(new_mcast_grp)
        assert Behavior.MCAST_GRP == initial_mcast_grp
        leader._change_all_mcast_ports(new_mcast_port)
        assert Behavior.MCAST_PORT == initial_mcast_port
        leader._change_all_tcp_ports(new_tcp_port)
        assert Behavior.TCP_PORT == initial_tcp_port

    with mock.patch.object(builtins, 'input', lambda _: 'shduvzdi'):
        leader._change_all_mcast_grps(new_mcast_grp)
        assert Behavior.MCAST_GRP == initial_mcast_grp
        leader._change_all_mcast_ports(new_mcast_port)
        assert Behavior.MCAST_PORT == initial_mcast_port
        leader._change_all_tcp_ports(new_tcp_port)
        assert Behavior.TCP_PORT == initial_tcp_port

    with mock.patch.object(builtins, 'input', lambda _: 'y'):
        leader._change_all_mcast_grps(new_mcast_grp)
        assert Behavior.MCAST_GRP != initial_mcast_grp
        leader._change_all_mcast_ports(new_mcast_port)
        assert Behavior.MCAST_PORT != initial_mcast_port
        leader._change_all_tcp_ports(new_tcp_port)
        assert Behavior.TCP_PORT != initial_tcp_port





    





