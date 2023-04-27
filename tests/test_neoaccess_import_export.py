# Testing of Import/Export of database dumps : APOC must be installed first.
####  WARNING : the database will get erased!!!

import pytest
from src.neoaccess import neoaccess as neo_access



# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = neo_access.NeoAccess(debug=False)
    yield neo_obj



def test_export_dbase_json(db):
    # Completely clear the database
    db.empty_dbase()

    # Start by exporting the empty database
    result = db.export_dbase_json()
    assert result == {'nodes': 0, 'relationships': 0, 'properties': 0, 'data': '[\n]'}

    # Create a first node ("Eve")
    node_id_eve = db.create_node("User", {'name': 'Eve'})
    result = db.export_dbase_json()
    assert result['nodes'] == 1
    assert result['relationships'] == 0
    assert result['properties'] == 1
    expected_json = '[{"type":"node","id":"' + str(node_id_eve) + '","labels":["User"],"properties":{"name":"Eve"}}\n]'
    assert result['data'] == expected_json
    ''' EXAMPLE of JSON string:
                [{"type":"node","id":"100","labels":["User"],"properties":{"name":"Eve"}}
                ]
    '''


    # Create a 2nd node ("Adam")
    node_id_adam = db.create_node("User", {'name': 'Adam', 'age': 30})
    result = db.export_dbase_json()
    assert result['nodes'] == 2
    assert result['relationships'] == 0
    assert result['properties'] == 3
    expected_json = f'[{{"type":"node","id":"{node_id_eve}","labels":["User"],"properties":{{"name":"Eve"}}}},\n {{"type":"node","id":"{node_id_adam}","labels":["User"],"properties":{{"name":"Adam","age":30}}}}\n]'
    assert result['data'] == expected_json
    ''' EXAMPLE of JSON string:
                [{"type":"node","id":"100","labels":["User"],"properties":{"name":"Eve"}},
                 {"type":"node","id":"101","labels":["User"],"properties":{"name":"Adam","age":30}}
                ]
    '''

    # Now add relationship (with no properties) between the above two nodes
    db.link_nodes_by_ids(node_id_eve, node_id_adam, "LOVES")
    # Look up the Neo4j ID of the relationship just created
    cypher = "MATCH (to)-[r]->(from) RETURN id(r) AS rel_id"
    query_result = db.query(cypher)
    rel_id_1 = query_result[0]["rel_id"]

    result = db.export_dbase_json()
    assert result['nodes'] == 2
    assert result['relationships'] == 1
    assert result['properties'] == 3
    expected_json = f'[{{"type":"node","id":"{node_id_eve}","labels":["User"],"properties":{{"name":"Eve"}}}},\n' \
                    f' {{"type":"node","id":"{node_id_adam}","labels":["User"],"properties":{{"name":"Adam","age":30}}}},\n' \
                    f' {{"id":"{rel_id_1}","type":"relationship","label":"LOVES","start":{{"id":"{node_id_eve}","labels":["User"]}},"end":{{"id":"{node_id_adam}","labels":["User"]}}}}\n]'
    assert result['data'] == expected_json
    ''' EXAMPLE of JSON string:
        [{"type":"node","id":"108","labels":["User"],"properties":{"name":"Eve"}},
         {"type":"node","id":"109","labels":["User"],"properties":{"name":"Adam","age":30}},
         {"id":"3","type":"relationship","label":"LOVES","start":{"id":"108","labels":["User"]},"end":{"id":"109","labels":["User"]}}
        ]
    '''

    # Add a 2nd relationship (this time with properties) between the two nodes
    db.link_nodes_by_ids(node_id_eve, node_id_adam, "KNOWS", {'since': 1976, 'intensity': 'eternal'})
    # Look up the Neo4j ID of the relationship just created
    cypher = "MATCH (to)-[r:KNOWS]->(from) RETURN id(r) AS rel_id"
    query_result = db.query(cypher)
    rel_id_2 = query_result[0]["rel_id"]

    result = db.export_dbase_json()
    assert result['nodes'] == 2
    assert result['relationships'] == 2
    assert result['properties'] == 5    # Note that the 2 properties in the latest relationship went into the count
    expected_json = f'[{{"type":"node","id":"{node_id_eve}","labels":["User"],"properties":{{"name":"Eve"}}}},\n' \
                    f' {{"type":"node","id":"{node_id_adam}","labels":["User"],"properties":{{"name":"Adam","age":30}}}},\n' \
                    f' {{"id":"{rel_id_1}","type":"relationship","label":"LOVES","start":{{"id":"{node_id_eve}","labels":["User"]}},"end":{{"id":"{node_id_adam}","labels":["User"]}}}},\n' \
                    f' {{"id":"{rel_id_2}","type":"relationship","label":"KNOWS","properties":{{"intensity":"eternal","since":1976}},"start":{{"id":"{node_id_eve}","labels":["User"]}},"end":{{"id":"{node_id_adam}","labels":["User"]}}}}\n]'
    ''' EXAMPLE of JSON string:
        [{"type":"node","id":"124","labels":["User"],"properties":{"name":"Eve"}},
         {"type":"node","id":"125","labels":["User"],"properties":{"name":"Adam","age":30}},
         {"id":"11","type":"relationship","label":"LOVES","start":{"id":"124","labels":["User"]},"end":{"id":"125","labels":["User"]}},
         {"id":"12","type":"relationship","label":"KNOWS","properties":{"intensity":"eternal","since":1976},"start":{"id":"124","labels":["User"]},"end":{"id":"125","labels":["User"]}}
        ]
    '''

    # The order of the relationships appears to vary randomly: also cover the reverse the lines for "LOVES" and "KNOWS"
    # (TODO: it may be better to first parse the JSON string into a python entity and then assert)
    expected_json_reversed_order = f'[{{"type":"node","id":"{node_id_eve}","labels":["User"],"properties":{{"name":"Eve"}}}},\n' \
                    f' {{"type":"node","id":"{node_id_adam}","labels":["User"],"properties":{{"name":"Adam","age":30}}}},\n' \
                    f' {{"id":"{rel_id_2}","type":"relationship","label":"KNOWS","properties":{{"intensity":"eternal","since":1976}},"start":{{"id":"{node_id_eve}","labels":["User"]}},"end":{{"id":"{node_id_adam}","labels":["User"]}}}},\n' \
                    f' {{"id":"{rel_id_1}","type":"relationship","label":"LOVES","start":{{"id":"{node_id_eve}","labels":["User"]}},"end":{{"id":"{node_id_adam}","labels":["User"]}}}}\n]'

    assert (result['data'] == expected_json) or (result['data'] == expected_json_reversed_order)



