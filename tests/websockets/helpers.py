import time

from pykcworkshop import chat


def validInputMsg(endpoint_url: str, user_record: chat.db.models.User) -> dict:
    match endpoint_url.split("/").pop():
        case "chat-message":
            return {"user_name": user_record.name, "content": f"Message from {user_record.name}"}
        case "member-status":
            return {
                "user_id": user_record.id,
                "user_name": user_record.name,
                "user_status": "Online",
            }
        case "client-sync":
            return {"arbitrary_key": f"Some arbitrary message sent from {user_record.name}"}
        case "chat-history":
            return {"timestamp": int(time.time() * 1000), "chunk_size": 10}
        case "direct-message":
            return {
                "user_name": user_record.name,
                "content": f"Direct message from {user_record.name}",
            }
        case "form-validation":
            return {"type": "chat-message", "content": "Some message content for length checking."}
        case _:
            assert False, "This branch should never execute. Check the `endpoint_url`."
