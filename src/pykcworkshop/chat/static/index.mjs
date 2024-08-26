import { csrfToken } from "./utils/shared_state.mjs";
import {
  openModal,
  makeUserLoginModal,
  makeCreateUserModal,
  makeCreateRoomModal,
  makeJoinRoomModal,
} from "./modals.mjs";
import { onPageLoad, setupLoggingHandlers } from "./utils/helpers.mjs";
import { logOut } from "./user-info.mjs";

/** @type {{createUserValidation: WebSocket | null, createRoomValidation: WebSocket | null }} */
const connections = { createUserValidation: null, createRoomValidation: null };

onPageLoad(() => {
  // Create User Workflow
  /** @type {HTMLButtonElement} */
  const createUserBtn = document.querySelector("#create-user-btn");
  createUserBtn.addEventListener("click", () => {
    if (connections.createUserValidation !== null) {
      connections.createUserValidation.close();
    }
    const validationSocket = new WebSocket("/chat/api/v1/form-validation", `csrf${csrfToken()}`);
    connections.createUserValidation = validationSocket;
    setupLoggingHandlers(validationSocket, "form-validation/create-user");
    openModal(makeCreateUserModal(validationSocket));
  });

  // User Login Workflow
  /** @type {HTMLButtonElement} */
  const loginBtn = document.querySelector("#login-btn");
  loginBtn.addEventListener("click", () => {
    openModal(makeUserLoginModal());
  });

  // Create Room Workflow
  /** @type {HTMLButtonElement} */
  const createRoomBtn = document.querySelector("#create-room-btn");
  createRoomBtn.addEventListener("click", () => {
    if (connections.createRoomValidation !== null) {
      connections.createRoomValidation.close();
    }
    const validationSocket = new WebSocket("/chat/api/v1/form-validation", `csrf${csrfToken()}`);
    connections.createRoomValidation = validationSocket;
    setupLoggingHandlers(validationSocket, "form-validation/create-room");
    openModal(makeCreateRoomModal(validationSocket));
  });

  // Join Room Workflow
  /** @type {HTMLButtonElement} */
  const joinRoomBtn = document.querySelector("#join-room-btn");
  joinRoomBtn.addEventListener("click", () => {
    openModal(makeJoinRoomModal());
  });

  // User Logout Workflow
  /** @type {HTMLButtonElement} */
  const logoutBtn = document.querySelector("#logout-btn");
  logoutBtn.addEventListener("click", () => {
    logOut();
  });
});