def test_export_nodes_rels_json(db):    # TODO: this test intermittently fails; probably an assert issue involving order
    db.empty_dbase()

    # Start by exporting everything in the empty database
    result = db.export_nodes_rels_json(nodes_query = "MATCH (n)", rels_query = "MATCH ()-[r]->()")
    assert result == {'nodes': 0, 'relationships': 0, 'properties': 0, 'data': '[\n]'}

    # Create a first node ("Eve")
    node_id_eve = db.create_node("User", {'name': 'Eve'})
    result = db.export_nodes_rels_json()    # By default, all nodes and all relationships
    assert result['nodes'] == 1
    assert result['relationships'] == 0
    assert result['properties'] == 1
    expected_json = '[{"type":"node","id":"' + str(node_id_eve) + '","labels":["User"],"properties":{"name":"Eve"}}\n]'
    assert result['data'] == expected_json
    ''' EXAMPLE of JSON string:
                [{"type":"node","id":"100","labels":["User"],"properties":{"name":"Eve"}}
                ]
    '''

    # Overlook the one existing node
    result = db.export_nodes_rels_json(nodes_query = "MATCH (n :NON_EXISTENT_LABEL)")    # No nodes will be found
    assert result == {'nodes': 0, 'relationships': 0, 'properties': 0, 'data': '[\n]'}


    # Create a 2nd node ("Adam")
    node_id_adam = db.create_node("User", {'name': 'Adam', 'age': 30})
    result = db.export_nodes_rels_json()    # By default, all nodes and all relationships
    assert result['nodes'] == 2
    assert result['relationships'] == 0
    assert result['properties'] == 3
    expected_json = f'[{{"type":"node","id":"{node_id_eve}","labels":["User"],"properties":{{"name":"Eve"}}}},\n {{"type":"node","id":"{node_id_adam}","labels":["User"],"properties":{{"name":"Adam","age":30}}}}\n]'
    assert result['data'] == expected_json
    ''' EXAMPLE of JSON string:
                [{"type":"node","id":"100","labels":["User"],"properties":{"name":"Eve"}},
                 {"type":"node","id":"101","labels":["User"],"properties":{"name":"Adam","age":30}}
                ]
    '''

    # Overlook the "Adam" entry, and just pick up "Eve"
    result = db.export_nodes_rels_json(nodes_query = "MATCH (n) WHERE n.name = 'Eve'")
    assert result['nodes'] == 1
    assert result['relationships'] == 0
    assert result['properties'] == 1
    expected_json = '[{"type":"node","id":"' + str(node_id_eve) + '","labels":["User"],"properties":{"name":"Eve"}}\n]'
    assert result['data'] == expected_json
    ''' EXAMPLE of JSON string:
                [{"type":"node","id":"100","labels":["User"],"properties":{"name":"Eve"}}
                ]
    '''


    # Now add relationship (with no properties) between the above two nodes
    db.link_nodes_by_ids(node_id_eve, node_id_adam, "LOVES")
    # Look up the Neo4j ID of the relationship just created
    cypher = "MATCH (to)-[r]->(from) RETURN id(r) AS rel_id"
    query_result = db.query(cypher)
    rel_id_1 = query_result[0]["rel_id"]

    result = db.export_nodes_rels_json()    # Look up everything: the 2 nodes and the 1 relationship
    assert result['nodes'] == 2
    assert result['relationships'] == 1
    assert result['properties'] == 3
    expected_json = f'[{{"type":"node","id":"{node_id_eve}","labels":["User"],"properties":{{"name":"Eve"}}}},\n' \
                    f' {{"type":"node","id":"{node_id_adam}","labels":["User"],"properties":{{"name":"Adam","age":30}}}},\n' \
                    f' {{"id":"{rel_id_1}","type":"relationship","label":"LOVES","start":{{"id":"{node_id_eve}","labels":["User"]}},"end":{{"id":"{node_id_adam}","labels":["User"]}}}}\n]'
    assert result['data'] == expected_json
    ''' EXAMPLE of JSON string:
        [{"type":"node","id":"108","labels":["User"],"properties":{"name":"Eve"}},
         {"type":"node","id":"109","labels":["User"],"properties":{"name":"Adam","age":30}},
         {"id":"3","type":"relationship","label":"LOVES","start":{"id":"108","labels":["User"]},"end":{"id":"109","labels":["User"]}}
        ]
    '''

    # Only retrieve the "Adam" node, plus all relationships
    result = db.export_nodes_rels_json(nodes_query = "MATCH (n {name: 'Adam'})")    # Retrieves 1 node and 1 relationship
    assert result['nodes'] == 1
    assert result['relationships'] == 1
    assert result['properties'] == 2    # The "name" and "age" for the `Adam` node
    expected_json = f'[{{"type":"node","id":"{node_id_adam}","labels":["User"],"properties":{{"name":"Adam","age":30}}}},\n' \
                    f' {{"id":"{rel_id_1}","type":"relationship","label":"LOVES","start":{{"id":"{node_id_eve}","labels":["User"]}},"end":{{"id":"{node_id_adam}","labels":["User"]}}}}\n]'
    assert result['data'] == expected_json
    ''' EXAMPLE of JSON string:
        [{"type":"node","id":"109","labels":["User"],"properties":{"name":"Adam","age":30}},
         {"id":"3","type":"relationship","label":"LOVES","start":{"id":"108","labels":["User"]},"end":{"id":"109","labels":["User"]}}
        ]
    '''

    # Only retrieve the "Adam" node, and no relationships
    result = db.export_nodes_rels_json( nodes_query = "MATCH (n {name: 'Adam'})",
                                        rels_query = "MATCH ()-[r :NO_SUCH_NAME]->()")    # Retrieves 1 node and 0 relationships
    assert result['nodes'] == 1
    assert result['relationships'] == 0
    assert result['properties'] == 2    # The "name" and "age" for the `Adam` node
    expected_json = f'[{{"type":"node","id":"{node_id_adam}","labels":["User"],"properties":{{"name":"Adam","age":30}}}}\n]'
    assert result['data'] == expected_json
    ''' EXAMPLE of JSON string:
        [{"type":"node","id":"109","labels":["User"],"properties":{"name":"Adam","age":30}}
        ]
    '''

    # Only retrieve the relationship
    result = db.export_nodes_rels_json(nodes_query = "MATCH (n :NON_EXISTENT_LABEL)")    # Only the relationship will be found
    assert result['nodes'] == 0
    assert result['relationships'] == 1
    assert result['properties'] == 0

    expected_json = f'[{{"id":"{rel_id_1}","type":"relationship","label":"LOVES","start":{{"id":"{node_id_eve}","labels":["User"]}},"end":{{"id":"{node_id_adam}","labels":["User"]}}}}\n]'
    assert result['data'] == expected_json
    ''' EXAMPLE of JSON string:
        [{"id":"3","type":"relationship","label":"LOVES","start":{"id":"108","labels":["User"]},"end":{"id":"109","labels":["User"]}}
        ]
    '''

    # Retrieve absolutely nothing
    result = db.export_nodes_rels_json(nodes_query = "MATCH (n :NON_EXISTENT_LABEL)",
                                        rels_query = "MATCH ()-[r :NO_SUCH_NAME]->()")    # Nothing will be found

    assert result == {'nodes': 0, 'relationships': 0, 'properties': 0, 'data': '[\n]'}


    # Add a 2nd relationship (this time with properties) between the two nodes
    db.link_nodes_by_ids(node_id_eve, node_id_adam, "KNOWS", {'since': 1976, 'intensity': 'eternal'})
    # Look up the Neo4j ID of the relationship just created
    cypher = "MATCH (to)-[r:KNOWS]->(from) RETURN id(r) AS rel_id"
    query_result = db.query(cypher)
    rel_id_2 = query_result[0]["rel_id"]

    result = db.export_nodes_rels_json()
    assert result['nodes'] == 2
    assert result['relationships'] == 2
    assert result['properties'] == 5    # Note that the 2 properties in the latest relationship went into the count
    expected_json = f'[{{"type":"node","id":"{node_id_eve}","labels":["User"],"properties":{{"name":"Eve"}}}},\n' \
                    f' {{"type":"node","id":"{node_id_adam}","labels":["User"],"properties":{{"name":"Adam","age":30}}}},\n' \
                    f' {{"id":"{rel_id_1}","type":"relationship","label":"LOVES","start":{{"id":"{node_id_eve}","labels":["User"]}},"end":{{"id":"{node_id_adam}","labels":["User"]}}}},\n' \
                    f' {{"id":"{rel_id_2}","type":"relationship","label":"KNOWS","properties":{{"intensity":"eternal","since":1976}},"start":{{"id":"{node_id_eve}","labels":["User"]}},"end":{{"id":"{node_id_adam}","labels":["User"]}}}}\n]'
    ''' EXAMPLE of JSON string:
        [{"type":"node","id":"124","labels":["User"],"properties":{"name":"Eve"}},
         {"type":"node","id":"125","labels":["User"],"properties":{"name":"Adam","age":30}},
         {"id":"11","type":"relationship","label":"LOVES","start":{"id":"124","labels":["User"]},"end":{"id":"125","labels":["User"]}},
         {"id":"12","type":"relationship","label":"KNOWS","properties":{"intensity":"eternal","since":1976},"start":{"id":"124","labels":["User"]},"end":{"id":"125","labels":["User"]}}
        ]
    '''

    # The order of the relationships appears to vary randomly: also cover the reverse the lines for "LOVES" and "KNOWS"
    # (TODO: it may be better to first parse the JSON string into a python entity and then assert)
    expected_json_reversed_order = f'[{{"type":"node","id":"{node_id_eve}","labels":["User"],"properties":{{"name":"Eve"}}}},\n' \
                    f' {{"type":"node","id":"{node_id_adam}","labels":["User"],"properties":{{"name":"Adam","age":30}}}},\n' \
                    f' {{"id":"{rel_id_2}","type":"relationship","label":"KNOWS","properties":{{"intensity":"eternal","since":1976}},"start":{{"id":"{node_id_eve}","labels":["User"]}},"end":{{"id":"{node_id_adam}","labels":["User"]}}}},\n' \
                    f' {{"id":"{rel_id_1}","type":"relationship","label":"LOVES","start":{{"id":"{node_id_eve}","labels":["User"]}},"end":{{"id":"{node_id_adam}","labels":["User"]}}}}\n]'

    assert (result['data'] == expected_json) or (result['data'] == expected_json_reversed_order)


    # Only request the "KNOWS" relationship
    result = db.export_nodes_rels_json(rels_query = "MATCH ()-[r :KNOWS]->()")
    assert result['nodes'] == 2
    assert result['relationships'] == 1 # We ditched one of the two relationships
    assert result['properties'] == 5
    expected_json = f'[{{"type":"node","id":"{node_id_eve}","labels":["User"],"properties":{{"name":"Eve"}}}},\n' \
                    f' {{"type":"node","id":"{node_id_adam}","labels":["User"],"properties":{{"name":"Adam","age":30}}}},\n' \
                    f' {{"id":"{rel_id_2}","type":"relationship","label":"KNOWS","properties":{{"intensity":"eternal","since":1976}},"start":{{"id":"{node_id_eve}","labels":["User"]}},"end":{{"id":"{node_id_adam}","labels":["User"]}}}}\n]'
    ''' EXAMPLE of JSON string:
        [{"type":"node","id":"124","labels":["User"],"properties":{"name":"Eve"}},
         {"type":"node","id":"125","labels":["User"],"properties":{"name":"Adam","age":30}},
         {"id":"12","type":"relationship","label":"KNOWS","properties":{"intensity":"eternal","since":1976},"start":{"id":"124","labels":["User"]},"end":{"id":"125","labels":["User"]}}
        ]
    '''
    assert result['data'] == expected_json



