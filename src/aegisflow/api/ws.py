"""WebSocket Streaming Replay with Play/Pause/Seek/Speed Controls.

See PROJECT_ROADMAP.md §5.2 & Task 12.
"""

import asyncio
import json
from typing import Dict, Any, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from aegisflow.api.deps import get_app_state
from aegisflow.api.routes_stream import build_tick_payload

router = APIRouter(tags=["WebSocket Replay"])


@router.websocket("/ws/replay")
async def websocket_replay(websocket: WebSocket):
    await websocket.accept()
    app_state = get_app_state()

    if app_state.df is None or not app_state.ticks_cache:
        await websocket.send_text(json.dumps({
            "type": "error",
            "error": {"code": "NOT_READY", "message": "Simulation data not loaded"}
        }))
        await websocket.close()
        return

    df = app_state.df
    total_hours = len(df)
    ticks_cache = app_state.ticks_cache

    current_index = 0
    is_playing = False
    speed = 60  # ticks per second
    strategies = ["aegisflow", "baseline2_static"]

    async def incoming_listener():
        nonlocal current_index, is_playing, speed, strategies
        try:
            while True:
                msg_text = await websocket.receive_text()
                try:
                    cmd_data = json.loads(msg_text)
                    if not isinstance(cmd_data, dict):
                        continue
                    cmd = cmd_data.get("cmd")

                    if cmd == "play":
                        if "speed" in cmd_data:
                            speed = max(1, min(2000, int(cmd_data["speed"])))
                        if "from_index" in cmd_data:
                            current_index = max(0, min(total_hours - 1, int(cmd_data["from_index"])))
                        if "strategies" in cmd_data and isinstance(cmd_data["strategies"], list):
                            strategies = cmd_data["strategies"]
                        is_playing = True

                    elif cmd == "pause":
                        is_playing = False

                    elif cmd == "seek":
                        idx = int(cmd_data.get("index", 0))
                        current_index = max(0, min(total_hours - 1, idx))
                        # Emit instant preview tick upon seek
                        tick = build_tick_payload(current_index, df, ticks_cache, strategies, preds_df=app_state.preds_df)
                        await websocket.send_text(json.dumps({"type": "tick", "payload": tick}))

                    elif cmd == "speed":
                        speed = max(1, min(2000, int(cmd_data.get("value", 60))))
                except (json.JSONDecodeError, ValueError, TypeError):
                    # Ignore malformed frame without terminating listener
                    continue

        except WebSocketDisconnect:
            pass
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    listener_task = asyncio.create_task(incoming_listener())

    try:
        while True:
            if listener_task.done():
                break

            if not is_playing:
                await asyncio.sleep(0.05)
                continue

            if current_index >= total_hours:
                await websocket.send_text(json.dumps({"type": "eof"}))
                is_playing = False
                continue

            # Frame rate cap: at most 30 socket packets per second
            if speed <= 30:
                tick = build_tick_payload(current_index, df, ticks_cache, strategies, preds_df=app_state.preds_df)
                await websocket.send_text(json.dumps({"type": "tick", "payload": tick}))
                current_index += 1
                await asyncio.sleep(1.0 / speed)
            else:
                # Batch ticks to keep message frequency <= 30/s
                t_frame_start = asyncio.get_running_loop().time()
                batch_size = max(2, int(round(speed / 30.0)))
                batch_end = min(total_hours, current_index + batch_size)
                batch_ticks = [
                    build_tick_payload(i, df, ticks_cache, strategies, preds_df=app_state.preds_df)
                    for i in range(current_index, batch_end)
                ]
                await websocket.send_text(json.dumps({
                    "type": "tick",
                    "batched": True,
                    "count": len(batch_ticks),
                    "ticks": batch_ticks,
                    "payload": batch_ticks[-1],
                }))
                current_index = batch_end
                target_duration = len(batch_ticks) / speed
                elapsed = asyncio.get_running_loop().time() - t_frame_start
                sleep_time = max(0.001, target_duration - elapsed)
                await asyncio.sleep(sleep_time)

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        if not listener_task.done():
            listener_task.cancel()
            try:
                await listener_task
            except (asyncio.CancelledError, Exception):
                pass
