import asyncio
import json
import time

import websockets

from pykcworkshop import utils
from tests.websockets.helpers import validInputMsg


async def test_m2m_broadcast(
    fixt_ws_m2m_endpoints,
    fixt_testy,
    fixt_ws_headers_testy,
    fixt_ws_headers_testier,
    fixt_ws_headers_testiest,
):
    """All many;many websockets should broadcast messages sent from one client to all
    other clients."""

    testy = await fixt_testy()
    sock_url = fixt_ws_m2m_endpoints
    testy_conn = await websockets.connect(sock_url, extra_headers=fixt_ws_headers_testy)
    testier_conn = await websockets.connect(sock_url, extra_headers=fixt_ws_headers_testier)
    testiest_conn = await websockets.connect(sock_url, extra_headers=fixt_ws_headers_testiest)
    payload = validInputMsg(sock_url, testy)
    await testy_conn.send(json.dumps(payload))
    msgs = await asyncio.gather(testier_conn.recv(), testiest_conn.recv())
    await testy_conn.close()
    await testier_conn.close()
    await testiest_conn.close()
    for msg in msgs:
        data = json.loads(msg)
        for key, value in payload.items():
            assert data[key] == value


async def test_m2m_return_to_sender(fixt_ws_m2m_endpoints, fixt_testy, fixt_ws_headers_testy):
    """All many;many websockets should include the client that sent the message when
    broadcasting."""

    testy = await fixt_testy()
    sock_url = fixt_ws_m2m_endpoints
    testy_conn = await websockets.connect(sock_url, extra_headers=fixt_ws_headers_testy)
    payload = validInputMsg(sock_url, testy)
    await testy_conn.send(json.dumps(payload))
    msg = await testy_conn.recv()
    await testy_conn.close()
    data = json.loads(msg)
    for key, value in payload.items():
        assert data[key] == value


async def test_p2p_broadcast(
    fixt_testy,
    fixt_ws_headers_testy,
    fixt_testier,
    fixt_ws_headers_testier,
    fixt_testiest,
    fixt_ws_headers_testiest,
):
    """All p2p websockets should only broadcast messages between two
    specific clients, even if there are other pairs of clients connected
    to the same endpoint."""

    testy = await fixt_testy()
    testier = await fixt_testier()
    testiest = await fixt_testiest()
    testy_2_testier_url = (
        f"{utils.get_domain().replace('http', 'ws')}/chat/api/v1/{testier.id}/direct-message"
    )
    testy_2_testiest_url = (
        f"{utils.get_domain().replace('http', 'ws')}/chat/api/v1/{testiest.id}/direct-message"
    )
    other_2_testy_url = (
        f"{utils.get_domain().replace('http', 'ws')}/chat/api/v1/{testy.id}/direct-message"
    )
    testy_2_testier = await websockets.connect(
        testy_2_testier_url, extra_headers=fixt_ws_headers_testy
    )
    testy_2_testiest = await websockets.connect(
        testy_2_testiest_url, extra_headers=fixt_ws_headers_testy
    )
    testier_2_testy = await websockets.connect(
        other_2_testy_url, extra_headers=fixt_ws_headers_testier
    )
    testiest_2_testy = await websockets.connect(
        other_2_testy_url, extra_headers=fixt_ws_headers_testiest
    )
    for i in range(3):
        await testy_2_testier.send(
            json.dumps({"user_name": testy.name, "content": f"testy_2_testier_{i}"})
        )
        await testy_2_testiest.send(
            json.dumps({"user_name": testy.name, "content": f"testy_2_testiest_{i}"})
        )

    for i in range(3):
        testy_2_testier_payload = {"user_name": testy.name, "content": f"testy_2_testier_{i}"}
        testy_2_testiest_payload = {"user_name": testy.name, "content": f"testy_2_testiest_{i}"}

        data = json.loads(await testy_2_testier.recv())
        for k, v in testy_2_testier_payload.items():
            assert data[k] == v

        data = json.loads(await testier_2_testy.recv())
        for k, v in testy_2_testier_payload.items():
            assert data[k] == v

        data = json.loads(await testy_2_testiest.recv())
        for k, v in testy_2_testiest_payload.items():
            assert data[k] == v

        data = json.loads(await testiest_2_testy.recv())
        for k, v in testy_2_testiest_payload.items():
            assert data[k] == v

    await testy_2_testier.close()
    await testy_2_testiest.close()
    await testier_2_testy.close()
    await testiest_2_testy.close()


async def test_121_broadcast(
    fixt_ws_121_endpoints,
    fixt_testy,
    fixt_ws_headers_testy,
    fixt_testier,
    fixt_ws_headers_testier,
):
    """1;1 websockets should not broadcast messages. All messages should be between the server
    and the connected client even if there are other clients connected to the same endpoint."""

    testy_conn = await websockets.connect(
        fixt_ws_121_endpoints, extra_headers=fixt_ws_headers_testy
    )
    testier_conn = await websockets.connect(
        fixt_ws_121_endpoints, extra_headers=fixt_ws_headers_testier
    )

    timestamp = int(time.time() * 1000)

    for i in range(3):

        match fixt_ws_121_endpoints.split("/").pop():
            case "chat-history":
                await testy_conn.send(json.dumps({"timestamp": timestamp, "chunk_size": 2}))
                await testier_conn.send(json.dumps({"timestamp": 0, "chunk_size": 2}))
            case "form-validation":
                await testy_conn.send(
                    json.dumps({"type": "chat-message", "form_data": {"content": f"testy_{i}"}})
                )
                await testier_conn.send(
                    json.dumps({"type": "chat-message", "form_data": {"content": f"testier_{i}"}})
                )
    for i in range(3):
        testy_data = json.loads(await testy_conn.recv())
        testier_data = json.loads(await testier_conn.recv())
        match fixt_ws_121_endpoints.split("/").pop():
            case "chat-history":
                assert len(testy_data) == 2
                assert len(testier_data) == 0
            case "form-validation":
                assert testy_data["form_data"]["content"] == f"testy_{i}"
                assert testier_data["form_data"]["content"] == f"testier_{i}"

    await testy_conn.close()
    await testier_conn.close()
