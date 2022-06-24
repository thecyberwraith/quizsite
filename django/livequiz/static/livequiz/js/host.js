import { LiveQuizWebsocket } from "./websocket.js";
import { ClientViewRenderer } from "./render.js";

let connection = null;

export function setup(quiz_code) {
    connection = new LiveQuizWebsocket(
        '/ws/live/host/' + quiz_code,
        new HostViewRenderer());
}

class HostViewRenderer extends ClientViewRenderer {
    renderBoardQuestion(question_data) {
        let element = document.createElement('a');
        element.innerHTML = question_data.value;
        element.onclick = (e) => {sendViewRequest('question', question_data.id);};
        return element;
    }

    renderQuestion(question_data) {
        super.renderQuestion(question_data);
        let element = this.contentDiv.children[0];
        let buttons = this.createButtons(['Back', 'Show Answer']);
        
        buttons.children[0].onclick = (e) => {sendViewRequest('quiz_board');};
        buttons.children[1].onclick = (e) => {sendViewRequest('answer', question_data.id);};
        
        element.appendChild(buttons);
    }

    renderAnswer(question_data) {
        super.renderAnswer(question_data);

        let element = this.contentDiv.children[0];

        let buttons = this.createButtons(['Mark Done']);
        buttons.children[0].onclick = (e) => {sendViewRequest('quiz_board');};
        
        element.appendChild(buttons);
    }

    createButtons(button_names) {
        let container = document.createElement('div');

        button_names.forEach( (button_name) => {
            let button = document.createElement('button');
            button.innerHTML = button_name;
            container.appendChild(button);
        }
        )

        return container;
    }
}

function sendViewRequest(view, question_id=null) {
    connection.socket.send(JSON.stringify({
        type: 'set view',
        payload: {
            'view': view,
            'question_id': question_id
        }
    }))
}