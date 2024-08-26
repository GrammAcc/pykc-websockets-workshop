"""This module provides the version 1 websocket-based api endpoints of the backend.

All endpoints in this module need to authenticate the logged in user on connection except
for the form-validation endpoint, which is usable outside of a logged in session.
"""

from quart import Blueprint

from pykcworkshop.chat.api.websockets import helpers
from pykcworkshop.chat.types import UserData

bp = Blueprint("v1-websockets", __name__, url_prefix="/v1")
"""This blueprint contains all version 1 websocket routes for the chat app."""


@bp.websocket("/room/<room_token>/chat-message")
@helpers.auth_required(inject_user_data=True)
async def chat_message_socket(room_token: str, user_data: UserData):
    """Many;Many Websocket connection that brokers chat messages between clients connected
    to the same chatroom.

    This handler should receive() messages in JSON format from connected
    clients and send() the messages to all connected clients. This includes
    the client that the message came from.

    The JSON messages receive()d from the client will have the following structure:

        {
            "user_name": str,
            "content": str,
        }

    This handler should also add a `timestamp` field to the JSON message before send()ing it
    to the connected clients, so the JSON structure that should be passed into send() is:

        {
            "user_name": str,
            "content": str,
            "timestamp": str,
        }

    This timestamp should be a string in ISO 8601 format since the client needs to be able to
    parse the date and localize the timezone information in Javascript, so that the correct
    date and time are displayed based on the location of the user.

    This websocket should also silently discard any messages with an empty `content` field.
    The client's UI should prevent sending empty messages, but UI programming can be flaky, so
    we also want to ensure that we don't store empty messages in the db and/or broadcast them
    to all clients. We don't need to send back any kind of error or anything, so if a message
    comes in with a `content` field that is an empty string, then we can simply discard the
    message without queueing anything to send back.
    """

    return "NOT FOUND", 404


@bp.websocket("/room/<room_token>/member-status")
@helpers.auth_required(inject_user_data=True)
async def member_status_socket(room_token: str, user_data: UserData):
    """Many;Many Websocket connection that brokers status updates between clients connected to the
    same chatroom.

    This handler should receive() messages in JSON format from connected
    clients and send() the messages to all connected clients. This includes
    the client that the message came from.

    The JSON messages receive()d from the client will have the following structure:

        {
            user_id: int,
            user_name: str,
            user_status: str,
        }

    This handler doesn't need to transform the data that it receives from
    the client in any way. It simply has to broadcast the JSON messages
    received to all connected clients including the client that the message came from.

    This handler also needs to send a message with the status 'Offline' to all connected
    clients when a client disconnects, so that the remaining clients will remain up-to-date
    with the disconnected client's status in the chatroom. This needs to be sent from the
    server since there is no way for the client to send this message when it disconnects
    unexpectedly.

    The offline message needs to have the same structure as the messages that are
    receive()d from the clients, so it should look like this:

        {
            user_id: disconnected_user_id,
            user_name: disconnected_user_name,
            user_status: 'Offline',
        }
    """

    return "NOT FOUND", 404


@bp.websocket("/room/<room_token>/client-sync")
@helpers.auth_required(inject_user_data=False)
async def client_sync_socket(room_token: str):
    """Many;Many Websocket connection that brokers arbitrary client-client messages.

    This handler should receive() arbitrary string messages from connected clients
    and send() the messages to all connected clients unaltered. This includes
    the client that the message came from.

    The purpose of this websocket connection is to simplify development of some UI features
    without requiring the frontend developers to request additional functionality from
    the backend developers.

    For example, the client can define a simple event protocol for requesting a status update from
    all other connected clients. When the client receive()s a message using this event protocol
    on the client side of this websocket connection, it then send()s a message on the
    member-status socket connection with its current status, which would then get broadcast
    to all other connected clients by the server through the normal behavior of that connection.

    Since all connected clients would be using this event protocol, this would allow the
    frontend developers to synchronize client connection statuses in the UI when a
    new client connects without needing the backend to implement this kind of logic on
    client connection.

    Essentially, this websocket is used by the frontend to broker client-client communication
    when functionality needed by the frontend is acheiveable through the use of other
    sockets/routes already implemented, but requires additional coordination between connected
    clients. This makes it easier for frontend devs to make small day to day UI/UX improvements
    without requesting changes to the backend.
    """

    return "NOT FOUND", 404


