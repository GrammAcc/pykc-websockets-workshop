import {
  currentUser,
  sessionToken,
  csrfToken,
  setCurrentRoom,
  currentRoom,
  clearCurrentRoom,
  authHeaders,
} from "./utils/shared_state.mjs";
import { onPageLoad, setupLoggingHandlers } from "./utils/helpers.mjs";
import { appendMessageToChatUI, makeErrMsgEl, prependMessageToChatUI } from "./utils/ui.mjs";
import { openModal, getModalAnchor, makeRoomInfoModal, makeDMChatModal } from "./modals.mjs";

/** @type { {chatMessage: WebSocket | null, msgLengthValidation: WebSocket | null, chatHistory: WebSocket | null, memberStatus: WebSocket | null, clientSync: WebSocket | null, dms: WebSocket | null, dmLengthValidation: WebSocket | null }} */
const connections = {
  chatMessage: null,
  msgLengthValidation: null,
  chatHistory: null,
  memberStatus: null,
  clientSync: null,
  dms: null,
  dmLengthValidation: null,
};

/** @type {number} */
let oldestMsgTimestamp = new Date().getTime();

/** @type {boolean} */
let isRoomSendDisabled = false;

/** @type {string} */
let connectedRoomID = "";

export function isChatroomConnected() {
  return connectedRoomID !== "";
}

