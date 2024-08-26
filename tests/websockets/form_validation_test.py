import json

import pytest
import websockets

from pykcworkshop import utils

form_types = ["create-user", "create-room", "chat-message"]


@pytest.fixture(params=form_types, ids=form_types)
async def fixt_valid_form_messages(request, fixt_testy):
    testy = await fixt_testy()
    match request.param:
        case "create-user":
            return {"type": "create-user", "form_data": {"user_name": "NewUser"}}
        case "create-room":
            return {
                "type": "create-room",
                "form_data": {"room_name": "New Room", "user_id": testy.id},
            }
        case "chat-message":
            return {"type": "chat-message", "form_data": {"content": "Some chat message text"}}


@pytest.fixture(params=form_types, ids=form_types)
async def fixt_invalid_form_messages(request, fixt_testy, fixt_test_room):
    testy = await fixt_testy()
    test_room = await fixt_test_room()
    match request.param:
        case "create-user":
            return {"type": "create-user", "form_data": {"user_name": testy.name}}
        case "create-room":
            return {
                "type": "create-room",
                "form_data": {"room_name": test_room.name, "user_id": testy.id},
            }
        case "chat-message":
            return {
                "type": "chat-message",
                "form_data": {"content": "".join(["c" for i in range(2048)])},
            }


async def test_form_validation_form_data_unchanged_on_success(
    fixt_ws_headers_csrf_only, fixt_valid_form_messages
):
    """The form validation websocket should send response messages with the provided form_data
    without altering it in any way regardless of validation failure."""

    sock_url = f"{utils.get_domain().replace('http', 'ws')}/chat/api/v1/form-validation"
    sock = await websockets.connect(sock_url, extra_headers=fixt_ws_headers_csrf_only)
    await sock.send(json.dumps(fixt_valid_form_messages))
    msg = await sock.recv()
    await sock.close()
    data = json.loads(msg)
    for k, v in data["form_data"].items():
        assert fixt_valid_form_messages["form_data"][k] == v


async def test_form_validation_form_data_unchanged_on_failure(
    fixt_ws_headers_csrf_only, fixt_invalid_form_messages
):
    """The form validation websocket should send response messages with the provided form_data
    without altering it in any way regardless of validation failure."""

    sock_url = f"{utils.get_domain().replace('http', 'ws')}/chat/api/v1/form-validation"
    sock = await websockets.connect(sock_url, extra_headers=fixt_ws_headers_csrf_only)
    await sock.send(json.dumps(fixt_invalid_form_messages))
    msg = await sock.recv()
    await sock.close()
    data = json.loads(msg)
    for k, v in data["form_data"].items():
        assert fixt_invalid_form_messages["form_data"][k] == v


async def test_form_validation_failed_is_false_on_success(
    fixt_ws_headers_csrf_only, fixt_valid_form_messages
):
    """The form validation websocket should send response messages with False for the
    `validation_failed` value when validation was successful. This is the most
    important part of the interface."""

    sock_url = f"{utils.get_domain().replace('http', 'ws')}/chat/api/v1/form-validation"
    sock = await websockets.connect(sock_url, extra_headers=fixt_ws_headers_csrf_only)
    await sock.send(json.dumps(fixt_valid_form_messages))
    msg = await sock.recv()
    await sock.close()
    data = json.loads(msg)
    assert "validation_failed" in data
    assert not data["validation_failed"]


async def test_form_validation_failed_is_true_on_failure(
    fixt_ws_headers_csrf_only, fixt_invalid_form_messages
):
    """The form validation websocket should send response messages with True for the
    `validation_failed` value when validation was unsuccessful. This is the most
    important part of the interface."""

    sock_url = f"{utils.get_domain().replace('http', 'ws')}/chat/api/v1/form-validation"
    sock = await websockets.connect(sock_url, extra_headers=fixt_ws_headers_csrf_only)
    await sock.send(json.dumps(fixt_invalid_form_messages))
    msg = await sock.recv()
    await sock.close()
    data = json.loads(msg)
    assert data["validation_failed"]


async def test_form_validation_failure_reason_empty_on_success(
    fixt_ws_headers_csrf_only, fixt_valid_form_messages
):
    """The form validation websocket should send response messages with an empty string
    for the `failure_reason` when validation succeeded."""

    sock_url = f"{utils.get_domain().replace('http', 'ws')}/chat/api/v1/form-validation"
    sock = await websockets.connect(sock_url, extra_headers=fixt_ws_headers_csrf_only)
    await sock.send(json.dumps(fixt_valid_form_messages))
    msg = await sock.recv()
    await sock.close()
    data = json.loads(msg)
    assert "failure_reason" in data
    assert data["failure_reason"] == ""


