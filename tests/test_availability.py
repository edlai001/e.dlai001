from tests.conftest import register_and_login


def add_slot(client, day, start, end):
    return client.post('/api/availability',
                       json={'day_of_week': day, 'start_time': start, 'end_time': end})


def test_availability_requires_login(client):
    assert client.get('/api/availability').status_code == 401
    assert add_slot(client, 0, '09:00', '11:00').status_code == 401


def test_add_and_list_slots_sorted_by_day_and_time(client):
    register_and_login(client)
    assert add_slot(client, 2, '14:00', '16:00').status_code == 201
    assert add_slot(client, 0, '18:00', '20:00').status_code == 201
    assert add_slot(client, 0, '09:00', '11:00').status_code == 201

    slots = client.get('/api/availability').get_json()['slots']
    assert [(s['day'], s['start'], s['end']) for s in slots] == [
        ('Monday', '09:00', '11:00'),
        ('Monday', '18:00', '20:00'),
        ('Wednesday', '14:00', '16:00'),
    ]


def test_sunday_is_day_6(client):
    register_and_login(client)
    assert add_slot(client, 6, '10:00', '12:00').status_code == 201
    assert client.get('/api/availability').get_json()['slots'][0]['day'] == 'Sunday'


def test_slot_requires_all_fields(client):
    register_and_login(client)
    assert client.post('/api/availability', json={'start_time': '09:00', 'end_time': '10:00'}).status_code == 400
    assert client.post('/api/availability', json={'day_of_week': 1, 'end_time': '10:00'}).status_code == 400


def test_slot_start_must_be_before_end(client):
    register_and_login(client)
    assert add_slot(client, 1, '11:00', '09:00').status_code == 400
    assert add_slot(client, 1, '09:00', '09:00').status_code == 400


def test_day_outside_0_to_6_is_rejected(client):
    # schema.sql: CHECK (day_of_week BETWEEN 0 AND 6)
    register_and_login(client)
    assert add_slot(client, 7, '09:00', '10:00').status_code == 400
    assert add_slot(client, -1, '09:00', '10:00').status_code == 400
    assert add_slot(client, 'monday', '09:00', '10:00').status_code == 400


def test_time_must_be_hh_mm(client):
    # schema.sql: start_time / end_time are VARCHAR2(5), i.e. exactly "HH:MM"
    register_and_login(client)
    assert add_slot(client, 1, '09:00:00', '10:00:00').status_code == 400
    assert add_slot(client, 1, '9:00', '10:00').status_code == 400
    assert add_slot(client, 1, '25:00', '26:00').status_code == 400


def test_delete_slot(client):
    register_and_login(client)
    slot_id = add_slot(client, 3, '09:00', '10:00').get_json()['id']
    assert client.delete(f'/api/availability/{slot_id}').status_code == 200
    assert client.get('/api/availability').get_json()['slots'] == []


def test_cannot_delete_another_users_slot(client, make_client):
    register_and_login(client)
    slot_id = add_slot(client, 3, '09:00', '10:00').get_json()['id']

    other = make_client()
    register_and_login(other)
    other.delete(f'/api/availability/{slot_id}')
    assert len(client.get('/api/availability').get_json()['slots']) == 1
