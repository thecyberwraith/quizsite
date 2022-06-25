import { LiveQuizWebsocket } from "./websocket.js";
import { ClientViewRenderer } from "./render.js";

let connection = null;

export function setup(quiz_code) {
    connection = new LiveQuizWebsocket(
        '/ws/live/host/' + quiz_code,
        new HostViewRenderer());
}

class HostViewRenderer extends ClientViewRenderer {
    renderBuzzArea(data) {
        let newArea = document.createElement('div');
        if (data.status != 'none') {
            let p = document.createElement('p');
            newArea.appendChild(p);

            if (data.status == 'open')
                p.innerHTML = 'Waiting for someone to buzz in!'
            else 
                p.innerHTML = 'Player ' + data.name + ' buzzed first!'
            
            let button = document.createElement('button')
            button.onclick = (e) => {sendBuzzRequest('end');};
            button.innerHTML = 'Stop Buzz Event'
            newArea.appendChild(button);
        }
        this.swapContent(newArea, this.buzzDiv);
    }
    renderBoardQuestion(question_data) {
        let element = document.createElement('a');
        element.innerHTML = question_data.value;
        element.onclick = (e) => {sendViewRequest('question', question_data.id);};
        return element;
    }

    renderQuestion(question_data) {
        super.renderQuestion(question_data);
        let element = this.contentDiv.children[0];
        let buttons = this.createButtons(['Back', 'Show Answer', '(Re)start Buzz']);
        
        buttons.children[0].onclick = (e) => {sendViewRequest('quiz_board');};
        buttons.children[1].onclick = (e) => {sendViewRequest('answer', question_data.id);};
        buttons.children[2].onclick = (e) => {sendBuzzRequest('start');};
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

function sendBuzzRequest(action) {
    connection.socket.send(JSON.stringify({
        type: 'manage buzz',
        payload: {
            'action': action
        }
    }));
}