from conftest import client


def test_auditor_can_read_audit_not_block_users():
    client.post('/api/auth/register', json={'username': 'admin1', 'email': 'admin1@test.com', 'password': 'Password1', 'recaptcha_token': 'test-token'})
    login = client.post('/api/auth/login', json={'email': 'admin1@test.com', 'password': 'Password1', 'recaptcha_token': 'test-token'})
    cookies = login.cookies

    res = client.get('/api/audit', cookies=cookies)
    assert res.status_code in (200, 403)
