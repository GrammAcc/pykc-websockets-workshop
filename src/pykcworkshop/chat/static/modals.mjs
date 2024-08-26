import { currentUser } from "./utils/shared_state.mjs";
import { appendMessageToChatUI, makeErrMsgEl } from "./utils/ui.mjs";
import { createRoom, createUser, joinRoom } from "./resources.mjs";
import { logIn } from "./user-info.mjs";

/** Create a base styled modal and return the element.
 * @returns {HTMLDivElement}
 */
function _makeBaseModal() {
  const modal = document.createElement("div");
  modal.classList.add(
    "flex",
    "flex-col",
    "p-4",
    "bg-gray-800",
    "shadow-lg",
    "shadow-black",
    "fixed",
    "top-[15%]",
    "bottom-[15%]",
    "left-[15%]",
    "right-[15%]",
    "overflow-y-scroll",
  );
  return modal;
}

/** Create a modal for the create new user workflow and return its root element.
 * @param {WebSocket} validationSocket An open websocket connection to the form-validation endpoint.
 * @returns {HTMLDivElement}
 */
export function makeCreateUserModal(validationSocket) {
  const modal = _makeBaseModal();
  const userNameInput = document.createElement("input");
  userNameInput.type = "text";
  userNameInput.placeholder = "New user name...";
  userNameInput.classList.add("common-text-input");
  modal.appendChild(userNameInput);
  const btnLayout = document.createElement("div");
  btnLayout.classList.add("flex", "flex-row");
  const submitBtn = document.createElement("button");
  submitBtn.textContent = "Submit";
  btnLayout.appendChild(submitBtn);
  const cancelBtn = document.createElement("button");
  cancelBtn.textContent = "Cancel";
  cancelBtn.classList.add("ml-auto");
  btnLayout.appendChild(cancelBtn);
  modal.appendChild(btnLayout);
  const validationMsgEl = makeErrMsgEl();
  validationMsgEl.classList.remove("hidden");
  modal.appendChild(validationMsgEl);
  submitBtn.setAttribute("disabled", true);
  let isFormValid = false;
  validationSocket.addEventListener("message", (ev) => {
    /** @type {{form_data: {user_name: string}, validation_failed: Boolean, failure_reason: string}} */
    const data = JSON.parse(ev.data);
    isFormValid = !data.validation_failed;
    if (data.validation_failed) {
      validationMsgEl.style.color = "red";
      validationMsgEl.textContent = data.failure_reason;
      submitBtn.setAttribute("disabled", true);
    } else {
      validationMsgEl.style.color = "green";
      validationMsgEl.textContent = `User name ${data.form_data.user_name} is available!`;
      submitBtn.removeAttribute("disabled");
    }
  });
  userNameInput.addEventListener("input", (_ev) => {
    validationSocket.send(
      JSON.stringify({ type: "create-user", form_data: { user_name: userNameInput.value } }),
    );
  });
  /** @param {Event} ev */
  const submitRoutine = async (ev) => {
    ev.stopImmediatePropagation();
    ev.preventDefault();
    if (isFormValid) {
      const newUserData = await createUser(userNameInput.value);
      if (newUserData === null) {
        alert("An unknown error occurred");
      } else {
        validationSocket.close();
        logIn(newUserData.userID);
        modal.replaceWith(makeUserInfoModal(newUserData.userID));
      }
    }
  };
  userNameInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      submitRoutine(event);
    }
  });
  submitBtn.addEventListener("click", submitRoutine);
  cancelBtn.addEventListener("click", (_ev) => {
    validationSocket.close();
    modal.remove();
  });
  return modal;
}

/**
 * @param {string} hash
 * @param {string} introText
 * @param {string} instructionsText
 * @returns {HTMLDivElement}
 */
function _makeInfoModal(hash, introText, instructionsText) {
  const modal = _makeBaseModal();
  const introParagraph = document.createElement("p");
  introParagraph.textContent = introText;
  modal.appendChild(introParagraph);
  const tokenParagraph = document.createElement("p");
  tokenParagraph.classList.add("my-2", "px-2", "rounded-sm", "bg-black", "text-center");
  tokenParagraph.textContent = hash;
  modal.appendChild(tokenParagraph);
  const instructionsParagraph = document.createElement("p");
  instructionsParagraph.textContent = instructionsText;
  modal.appendChild(instructionsParagraph);
  const acceptBtn = document.createElement("button");
  acceptBtn.textContent = "OK";
  modal.appendChild(acceptBtn);
  acceptBtn.addEventListener("click", (_ev) => {
    modal.remove();
  });
  return modal;
}

/**
 * @param {string} newUserHash
 * @returns {HTMLDivElement}
 */
export function makeUserInfoModal(newUserHash) {
  const introText = "This is your access token:";
  const instructionsText =
    "This token acts as both your username and password. Keep it somewhere safe and do not share it with anyone.";
  return _makeInfoModal(newUserHash, introText, instructionsText);
}