async def test_form_validation_create_user_name_taken(fixt_ws_headers_csrf_only, fixt_testy):
    """The form validation websocket should respond with validation failure
    for create-user when the user name is already taken."""

    testy = await fixt_testy()
    sock_url = f"{utils.get_domain().replace('http', 'ws')}/chat/api/v1/form-validation"
    sock = await websockets.connect(sock_url, extra_headers=fixt_ws_headers_csrf_only)
    await sock.send(json.dumps({"type": "create-user", "form_data": {"user_name": testy.name}}))
    msg = await sock.recv()
    await sock.close()
    data = json.loads(msg)
    assert data["validation_failed"]


async def test_form_validation_create_user_name_too_long(fixt_ws_headers_csrf_only):
    """The form validation websocket should respond with validation failure
    for create-user when the user name is longer than the character limit
    on the db column."""

    sock_url = f"{utils.get_domain().replace('http', 'ws')}/chat/api/v1/form-validation"
    sock = await websockets.connect(sock_url, extra_headers=fixt_ws_headers_csrf_only)
    await sock.send(
        json.dumps(
            {"type": "create-user", "form_data": {"user_name": "".join(["c" for i in range(50)])}}
        )
    )
    msg = await sock.recv()
    await sock.close()
    data = json.loads(msg)
    assert data["validation_failed"]


async def test_form_validation_create_user_name_empty(fixt_ws_headers_csrf_only):
    """The form validation websocket should respond with validation failure
    for create-user when the user name is an empty string."""

    sock_url = f"{utils.get_domain().replace('http', 'ws')}/chat/api/v1/form-validation"
    sock = await websockets.connect(sock_url, extra_headers=fixt_ws_headers_csrf_only)
    await sock.send(json.dumps({"type": "create-user", "form_data": {"user_name": ""}}))
    msg = await sock.recv()
    await sock.close()
    data = json.loads(msg)
    assert data["validation_failed"]


async def test_form_validation_create_room_name_taken(
    fixt_ws_headers_csrf_only, fixt_testy, fixt_test_room
):
    """The form validation websocket should respond with validation failure
    for create-room when the user already has a room with that name."""

    testy = await fixt_testy()
    test_room = await fixt_test_room()
    sock_url = f"{utils.get_domain().replace('http', 'ws')}/chat/api/v1/form-validation"
    sock = await websockets.connect(sock_url, extra_headers=fixt_ws_headers_csrf_only)
    await sock.send(
        json.dumps(
            {"type": "create-room", "form_data": {"user_id": testy.id, "room_name": test_room.name}}
        )
    )
    msg = await sock.recv()
    await sock.close()
    data = json.loads(msg)
    assert data["validation_failed"]


async def test_form_validation_create_room_name_too_long(fixt_ws_headers_csrf_only, fixt_testy):
    """The form validation websocket should respond with validation failure
    for create-room when the room name is longer than the character limit
    on the db column."""

    testy = await fixt_testy()
    sock_url = f"{utils.get_domain().replace('http', 'ws')}/chat/api/v1/form-validation"
    sock = await websockets.connect(sock_url, extra_headers=fixt_ws_headers_csrf_only)
    await sock.send(
        json.dumps(
            {
                "type": "create-room",
                "form_data": {"user_id": testy.id, "room_name": "".join(["c" for i in range(100)])},
            }
        )
    )
    msg = await sock.recv()
    await sock.close()
    data = json.loads(msg)
    assert data["validation_failed"]


async def test_form_validation_create_room_name_empty(fixt_ws_headers_csrf_only, fixt_testy):
    """The form validation websocket should respond with validation failure
    for create-room when the room name is an empty string."""

    testy = await fixt_testy()
    sock_url = f"{utils.get_domain().replace('http', 'ws')}/chat/api/v1/form-validation"
    sock = await websockets.connect(sock_url, extra_headers=fixt_ws_headers_csrf_only)
    await sock.send(
        json.dumps({"type": "create-room", "form_data": {"user_id": testy.id, "room_name": ""}})
    )
    msg = await sock.recv()
    await sock.close()
    data = json.loads(msg)
    assert data["validation_failed"]


async def test_form_validation_chat_message_too_long(fixt_ws_headers_csrf_only):
    """The form validation websocket should respond with validation failure for
    chat-message when the content is longer than the character limit on the db
    column."""

    sock_url = f"{utils.get_domain().replace('http', 'ws')}/chat/api/v1/form-validation"
    sock = await websockets.connect(sock_url, extra_headers=fixt_ws_headers_csrf_only)
    await sock.send(
        json.dumps(
            {"type": "chat-message", "form_data": {"content": "".join(["c" for i in range(2000)])}}
        )
    )
    msg = await sock.recv()
    await sock.close()
    data = json.loads(msg)
    assert data["validation_failed"]
