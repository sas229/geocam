import pytest
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







    





