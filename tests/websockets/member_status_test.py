import json

import websockets

from pykcworkshop import utils


async def test_member_status_disconnection(
    fixt_test_room, fixt_testy, fixt_ws_headers_testy, fixt_ws_headers_testier
):
    """The member status websocket connection should send a server-originated message to all
    connected clients when a client disconnects."""

    test_room = await fixt_test_room()
    testy = await fixt_testy()
    sock_url = f"{utils.get_domain().replace('http', 'ws')}\
/chat/api/v1/room/{test_room.id}/member-status"
    first_connection = await websockets.connect(sock_url, extra_headers=fixt_ws_headers_testier)
    second_connection = await websockets.connect(sock_url, extra_headers=fixt_ws_headers_testy)
    await second_connection.close()
    msg = await first_connection.recv()
    await first_connection.close()
    data = json.loads(msg)
    assert data["user_id"] == testy.id
    assert data["user_name"] == testy.name
    assert data["user_status"] == "Offline"
