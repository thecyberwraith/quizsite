import { LiveQuizWebsocket } from "./websocket.js"
import { ClientViewRenderer } from "./render.js"

let connection = null;

export function setup(quiz_code) {
    connection = new LiveQuizWebsocket(
        '/ws/live/play/' + quiz_code,
        new PlayerRenderer());
}


class PlayerRenderer extends ClientViewRenderer {
    constructor() {
        super()
        this.playerDiv = document.getElementById('livequiz_player_div');
    }

    renderPlayerInfo(data) {
        console.log('New player info:', data);
        let newDiv = document.createElement('div');
        let p = document.createElement('p');
        p.innerHTML = `Playing as "${data.name}"`;
        newDiv.appendChild(p);

        let button = document.createElement('button');
        button.onclick = (e) => {
            let new_name = prompt('What is your name?', data.name);
            sendPlayerUpdateRequest(new_name);
        }
        button.innerHTML = 'Change Name';

        newDiv.appendChild(button);

        this.swapContent(newDiv, this.playerDiv);
    }
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

function sendPlayerUpdateRequest(new_name) {
    connection.socket.send(JSON.stringify({
        type: 'set player name',
        payload: {
            name: new_name
        }
    }))
}