export async function connectToRoom(roomID) {
  if (isChatroomConnected()) {
    disconnectFromRoom();
  }
  document.querySelector("#chatroom-ui-root").classList.remove("hidden");
  connectedRoomID = roomID;

  const jsonData = await (
    await fetch(`/chat/api/v1/room/${roomID}`, { headers: authHeaders() })
  ).json();

  setCurrentRoom(jsonData);
  const { roomName, ...rest } = currentRoom();

  /** @type {HTMLDivElement} */
  const msgList = document.querySelector("#room-message-list");

  /** @type {HTMLButtonElement} */
  const sendBtn = document.querySelector("#room-message-send-btn");

  /** @type {HTMLParagraphElement} */
  const errMsgEl = document.querySelector("#room-message-length-validation-msg");

  // Chat Message Socket Setup.
  if (connections.chatMessage !== null) {
    connections.chatMessage.close();
  }
  oldestMsgTimestamp = new Date().getTime();
  const chatMessageSocket = new WebSocket(`/chat/api/v1/room/${roomID}/chat-message`, [
    `Bearer${sessionToken()}`,
    `csrf${csrfToken()}`,
  ]);
  connections.chatMessage = chatMessageSocket;
  setupLoggingHandlers(chatMessageSocket, "chat-message");
  chatMessageSocket.addEventListener("message", (ev) => {
    appendMessageToChatUI(msgList, JSON.parse(ev.data));
  });

  // Chat Message Length Validation Socket Setup.
  if (connections.msgLengthValidation !== null) {
    connections.msgLengthValidation.close();
  }
  const msgLengthSocket = new WebSocket(`/chat/api/v1/form-validation`, `csrf${csrfToken()}`);
  connections.msgLengthValidation = msgLengthSocket;
  setupLoggingHandlers(msgLengthSocket, "form-validation/chat-message");
  msgLengthSocket.addEventListener("message", (ev) => {
    /** @type {{form_data: {content: string}, validation_failed: boolean, failure_reason: string}} */
    const result = JSON.parse(ev.data);
    if (result.validation_failed) {
      errMsgEl.textContent = result.failure_reason;
      errMsgEl.style.color = "red";
      sendBtn.setAttribute("disabled", true);
      isRoomSendDisabled = true;
      errMsgEl.classList.remove("hidden");
    } else {
      sendBtn.removeAttribute("disabled");
      isRoomSendDisabled = false;
      errMsgEl.classList.add("hidden");
    }
  });
  // Chat History Socket Setup.
  if (connections.chatHistory !== null) {
    connections.chatHistory.close();
  }
  const chatHistorySocket = new WebSocket(`/chat/api/v1/room/${roomID}/chat-history`, [
    `Bearer${sessionToken()}`,
    `csrf${csrfToken()}`,
  ]);
  connections.chatHistory = chatHistorySocket;
  setupLoggingHandlers(chatHistorySocket, "chat-history");
  chatHistorySocket.addEventListener("message", (ev) => {
    /** @type {{user_name: string, content: string, timestamp: string}[]} */
    const msgData = JSON.parse(ev.data);
    if (msgData.length > 0) {
      oldestMsgTimestamp = new Date(msgData[msgData.length - 1].timestamp).getTime();

      for (const msg of msgData) {
        prependMessageToChatUI(msgList, msg);
      }
    }
  });
  chatHistorySocket.addEventListener("open", () => {
    sendHistoryRequest(10);
  });

  document.querySelector("#room-info-root").classList.remove("hidden");
  const roomNameEl = document.createElement("p");
  roomNameEl.classList.add("clickable", "ml-auto", "font-bold");
  roomNameEl.textContent = roomName;
  roomNameEl.addEventListener("click", () => {
    openModal(makeRoomInfoModal(roomID));
  });
  const roomNamePlateEl = document.querySelector("#room-name-plate");
  roomNamePlateEl.replaceChildren();
  roomNamePlateEl.appendChild(roomNameEl);

  const roomMembers = await (
    await fetch(`/chat/api/v1/room/${roomID}/members`, { headers: authHeaders() })
  ).json();
  for (const memberData of roomMembers) {
    memberData.user_status = "Offline";
    updateRoomMemberStatus(memberData);
  }

  // Member Status Socket Setup
  if (connections.memberStatus !== null) {
    connections.memberStatus.close();
  }
  const memberStatusSocket = new WebSocket(`/chat/api/v1/room/${roomID}/member-status`, [
    `Bearer${sessionToken()}`,
    `csrf${csrfToken()}`,
  ]);
  connections.memberStatus = memberStatusSocket;
  setupLoggingHandlers(memberStatusSocket, "member-status");
  memberStatusSocket.addEventListener("message", (ev) => {
    /** @type {{ "user_id": string, "user_name": string, "user_status": string }} */
    const userData = JSON.parse(ev.data);
    updateRoomMemberStatus(userData);
  });

  // Client Sync Socket Setup
  if (connections.clientSync !== null) {
    connections.clientSync.close();
  }
  const clientSyncSocket = new WebSocket(`/chat/api/v1/room/${roomID}/client-sync`, [
    `Bearer${sessionToken()}`,
    `csrf${csrfToken()}`,
  ]);
  connections.clientSync = clientSyncSocket;
  setupLoggingHandlers(clientSyncSocket, "client-sync");
  clientSyncSocket.addEventListener("open", (_ev) => {
    clientSyncSocket.send("member-status");
  });
  clientSyncSocket.addEventListener("message", (ev) => {
    if (ev.data === "member-status") {
      sendMemberStatus("Online");
    }
  });
}

export async function disconnectFromRoom() {
  connectedRoomID = "";
  clearCurrentRoom();
  document.querySelector("#chatroom-ui-root").classList.add("hidden");
  document.querySelector("#room-info-root").classList.add("hidden");
  oldestMsgTimestamp = new Date().getTime();
  document.querySelector("#member-list").replaceChildren();
  document.querySelector("#room-name-plate").replaceChildren();
  document.querySelector("#room-message-list").replaceChildren();
  document.querySelector("#room-message-input").value = "";
  for (const socket of Object.values(connections)) {
    if (socket !== null) {
      socket.close();
    }
  }
  getModalAnchor().replaceChildren();
}

/** @param {string} msg */
function sendChatMessage(msg) {
  if (msg !== "") {
    const userData = currentUser();
    const payload = { content: msg, user_name: userData.userName };
    if (connections.chatMessage !== null) {
      connections.chatMessage.send(JSON.stringify(payload));
    }
  }
}

/**
 * @param {{ "user_id": string, "user_name": string, "user_status": string }} memberData
 */
