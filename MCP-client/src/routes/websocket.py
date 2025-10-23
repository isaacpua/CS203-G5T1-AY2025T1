from fastapi import WebSocket, WebSocketDisconnect

class WebSocketManager:
    def __init__(self):
        self.connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.connections:
            self.connections.remove(websocket)

    async def emit(self, event_type: str, payload: dict = {}):
        message = {"event": event_type, **payload}
        print(f"WS emit: {message}")
        for ws in self.connections:
            try:
                await ws.send_json(message)
            except Exception as e:
                print(f"Failed to send WebSocket message: {e}")

# Singleton instance
ws_manager = WebSocketManager()