def test_import_json_data(db):

    # Check various malformed JSON data dumps
    with pytest.raises(Exception):
        assert db.import_json_dump("Nonsensical JSON string")   # This ought to raise an Exception:
                                                                # Incorrectly-formatted JSON string. Expecting value: line 1 column 1 (char 0)
    with pytest.raises(Exception):
        assert db.import_json_dump('{"a": "this is good JSON, but not a list!"}')   # This ought to raise an Exception:
                                                                                    # "The JSON string does not represent a list"
    with pytest.raises(Exception):                      # This ought to raise an Exception:
        assert db.import_json_dump('[1, 2, 3]')         # Item in list index 0 should be a dict, but instead it's of type <class 'int'>.  Item: 1

    with pytest.raises(Exception):
        assert db.import_json_dump('[{"bad_type":"node"}]')     # The dict in 0-th element lacks a "type" key

    with pytest.raises(Exception):
        assert db.import_json_dump('[{"type":"bad_value"}]')    # The dict in 0-th element doesn't have an acceptable value
                                                                # for the "type" key

    with pytest.raises(Exception):
        assert db.import_json_dump('[{"type":"node"}]')         # Missing "id" key

    with pytest.raises(Exception):
        assert db.import_json_dump('[{"type":"node", "id": "NOT_INTEGER"}]')    # Non-integer id

    with pytest.raises(Exception):
        json = '[{"id":"4","type":"relationship","label":"is_friends_with","start":{"id":"123","labels":["User"]},"end":{"id":"456","labels":["Person", "Client"]}}]'
        db.import_json_dump(json)                               # Trying to add a relationship between non-existing nodes


    # Now, test actual imports

    db.empty_dbase()    # Completely clear the database

    # Import a 1st node
    json = '[{"type":"node","id":"123","labels":["User"],"properties":{"name":"Eve"}}]'
    details = db.import_json_dump(json)
    assert details == "Successful import of 1 node(s) and 0 relationship(s)"
    match = db.match(labels="User", properties={"name": "Eve"})
    retrieved_records = db.get_nodes(match)
    assert len(retrieved_records) == 1
    match_all = db.match()
    retrieved_records = db.get_nodes(match_all)
    assert len(retrieved_records) == 1

    # Import a 2nd node
    json = '[{"type":"node","id":"456","labels":["Person", "Client"],"properties":{"name":"Adam"}}]'
    details = db.import_json_dump(json)
    assert details == "Successful import of 1 node(s) and 0 relationship(s)"
    match = db.match(labels=["Person", "Client"], properties={"name": "Adam"})
    retrieved_records = db.get_nodes(match)
    assert len(retrieved_records) == 1
    retrieved_records = db.get_nodes(match_all)
    assert len(retrieved_records) == 2


    # Starting with an empty database, re-import the 2 earlier nodes, but this time both at once
    db.empty_dbase()    # Completely clear the database

    json = '[{"type":"node","id":"123","labels":["User"],"properties":{"name":"Eve"}},\n' \
           '{"type":"node","id":"456","labels":["Person", "Client"],"properties":{"name":"Adam"}}]'
    details = db.import_json_dump(json)
    assert details == "Successful import of 2 node(s) and 0 relationship(s)"

    match = db.match(labels="User", properties={"name": "Eve"})
    retrieved_records = db.get_nodes(match)
    assert len(retrieved_records) == 1

    match = db.match(labels=["Person", "Client"], properties={"name": "Adam"})
    retrieved_records = db.get_nodes(match)
    assert len(retrieved_records) == 1

    retrieved_records = db.get_nodes(match_all)
    assert len(retrieved_records) == 2


    # Starting with an empty database, re-import the 2 earlier nodes, but this time both at once - and with a relationship between them
    db.empty_dbase()    # Completely clear the database

    json = '[{"type":"node","id":"123","labels":["User"],"properties":{"name":"Eve"}},\n' \
           '{"type":"node","id":"456","labels":["Person", "Client"],"properties":{"name":"Adam"}},\n' \
           '{"id":"7","type":"relationship","label":"is_friends_with","start":{"id":"123","labels":["User"]},"end":{"id":"456","labels":["Person", "Client"]}}]'
    details = db.import_json_dump(json)
    assert details == "Successful import of 2 node(s) and 1 relationship(s)"

    match = db.match(labels="User", properties={"name": "Eve"})
    retrieved_records = db.get_nodes(match, return_internal_id=True)
    assert len(retrieved_records) == 1
    id_eve = retrieved_records[0]["internal_id"]

    match = db.match(labels=["Person", "Client"], properties={"name": "Adam"})
    retrieved_records = db.get_nodes(match, return_internal_id=True)
    assert len(retrieved_records) == 1
    id_adam = retrieved_records[0]["internal_id"]

    retrieved_records = db.get_nodes(match_all)
    assert len(retrieved_records) == 2

    q = '''
        MATCH (eve :User {name: "Eve"}) - [:is_friends_with] -> (adam :Person:Client {name: "Adam"})
        RETURN count(eve) AS num_eve, count(adam) AS num_adam, id(eve) AS id_eve, id(adam) AS id_adam
        '''
    result = db.query(q, single_row=True)
    assert result == {'num_eve': 1, 'num_adam': 1, 'id_eve': id_eve, 'id_adam': id_adam}