/** Create a modal for the create new room workflow and return its root element.
 * @param {WebSocket} validationSocket An open websocket connection to the form-validation endpoint.
 * @returns {HTMLDivElement}
 */
export function makeCreateRoomModal(validationSocket) {
  const modal = _makeBaseModal();
  const roomNameInput = document.createElement("input");
  roomNameInput.type = "text";
  roomNameInput.placeholder = "New room name...";
  roomNameInput.classList.add("common-text-input");
  modal.appendChild(roomNameInput);
  const btnLayout = document.createElement("div");
  btnLayout.classList.add("flex", "flex-row");
  const submitBtn = document.createElement("button");
  submitBtn.textContent = "Submit";
  btnLayout.appendChild(submitBtn);
  const cancelBtn = document.createElement("button");
  cancelBtn.textContent = "Cancel";
  cancelBtn.classList.add("ml-auto");
  btnLayout.appendChild(cancelBtn);
  modal.appendChild(btnLayout);
  submitBtn.setAttribute("disabled", true);
  let isFormValid = false;
  const validationMsgEl = makeErrMsgEl();
  validationMsgEl.classList.remove("hidden");
  modal.appendChild(validationMsgEl);
  validationSocket.addEventListener("message", (ev) => {
    /** @type {{form_data: {room_name: string, user_id: number}, validation_failed: Boolean, failure_reason: string}} */
    const data = JSON.parse(ev.data);
    isFormValid = !data.validation_failed;
    if (data.validation_failed) {
      validationMsgEl.style.color = "red";
      validationMsgEl.textContent = data.failure_reason;
      submitBtn.setAttribute("disabled", true);
    } else {
      validationMsgEl.style.color = "green";
      validationMsgEl.textContent = `Room name ${data.form_data.room_name} is available!`;
      submitBtn.removeAttribute("disabled");
    }
  });
  roomNameInput.addEventListener("input", (_ev) => {
    validationSocket.send(
      JSON.stringify({
        type: "create-room",
        form_data: { room_name: roomNameInput.value, user_id: currentUser().userID },
      }),
    );
  });

  /** @param {Event} ev */
  const submitRoutine = async (ev) => {
    ev.stopImmediatePropagation();
    ev.preventDefault();
    if (isFormValid) {
      const newRoomData = await createRoom(roomNameInput.value);
      if (newRoomData === null) {
        alert("An unknown error occurred.");
      } else {
        validationSocket.close();
        modal.replaceWith(makeRoomInfoModal(newRoomData.roomID));
      }
    }
  };
  roomNameInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      submitRoutine(event);
    }
  });
  submitBtn.addEventListener("click", submitRoutine);
  cancelBtn.addEventListener("click", (_ev) => {
    validationSocket.close();
    modal.remove();
  });
  return modal;
}

/**
 * @param {string} newRoomHash
 * @returns {HTMLDivElement}
 */
export function makeRoomInfoModal(newRoomHash) {
  const introText = "This is your room access token:";
  const instructionsText =
    "Share this token with anyone you want to be able to join this chatroom.";
  return _makeInfoModal(newRoomHash, introText, instructionsText);
}

/** Create a modal for the user login workflow and return its root element.
 * @returns {HTMLDivElement}
 */
export function makeUserLoginModal() {
  const modal = _makeBaseModal();
  const userTokenInput = document.createElement("input");
  userTokenInput.type = "password";
  userTokenInput.placeholder = "User access token...";
  userTokenInput.classList.add("common-text-input");
  modal.appendChild(userTokenInput);
  const btnLayout = document.createElement("div");
  btnLayout.classList.add("flex", "flex-row");
  const submitBtn = document.createElement("button");
  submitBtn.textContent = "Submit";
  btnLayout.appendChild(submitBtn);
  const cancelBtn = document.createElement("button");
  cancelBtn.textContent = "Cancel";
  cancelBtn.classList.add("ml-auto");
  btnLayout.appendChild(cancelBtn);
  modal.appendChild(btnLayout);
  /** @param {Event} ev */
  const submitRoutine = async (ev) => {
    ev.stopImmediatePropagation();
    ev.preventDefault();
    const loginSuccessful = await logIn(userTokenInput.value);
    if (loginSuccessful) {
      modal.remove();
    } else {
      alert("Error: Invalid user token.");
    }
  };

  userTokenInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      submitRoutine(event);
    }
  });
  submitBtn.addEventListener("click", submitRoutine);
  cancelBtn.addEventListener("click", (_ev) => {
    modal.remove();
  });
  return modal;
}

/** Create a modal for the join room workflow and return its root element.
 * @returns {HTMLDivElement}
 */
