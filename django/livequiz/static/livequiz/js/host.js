import { LiveQuizWebsocket } from "./websocket.js"

const contentDiv = document.getElementById('livequiz_content_div');
const templateBoard = document.getElementById('template_livequiz_board');

export function setup(quiz_code) {
    new LiveQuizWebsocket('/ws/live/host/' + quiz_code);
}