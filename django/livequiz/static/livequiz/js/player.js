import { LiveQuizWebsocket } from "./websocket.js"
import { ClientViewRenderer } from "./render.js"

let connection = null;

export function setup(quiz_code) {
    connection = new LiveQuizWebsocket(
        '/ws/live/play/' + quiz_code,
        new PlayerRenderer());
}


class PlayerRenderer extends ClientViewRenderer {
    renderBuzzArea(data) {
        let newDiv = document.createElement('div')

        if (data.status != 'none') {
            if (data.status == 'open') {
                let button = document.createElement('button');
                button.innerHTML = 'Buzz In!'
                button.onclick = (e) => {sendBuzzInEvent();};
                newDiv.appendChild(button);
            }
            else {
                let p = document.createElement('p');
                p.innerHTML = `${data.name} was the first to buzz in.`;

                newDiv.appendChild(p);
            }
        }
        this.swapContent(newDiv, this.buzzDiv);
    }
}

function sendBuzzInEvent() {
    connection.socket.send(JSON.stringify({
        type: 'buzz in',
        payload: {}
    }))
}