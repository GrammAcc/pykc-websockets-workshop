const nullRoom = { roomID: "", roomName: "" };

/** @type {{roomID: string, roomName: string}} */
const roomData = { ...nullRoom };

export function clearCurrentRoom() {
  for (const key of Object.keys(roomData)) {
    roomData[key] = nullRoom[key];
  }
}

export function currentRoom() {
  return { roomID: roomData.roomID, roomName: roomData.roomName };
}

/**
 * @param {{room_hash: string, room_name: string}} newRoomData
 */
export function setCurrentRoom(newRoomData) {
  roomData.roomID = newRoomData.room_hash;
  roomData.roomName = newRoomData.room_name;
}

const nullUser = { userID: -1, userName: "", userToken: "" };

/** @type {{userID: number, userName: string, userToken: string}} */
const userData = { ...nullUser };

export function clearCurrentUser() {
  for (const key of Object.keys(userData)) {
    userData[key] = nullUser[key];
  }
}

export function currentUser() {
  return { userID: userData.userID, userName: userData.userName };
}

/**
 * @param {{user_id: number, user_name: string, user_token: string}} newUserData
 */
export function setCurrentUser(newUserData) {
  userData.userID = newUserData.user_id;
  userData.userName = newUserData.user_name;
  userData.userToken = newUserData.user_token;
}

export function sessionToken() {
  return userData.userToken;
}

/** Get the CSRF token from the server-rendered page.
 * @returns {string} The CSRF token unique to this page.
 */
export function csrfToken() {
  return document.querySelector('meta[name="csrf-token"]').content;
}

export function authHeaders() {
  return { Authorization: `Bearer ${sessionToken()}`, "X-CSRF-TOKEN": csrfToken() };
}
