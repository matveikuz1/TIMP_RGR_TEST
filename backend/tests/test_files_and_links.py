from io import BytesIO

from conftest import client


def auth_cookie():
    client.post('/api/auth/register', json={'username': 'u2', 'email': 'u2@test.com', 'password': 'Password1', 'recaptcha_token': 'test-token'})
    r = client.post('/api/auth/login', json={'email': 'u2@test.com', 'password': 'Password1', 'recaptcha_token': 'test-token'})
    return r.cookies


def test_upload_create_link_download_revoke():
    cookies = auth_cookie()

    file_content = b'hello world'
    r = client.post('/api/files/upload', files={'upload': ('a.txt', BytesIO(file_content), 'text/plain')}, cookies=cookies)
    assert r.status_code == 200
    file_id = r.json()['id']

    r = client.post(f'/api/files/{file_id}/links', json={'ttl_hours': 1, 'max_uses': 1, 'password': 'Pass1234'}, cookies=cookies)
    assert r.status_code == 200
    token = r.json()['token']

    r = client.get(f'/api/files/download/{token}', params={'password': 'Pass1234'})
    assert r.status_code == 200

    r = client.get(f'/api/files/download/{token}', params={'password': 'Pass1234'})
    assert r.status_code == 410
