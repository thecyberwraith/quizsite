import { LiveQuizWebsocket } from "./websocket.js"
import { ClientViewRenderer } from "./render.js"

let connection = null;

export function setup(quiz_code) {
    connection = new LiveQuizWebsocket(
        '/ws/live/play/' + quiz_code,
        new PlayerRenderer());
}


class PlayerRenderer extends ClientViewRenderer {

}