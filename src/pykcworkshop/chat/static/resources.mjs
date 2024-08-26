import { connectToRoom } from "./chat-ui.mjs";
import { repopulateJoinedRoomList } from "./user-info.mjs";
import { csrfToken, authHeaders } from "./utils/shared_state.mjs";

/**
 * @param {string} userName
 * @returns {Promise<{ "userID": string, "userName": string } | string | null>}
 */
export async function createUser(userName) {
  const res = await fetch("/chat/api/v1/user/create", {
    method: "POST",
    body: JSON.stringify({ user_name: userName }),
    headers: { "Content-Type": "application/json", "X-CSRF-TOKEN": csrfToken() },
  });
  if (res.status === 201) {
    /** @type {{ "user_hash": string, "user_name": string }} */
    const jsonData = await res.json();
    return { userID: jsonData.user_hash, userName: jsonData.user_name };
  } else {
    return null;
  }
}

/**
 * @param {string} roomName
 * @returns {Promise<{ "room_hash": string, "room_name": string } | null>}
 */
export async function createRoom(roomName) {
  const res = await fetch("/chat/api/v1/room/create", {
    method: "POST",
    body: JSON.stringify({ room_name: roomName }),
    headers: {
      ...authHeaders(),
      "Content-Type": "application/json",
    },
  });
  if (res.status === 201) {
    /** @type {{ "room_hash": string, "room_name": string }} */
    const jsonData = await res.json();
    const roomData = { roomID: jsonData.room_hash, roomName: jsonData.room_name };
    repopulateJoinedRoomList();
    connectToRoom(roomData.roomID);
    return roomData;
  } else {
    return null;
  }
}

/**
 * @param {string} roomID The hash of the room to join.
 * @returns {Promise<boolean>} true if user was successfully added to room else false.
 */
export async function joinRoom(roomID) {
  const res = await fetch(`/chat/api/v1/room/${roomID}/join`, {
    method: "PUT",
    headers: {
      ...authHeaders(),
      "Content-Type": "application/json",
    },
  });
  if (res.status === 200) {
    repopulateJoinedRoomList();
    connectToRoom(roomID);
    return true;
  } else {
    return false;
  }
}
