/** Bind some JS code to run on page load.
 * @param {function} callback A 0-arity function to call once the page content is loaded.
 */
export const onPageLoad = (callback) => {
  if (document.readyState !== "loading") {
    callback();
  } else {
    document.addEventListener("DOMContentLoaded", () => {
      callback();
    });
  }
};

/** Setup basic printf handlers for the open, close, and error events for a WebSocket.
 * @param {WebSocket} socket
 * @param {string} name
 */
export function setupLoggingHandlers(socket, name) {
  socket.addEventListener("open", (_ev) => {
    console.log(`${name} socket opened successfully.`);
  });

  socket.addEventListener("close", (ev) => {
    console.log(
      `${name} socket closed ${ev.wasClean ? "cleanly" : "uncleanly"} with code ${ev.code}`,
    );
  });

  socket.addEventListener("error", () => {
    console.log(`${name} socket closed with an unknown error.`);
  });
}
