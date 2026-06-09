from conftest import client

def test_register_and_login():
    r = client.post('/api/auth/register', json={
        'username': 'u1', 
        'email': 'u1@test.com', 
        'password': 'Password1'
    })
    assert r.status_code == 201  
    assert r.json()['requires_2fa'] == True
    email = r.json()['email']
    
    r = client.post('/api/auth/login', json={
        'email': 'u1@test.com', 
        'password': 'Password1'
    })
    assert r.status_code == 200
    assert r.json()['requires_2fa'] == True
    
def test_login_invalid_credentials():
    r = client.post('/api/auth/login', json={
        'email': 'none@test.com', 
        'password': 'Password1'
    })
    assert r.status_code == 401
    body = r.json()
    assert body['message'] == 'Неверный email или пароль'