@bp.websocket("/room/<room_token>/chat-history")
@helpers.auth_required(inject_user_data=False)
async def stream_chat_history(room_token: str):
    """1;1 WebSocket that streams older messages to the client in chunks to
    facilitate features such as infinite scroll and chat history without
    laggy or clunky interfaces.

    The client will send messages with a reference timestamp and a chunk size.
    This websocket should return messages containing `chunk_size` chat message
    objects in reverse chronological order starting from the first chat message
    in this room that is older than the reference timestamp. The client will
    send JSON messages with the following structure:

        {
            timestamp: int,
            chunk_size: int,
        }

    The `timestamp` field is the client's current reference point in the history as a
    Unix timestamp in UTC. Because javascript encodes timestamps in milliseconds but Python
    uses seconds in floating point, this value needs to be divided by 1000 before constructing a
    `datetime.datetime` instance from it.

    The `chunk_size` field is the number of chat messages the client wants. This value is
    suitable for use directly in a `limit` statement for the db query.

    The server should send json-encoded messages with the following structure:

        {
            user_name: str,
            content: str,
            timestamp: str,
        }[]


    The objects are the same structure as the chat-message and direct-message endpoints. The
    only difference is that we are returning an array of these objects instead of a single
    json-serialized object.

    The specific messages that are returned should be the newest messages in the db for this
    chatroom that are older than the reference timestamp. The length of the list/array we
    return should match the `chunk_size`, and the order of the objects in the array should
    be reverse-chronological.

    In other words, this corresponds to a SQL query for messages older than the reference
    timestamp, ordered by their timestamps descending, and with a limit of
    `chunk_size`.
    """

    return "NOT FOUND", 404


@bp.websocket("/<interlocutor_id>/direct-message")
@helpers.auth_required(inject_user_data=True)
async def slide_in_those_dms(interlocutor_id: int, user_data: UserData):
    """P2P WebSocket for private messages between the logged in user and
    the user with id `interlocutor_id`.

    The behavior and data structures of this websocket are the same as the `chat-message`
    socket with the following exceptions:

    1. Messages should only be broadcast between the logged
    in user and the user with id `interlocutor_id` instead of all
    members of a chatroom.
    2. Messages should not get saved to the database. DMs are considered ephemeral.

    Even though messages are not stored in the db, this websocket should still silently
    discard messages with empty `content` fields just like the chat-message socket.
    The reason is to avoid the overhead and potentially bad user experience of broadcasting
    empty messages to connected clients even if we don't have to worry about keeping the db
    clean.
    """

    return "NOT FOUND", 404


@bp.websocket("/form-validation")
async def form_validation():
    """1;1 Websocket connection that validates form-fields in realtime as the
    user types.

    This connection is protected by the CSRF token, but it is not authenticated
    since some input screens are available to users who are not logged in
    (e.g. user sign-up/creation), so the server should not send any information over this
    connection that could benefit a malicious user in mounting a side channel attack.

    In general, since this websocket is only doing input validation, at a minimum it only
    needs to send back the data that the client sent and a boolean field indicating if validation
    failed or not, so we don't have to worry about leaking information if we don't
    include anything unnecessary in the messages sent to the client. The client
    will send data in one of the following formats:

        {
            type: "create-user",
            form_data: {"user_name": str},
        }
        or
        {
            type: "create-room",
            form_data: {"room_name": str, "user_id": int},
        }
        or
        {
            type: "chat-message",
            form_data: {"content": str},
        }

    This is a simple JSON protocol for validating different form fields sent from the
    frontend, and more formats can be added as needed.

    After validating the `form_data`, a JSON-formatted message should be sent to the
    client with the following structure:

        {
            form_data: dict,
            validation_failed: bool,
            failure_reason: str,
        }

    The `form_data` key in this message should be the same `form_data` key from the message
    received from the client, and it should not be altered in any way on the server.

    It's probably obvious, but the `validation_failed` boolean is `True` if the `form_data` failed
    validation and `False` if it succeeded.

    The `failure_reason` key is a string message that can be displayed to the user in
    realtime while they are editing the form field.
    This message should not include any debugging information or other details that could be
    used by an attacker. It should be concise and state a single validation problem with
    the form data. For example, `f"User name {form_data['user_name']} is already taken"` if
    we are validating whether a user name is available. If there are multiple validation
    conditions, this message should only include the first failed condition.
    We don't need to include all validation problems since the message will update
    in realtime on the frontend as the user types, so the user can correct the error as they type
    and the bad UX of only seeing the first error in traditional input validation is not an issue.
    For this reason, if we want to, then we can also optimize the validation routine slightly by
    stopping at the first failure condition and sending the message. For example, if there are
    two different conditions that need to be met to pass validation, and the check for the
    first condition fails, we don't need to check the second condition, and we can simply send
    a failure message over the websocket using the first failure condition for the
    `failure_reason`. This can be a significant gain if some of the validation conditions
    require db queies and others don't. Validating the fastest checks first could save
    a lot of time when the server is under load.

    `failure_reason` should be an empty string `""` if validation succeeded.

    Validation rules:

    If the `type` field is `"create-user"`, then we need to validate the following:

    1. The user name isn't already taken by a user in the database.
    2. The user name isn't longer than the character limit on the `User.name` column in the db.
      - See `pykcworkshop.chat.db.models.User` for this limit.
    3. The user name isn't an empty string.

    If the `type` is `"create-room"`, then we need to validate the following:

    1. The user with id `form_data["user_id"]` doesn't already own a room with the provided
    `room_name`.
    2. The `room_name` isn't longer than the character limit on the `Room.name` column in the db.
      - See `pykcworkshop.chat.db.models.Room` for this limit.
    3. The room name isn't an empty string.

    If the `type` is `"chat-message"`, then we need to validate the following:

    1. The `form_data["content"]` str is not longer than the character limit on the
    `ChatMessage.content` column in the db.
      - See `pykcworkshop.chat.db.models.ChatMessage` for this limit.
    """

    return "NOT FOUND", 404