async function updateRoomMemberStatus(memberData) {
  /** @type {HTMLDivElement} */
  const memberList = document.querySelector("#member-list");

  /** @type {HTMLParagraphElement} */
  const userStatusEl = memberList.querySelector(`#USER-${memberData.user_id}`);
  if (userStatusEl) {
    userStatusEl.textContent = `${memberData.user_name} - ${memberData.user_status}`;
    if (memberData.user_status === "Offline") {
      userStatusEl.classList.remove("clickable");
    } else if (currentUser().userID !== memberData.user_id) {
      userStatusEl.classList.add("clickable");
    }
  } else {
    const newStatusEl = document.createElement("p");
    newStatusEl.textContent = `${memberData.user_name} - ${memberData.user_status}`;
    newStatusEl.id = `USER-${memberData.user_id}`;
    if (currentUser().userID !== memberData.user_id) {
      newStatusEl.classList.add("clickable");
    }
    newStatusEl.addEventListener("click", () => {
      if (newStatusEl.classList.contains("clickable")) {
        if (connections.dms !== null) {
          connections.dms.close();
        }
        getModalAnchor().replaceChildren();
        const dmSocket = new WebSocket(`/chat/api/v1/${memberData.user_id}/direct-message`, [
          `Bearer${sessionToken()}`,
          `csrf${csrfToken()}`,
        ]);
        connections.dms = dmSocket;
        setupLoggingHandlers(dmSocket, "direct-message");
        const validationSocket = new WebSocket(
          "/chat/api/v1/form-validation",
          `csrf${csrfToken()}`,
        );
        connections.dmLengthValidation = validationSocket;
        setupLoggingHandlers(validationSocket, "form-validation/dm-length");
        openModal(
          makeDMChatModal(dmSocket, validationSocket, {
            user_id: memberData.user_id,
            user_name: memberData.user_name,
          }),
        );
      }
    });
    memberList.appendChild(newStatusEl);
  }
}

/** @param {string} status */
function sendMemberStatus(status) {
  if (status !== "") {
    const userData = currentUser();
    const payload = { user_id: userData.userID, user_name: userData.userName, user_status: status };
    if (connections.memberStatus !== null) {
      connections.memberStatus.send(JSON.stringify(payload));
    }
  }
}

/** @param {number} chunkSize */
function sendHistoryRequest(chunkSize) {
  if (connections.chatHistory !== null) {
    connections.chatHistory.send(
      JSON.stringify({ timestamp: oldestMsgTimestamp, chunk_size: chunkSize, newer: false }),
    );
  }
}

onPageLoad(() => {
  /** @type {HTMLDivElement} */
  const msgList = document.querySelector("#room-message-list");

  msgList.addEventListener("scroll", (_ev) => {
    if (msgList.scrollTop === 0) {
      if (connections.chatHistory !== null) {
        sendHistoryRequest(5);
      }
    }
    setTimeout(() => {}, 400);
  });

  /** @type {HTMLDivElement} */
  const msgInputContainer = document.querySelector("#room-message-input-container");
  const errMsgEl = makeErrMsgEl();
  errMsgEl.id = "room-message-length-validation-msg";
  msgInputContainer.after(errMsgEl);

  /** @type {HTMLTextAreaElement} */
  const msgInput = document.querySelector("#room-message-input");
  msgInput.addEventListener("input", async (_ev) => {
    if (connections.msgLengthValidation !== null) {
      connections.msgLengthValidation.send(
        JSON.stringify({ type: "chat-message", form_data: { content: msgInput.value } }),
      );
    }
  });
  msgInput.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter" && !ev.shiftKey) {
      ev.preventDefault();
      if (!isRoomSendDisabled) {
        sendChatMessage(msgInput.value);
        msgInput.value = "";
        sendMemberStatus("Online");
      }
    }
  });
  const sendBtn = document.querySelector("#room-message-send-btn");
  sendBtn.addEventListener("click", (_ev) => {
    const msg = msgInput.value;
    sendChatMessage(msg);
    msgInput.value = "";
    sendMemberStatus("Online");
  });

  /** @type {HTMLTextAreaElement} */
  const messageInput = document.querySelector("#room-message-input");
  messageInput.addEventListener("input", async (ev) => {
    if (ev.target.value === "") {
      sendMemberStatus("Online");
    } else {
      sendMemberStatus("Typing");
    }
  });
});
