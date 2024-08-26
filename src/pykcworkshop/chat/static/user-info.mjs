import {
  csrfToken,
  authHeaders,
  currentUser,
  clearCurrentUser,
  setCurrentUser,
} from "./utils/shared_state.mjs";
import { disconnectFromRoom, connectToRoom, isChatroomConnected } from "./chat-ui.mjs";
import { openModal, makeUserInfoModal, getModalAnchor } from "./modals.mjs";

export async function repopulateJoinedRoomList() {
  const container = document.querySelector("#joined-room-list");
  container.replaceChildren();
  const res = await fetch(`/chat/api/v1/user/rooms/joined`, { headers: authHeaders() });
  /** @type {{ "room_hash": str, "room_name": str }[]} */
  const rooms = await res.json();
  /** @type {HTMLDivElement} */
  const roomList = document.createElement("div");
  for (const room of rooms) {
    const roomData = { roomID: room.room_hash, roomName: room.room_name };
    const roomLink = document.createElement("p");
    roomLink.classList.add("alternating-item");
    roomLink.textContent = roomData.roomName;
    roomLink.addEventListener("click", () => {
      if (isChatroomConnected()) {
        disconnectFromRoom();
      }
      connectToRoom(roomData.roomID);
    });
    roomList.appendChild(roomLink);
  }
  container.appendChild(roomList);
}

export async function logIn(userHash) {
  const res = await fetch("/chat/api/v1/user/login", {
    method: "POST",
    body: JSON.stringify({ user_hash: userHash }),
    headers: { "Content-Type": "application/json", "X-CSRF-TOKEN": csrfToken() },
  });
  if (res.status === 200) {
    /** @type {{ "user_id": number, "user_name": string, "user_token": string }} */
    const newUserData = await res.json();
    setCurrentUser(newUserData);

    document.querySelector("#login-ui").classList.add("hidden");
    document.querySelector("#logout-ui").classList.remove("hidden");
    document.querySelector("#manage-rooms-ui").classList.remove("hidden");
    document.querySelector("#user-info-root").classList.remove("hidden");
    const userNameEl = document.createElement("h2");
    userNameEl.classList.add("clickable");
    userNameEl.textContent = currentUser().userName;
    userNameEl.addEventListener("click", () => {
      openModal(makeUserInfoModal(userHash));
    });
    const namePlatesEl = document.querySelector("#user-name-plate");
    namePlatesEl.replaceChildren();
    namePlatesEl.appendChild(userNameEl);
    repopulateJoinedRoomList();

    return true;
  } else {
    return false;
  }
}

export function logOut() {
  if (isChatroomConnected()) {
    disconnectFromRoom();
  }
  clearCurrentUser();
  document.querySelector("#logout-ui").classList.add("hidden");
  document.querySelector("#login-ui").classList.remove("hidden");
  document.querySelector("#manage-rooms-ui").classList.add("hidden");
  document.querySelector("#user-info-root").classList.add("hidden");
  document.querySelector("#user-name-plate").replaceChildren();
  document.querySelector("#joined-room-list").replaceChildren();
  getModalAnchor().replaceChildren();
}
