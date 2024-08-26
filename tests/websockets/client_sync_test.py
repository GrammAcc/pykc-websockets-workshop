import websockets

from pykcworkshop import utils


async def test_client_sync_messages_unchanged(fixt_test_room, fixt_ws_headers_testy):
    """The client-sync websocket should not alter the messages sent from
    the client in any way as this would break the expectations of the
    client-client communication on the frontend."""

    test_room = await fixt_test_room()
    sock_url = (
        f"{utils.get_domain().replace('http', 'ws')}/chat/api/v1/room/{test_room.id}/client-sync"
    )
    conn = await websockets.connect(sock_url, extra_headers=fixt_ws_headers_testy)
    msg = "some message"
    await conn.send(msg)
    res = await conn.recv()
    assert res == msg

    await conn.close()
