import os
import uuid
import httpx

BASE_URL=os.environ.get("BASE_URL","http://127.0.0.1:8000")

def _u(p): return f"{p}-{uuid.uuid4().hex[:10]}"

def assert_status(r,e):
    if r.status_code!=e:
        raise AssertionError(r.text)

def auth_headers(t): return {"Authorization":f"Bearer {t}"}

def api_register(client,email,password,name):
    r=client.post(f"{BASE_URL}/api/auth/register",json={"email":email,"password":password,"name":name})
    return r,r.json()

def send_req(client,t,receiver,msg=None):
    params={"receiver_id":receiver}
    if msg: params["message"]=msg
    return client.post(f"{BASE_URL}/api/friends/requests",params=params,headers=auth_headers(t))

def inbox(client,t):
    return client.get(f"{BASE_URL}/api/friends/requests/inbox",headers=auth_headers(t))

def accept(client,t,rid):
    return client.post(f"{BASE_URL}/api/friends/requests/{rid}/accept",headers=auth_headers(t))

def list_friends(client,t):
    return client.get(f"{BASE_URL}/api/friends",headers=auth_headers(t))

def unfriend(client,t,fid):
    return client.delete(f"{BASE_URL}/api/friends/{fid}",headers=auth_headers(t))


def test_friends(client):

    p="Password123!"
    e1=f"{_u('alice')}@example.com"
    e2=f"{_u('bob')}@example.com"

    a_r,a=api_register(client,e1,p,"Alice")
    b_r,b=api_register(client,e2,p,"Bob")

    alice_id=a["user"]["id"]
    bob_id=b["user"]["id"]

    at=a["access_token"]
    bt=b["access_token"]

    r1=send_req(client,at,bob_id,"yo")
    assert_status(r1,201)
    rid=r1.json()["id"]

    ib=inbox(client,bt)
    assert_status(ib,200)

    ok=accept(client,bt,rid)
    assert_status(ok,200)

    fl=list_friends(client,at)
    assert_status(fl,200)

    uf=unfriend(client,at,bob_id)
    assert_status(uf,200)

    print("✅ friends tests passed")


if __name__=="__main__":
    with httpx.Client(timeout=10) as client:
        test_friends(client)