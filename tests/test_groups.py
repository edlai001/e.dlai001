from datetime import datetime, timedelta

from tests.conftest import register_and_login


def create_group(client, name='Exam prep', description='Databases exam'):
    return client.post('/api/groups', json={'name': name, 'description': description})


def test_groups_require_login(client):
    assert client.get('/api/groups').status_code == 401
    assert create_group(client).status_code == 401


def test_create_group_makes_creator_the_owner(client):
    me = register_and_login(client)
    resp = create_group(client)
    assert resp.status_code == 201
    group_id = resp.get_json()['group_id']

    assert client.get('/api/groups').get_json()['groups'] == [
        {'id': group_id, 'name': 'Exam prep', 'description': 'Databases exam'}]

    detail = client.get(f'/api/groups/{group_id}').get_json()
    assert detail['members'] == [{'user_id': me, 'name': detail['members'][0]['name'], 'role': 'owner'}]
    assert detail['sessions'] == []


def test_create_group_requires_name(client):
    register_and_login(client)
    assert create_group(client, name='   ').status_code == 400


def test_group_name_and_description_longer_than_database_allows_are_rejected(client):
    # schema.sql: groups.name 100, groups.description 500 characters
    register_and_login(client)
    assert create_group(client, name='x' * 101).status_code == 400
    assert create_group(client, description='x' * 501).status_code == 400
    assert create_group(client, name='x' * 100, description='x' * 500).status_code == 201


def test_get_unknown_group_is_404(client):
    register_and_login(client)
    assert client.get('/api/groups/999999').status_code == 404


def test_discover_join_and_leave(client, make_client):
    register_and_login(client)
    client.put('/api/profile', json={'display_name': 'Owner'})
    client.post('/api/profile/subjects', json={'subject_name': 'Databases'})
    group_id = create_group(client).get_json()['group_id']

    other = make_client()
    other_id = register_and_login(other)

    found = other.get('/api/groups/discover').get_json()['groups']
    assert len(found) == 1
    assert found[0]['id'] == group_id
    assert found[0]['creator'] == 'Owner'
    assert found[0]['member_count'] == 1
    assert found[0]['subjects'] == ['Databases']
    assert found[0]['next_session'] is None

    # The owner does not see their own group in discover
    assert client.get('/api/groups/discover').get_json()['groups'] == []

    assert other.post(f'/api/groups/{group_id}/join').status_code == 201
    assert other.post(f'/api/groups/{group_id}/join').status_code == 409
    assert other.get('/api/groups/discover').get_json()['groups'] == []
    roles = {m['user_id']: m['role'] for m in other.get(f'/api/groups/{group_id}').get_json()['members']}
    assert roles[other_id] == 'member'

    assert other.post(f'/api/groups/{group_id}/leave').status_code == 200
    assert other.get('/api/groups').get_json()['groups'] == []


def test_join_unknown_group_is_404(client):
    register_and_login(client)
    assert client.post('/api/groups/999999/join').status_code == 404


def test_schedule_session_shows_in_group_and_discover(client, make_client):
    register_and_login(client)
    group_id = create_group(client).get_json()['group_id']

    start = (datetime.now() + timedelta(days=2)).replace(second=0, microsecond=0)
    end = start + timedelta(hours=2)
    resp = client.post(f'/api/groups/{group_id}/sessions', json={
        'start_datetime': start.strftime('%Y-%m-%d %H:%M'),
        'end_datetime': end.strftime('%Y-%m-%d %H:%M'),
        'location_or_link': 'Library room 3',
    })
    assert resp.status_code == 201

    sessions = client.get(f'/api/groups/{group_id}').get_json()['sessions']
    assert len(sessions) == 1
    assert sessions[0]['location'] == 'Library room 3'
    assert sessions[0]['start'].startswith(start.strftime('%Y-%m-%d %H:%M'))

    other = make_client()
    register_and_login(other)
    found = other.get('/api/groups/discover').get_json()['groups'][0]
    assert found['next_session'] == start.strftime('%Y-%m-%d %H:%M')


def test_schedule_session_requires_times(client):
    register_and_login(client)
    group_id = create_group(client).get_json()['group_id']
    assert client.post(f'/api/groups/{group_id}/sessions', json={}).status_code == 400


def test_schedule_session_with_bad_date_format_is_rejected(client):
    register_and_login(client)
    group_id = create_group(client).get_json()['group_id']
    resp = client.post(f'/api/groups/{group_id}/sessions',
                       json={'start_datetime': 'tomorrow', 'end_datetime': 'later'})
    assert resp.status_code == 400


def test_session_must_end_after_it_starts(client):
    register_and_login(client)
    group_id = create_group(client).get_json()['group_id']
    resp = client.post(f'/api/groups/{group_id}/sessions',
                       json={'start_datetime': '2030-01-01 12:00', 'end_datetime': '2030-01-01 10:00'})
    assert resp.status_code == 400


def test_only_members_can_schedule_sessions(client, make_client):
    register_and_login(client)
    group_id = create_group(client).get_json()['group_id']

    outsider = make_client()
    register_and_login(outsider)
    resp = outsider.post(f'/api/groups/{group_id}/sessions',
                         json={'start_datetime': '2030-01-01 10:00', 'end_datetime': '2030-01-01 12:00'})
    assert resp.status_code == 403


def test_invite_only_accepted_partners(client, make_client):
    register_and_login(client)
    group_id = create_group(client).get_json()['group_id']

    friend = make_client()
    friend_id = register_and_login(friend)

    # Not partners yet
    assert client.post(f'/api/groups/{group_id}/invite', json={'user_id': friend_id}).status_code == 403

    client.post('/api/matches/request', json={'to_user_id': friend_id})
    req_id = friend.get('/api/matches/requests/incoming').get_json()['requests'][0]['id']
    friend.put(f'/api/matches/request/{req_id}', json={'status': 'accepted'})

    assert client.post(f'/api/groups/{group_id}/invite', json={'user_id': friend_id}).status_code == 201
    assert [g['id'] for g in friend.get('/api/groups').get_json()['groups']] == [group_id]
