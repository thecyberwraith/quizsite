import { LiveQuizWebsocket } from "./websocket.js"

export function setup(quiz_code) {
    new LiveQuizWebsocket('/ws/live/host/' + quiz_code);
}