export function makeJoinRoomModal() {
  const modal = _makeBaseModal();
  const roomTokenInput = document.createElement("input");
  roomTokenInput.type = "text";
  roomTokenInput.placeholder = "User access token...";
  roomTokenInput.classList.add("common-text-input");
  modal.appendChild(roomTokenInput);
  const btnLayout = document.createElement("div");
  btnLayout.classList.add("flex", "flex-row");
  const submitBtn = document.createElement("button");
  submitBtn.textContent = "Submit";
  btnLayout.appendChild(submitBtn);
  const cancelBtn = document.createElement("button");
  cancelBtn.textContent = "Cancel";
  cancelBtn.classList.add("ml-auto");
  btnLayout.appendChild(cancelBtn);
  modal.appendChild(btnLayout);
  /** @param {Event} ev */
  const submitRoutine = async (ev) => {
    ev.stopImmediatePropagation();
    ev.preventDefault();
    const roomID = roomTokenInput.value;

    const roomSuccessfullyJoined = await joinRoom(roomID);
    if (roomSuccessfullyJoined) {
      modal.remove();
    } else {
      alert("Could not join room. Double check the access token.");
    }
  };

  roomTokenInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      submitRoutine(event);
    }
  });
  submitBtn.addEventListener("click", submitRoutine);
  cancelBtn.addEventListener("click", (_ev) => {
    modal.remove();
  });
  return modal;
}

/** Create a modal for a direct messaging chat between the logged in user and the interlocutor in the same chatroom.
 * @param {WebSocket} dmSocket An open websocket connection to the direct-message endpoint.
 * @param {WebSocket} messageLengthSocket An open websocket connection to the form-validation endpoint.
 * @param {{user_id: number, user_name: string}} interlocutorData The data of the user that the logged in user wants to chat with.
 * @returns {HTMLDivElement} The fully configured modal.
 */
export function makeDMChatModal(dmSocket, messageLengthSocket, interlocutorData) {
  const modal = _makeBaseModal();

  /** @type {HTMLDivElement} */
  const titleBar = document.createElement("div");
  titleBar.classList.add("flex", "flex-row");

  /** @type {HTMLHeadingElement} */
  const chatTitle = document.createElement("h2");
  chatTitle.textContent = `Direct Messaging ${interlocutorData.user_name}`;
  chatTitle.classList.add("grow");
  titleBar.appendChild(chatTitle);
  /** @type {HTMLButtonElement} */
  const closeBtn = document.createElement("button");
  closeBtn.textContent = "Close Chat";
  closeBtn.classList.add("shrink");
  closeBtn.addEventListener("click", () => {
    dmSocket.close();
    modal.remove();
  });
  titleBar.appendChild(closeBtn);

  modal.appendChild(titleBar);

  /** @type {HTMLDivElement} */
  const msgArea = document.createElement("div");
  msgArea.classList.add("grow", "relative");

  /** @type {HTMLDivElement} */
  const dmMsgList = document.createElement("div");
  dmMsgList.classList.add("chat-msg-list");
  msgArea.appendChild(dmMsgList);
  modal.appendChild(msgArea);

  dmSocket.addEventListener("message", (ev) => {
    appendMessageToChatUI(dmMsgList, JSON.parse(ev.data));
  });

  /** @type {HTMLDivElement} */
  const inputContainer = document.querySelector("#room-message-input-container").cloneNode(true);
  inputContainer.id = "dm-input-container";
  const [msgInput, sendBtn] = inputContainer.children;
  msgInput.id = "dm-input";
  sendBtn.id = "dm-input-send-btn";
  modal.appendChild(inputContainer);
  const errMsg = makeErrMsgEl();
  modal.appendChild(errMsg);

  let isSendDisabled = true;

  messageLengthSocket.addEventListener("message", (ev) => {
    /** @type {{form_data: {content: string}, validation_failed: boolean, failure_reason: string}} */
    const result = JSON.parse(ev.data);
    if (result.validation_failed) {
      sendBtn.setAttribute("disabled", true);
      isSendDisabled = true;
      errMsg.classList.remove("hidden");
    } else {
      sendBtn.removeAttribute("disabled");
      isSendDisabled = false;
      errMsg.classList.add("hidden");
    }
  });

  const sendDM = (msg) => {
    const userData = currentUser();
    const payload = { content: msg, user_name: userData.userName };
    dmSocket.send(JSON.stringify(payload));
  };

  msgInput.addEventListener("input", (_ev) => {
    messageLengthSocket.send(
      JSON.stringify({ type: "chat-message", form_data: { content: msgInput.value } }),
    );
  });
  msgInput.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter" && !ev.shiftKey) {
      ev.preventDefault();
      if (!isSendDisabled) {
        const msg = msgInput.value;
        if (msg !== "") {
          sendDM(msg);
          ev.target.value = "";
        }
      }
    }
  });
  sendBtn.addEventListener("click", (_ev) => {
    if (!isSendDisabled) {
      const msg = msgInput.value;
      if (msg !== "") {
        sendDM(msg);
        msgInput.value = "";
      }
    }
  });
  return modal;
}

/** @param {HTMLDivElement} modalEl */
export function openModal(modalEl) {
  const parent = getModalAnchor();
  parent.replaceChildren(modalEl);
}

/** @returns {HTMLDivElement} */
export function getModalAnchor() {
  return document.querySelector("#modal-anchor");
}
