import { LiveQuizWebsocket } from "./websocket.js";
import { ClientViewRenderer } from "./render.js";

let connection = null;

export function setup(quiz_code) {
    connection = new LiveQuizWebsocket('/ws/live/host/' + quiz_code);
    let renderer = new HostViewRenderer();
    connection.renderView = (payload) => {renderer.renderView(payload);};
}

class HostViewRenderer extends ClientViewRenderer {
    renderBoardQuestion(question_data) {
        let element = document.createElement('a');
        element.innerHTML = question_data.value;
        element.onclick = (e) => {sendViewRequest('question', question_data.id);};
        return element;
    }
}

function sendViewRequest(view, question_id=null) {
    console.log('Setting view to ', view);
}