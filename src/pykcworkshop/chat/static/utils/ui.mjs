import { currentUser } from "./shared_state.mjs";

/** Convert a server-time string to a localized date and time display string.
 * @param {string} timestamp
 * @returns {string}
 */
function parseServerTimestamp(timestamp) {
  return new Date(timestamp).toLocaleString();
}

/** Build and return a structured chat message that can be added to a chatroom UI.
 * @param {{user_name: string, content: string, timestamp: string}} msgData The structured chat message.
 * @returns {HTMLDivElement}
 */
function buildNewChatMessageEl(msgData) {
  const newMsgContainer = document.createElement("div");
  newMsgContainer.classList.add("flex", "flex-col");
  const metaDataContainer = document.createElement("div");
  metaDataContainer.classList.add("flex", "flex-row");
  newMsgContainer.appendChild(metaDataContainer);
  const userNameEl = document.createElement("b");
  userNameEl.textContent = msgData.user_name;
  userNameEl.classList.add("mr-2");
  metaDataContainer.appendChild(userNameEl);
  const ts = document.createTextNode(parseServerTimestamp(msgData.timestamp));
  metaDataContainer.appendChild(ts);

  const newMsg = document.createElement("pre");
  newMsg.textContent = msgData.content;
  newMsgContainer.appendChild(newMsg);
  return newMsgContainer;
}

/** Append a structured chat message to a scrolling chat window/ui element.
 * @param {HTMLDivElement} msgList The scrolling chat element to add the message to.
 * @param {{user_name: string, content: string, timestamp: string}} msgData The structured chat message.
 */
export function appendMessageToChatUI(msgList, msgData) {
  const newMsgContainer = buildNewChatMessageEl(msgData);
  msgList.appendChild(newMsgContainer);
  if (msgData.user_name === currentUser().userName) {
    msgList.scrollTo(0, msgList.scrollHeight);
  }
}

/** Prepend a structured chat message to a scrolling chat window/ui element.
 * @param {HTMLDivElement} msgList The scrolling chat element to add the message to.
 * @param {{user_name: string, content: string, timestamp: string}} msgData The structured chat message.
 */
export function prependMessageToChatUI(msgList, msgData) {
  const newMsgContainer = buildNewChatMessageEl(msgData);
  const oldHeight = msgList.scrollHeight;
  msgList.prepend(newMsgContainer);
  msgList.scrollTo(0, msgList.scrollHeight - oldHeight);
}

export function makeErrMsgEl() {
  const errMsg = document.createElement("p");
  errMsg.style.color = "red";
  errMsg.classList.add("hidden");
  return errMsg;
}
