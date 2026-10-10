import logging
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime

from backend.services.websocket import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websockets"])

@router.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """
    Main WebSocket endpoint for the frontend dashboard.
    
    This maintains a persistent bidirectional connection with the client, sends an 
    initial confirmation payload, and listens for 'ping' messages from the client 
    to keep the connection alive (heartbeat). Any real-time disaster updates are 
    pushed through this socket dynamically by the global ConnectionManager.
    
    Keep-alive mechanism:
    - Client sends ping every 15 seconds
    - Server responds with pong
    - Connection stays open indefinitely (no timeout)
    """
    await manager.connect(websocket)
    import time
    last_message_time = 0.0
    
    try:
        # Send immediate connection success message
        await websocket.send_json({
            "type": "connection_established",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"message": "Connected to TerraGrid Real-Time Engine"}
        })
        
        while True:
            try:
                # Use asyncio.wait_for with 120s timeout per message
                # This allows heartbeat (15s) to work + adds buffer for slow connections
                raw_data = await asyncio.wait_for(
                    websocket.receive_text(), 
                    timeout=120.0
                )
            except asyncio.TimeoutError:
                # No message received in 120s - likely client disconnected
                # Log and close gracefully
                logger.warning("WebSocket receive timeout (120s) - no heartbeat from client")
                break
            
            # Rate Limiting (Max 2 messages per second)
            current_time = time.time()
            if current_time - last_message_time < 0.5:
                logger.debug("WebSocket rate limit exceeded. Dropping spam message.")
                continue
            last_message_time = current_time

            try:
                import json
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                logger.debug("Received invalid JSON over WebSocket. Ignoring message.")
                continue

            if data.get("type") == "ping":
                # Respond with pong to keep connection alive
                try:
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                except Exception as e:
                    logger.debug(f"Failed to send pong: {e}")
                    break
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.exception(f"Unexpected WebSocket error.")
        manager.disconnect(websocket)
