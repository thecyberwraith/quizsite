import { getWebsocketURLFromLocation } from "./util.js"

export class LiveQuizWebsocket {
    constructor(relative_url) {
        let url = getWebsocketURLFromLocation(relative_url);
        this.socket = new WebSocket(url);

        this.socket.onopen = this.onSocketOpen;
        this.socket.onclose = this.onSocketClose;
        this.socket.onmessage = this.onSocketMessage;
    }

    onSocketOpen(e) {
        console.log(e);
    }

    onSocketClose(e) {
        console.log(e);
    }

    onSocketMessage(e) {
        console.log(e);
    }
}

function establish_connection() {
    if (games_socket !== null) {
        games_socket.close();
    }

    games_socket = new WebSocket(websocket_url);

    games_socket.onmessage = function(e) {
        if (e.data.error) {
            console.error('Problem from the server:', e.error)
        }
        console.log('Message', e.data);
    }
    games_socket.onclose = function(e) {
        if (!e.wasClean) {
            console.warn('Whoops. Socket closed.', e);
            setTimeout(establish_connection, 15000);
            }
        else {
            console.info('Clean disconnection.');
        }
    }
    games_socket.onopen = function(e) {
        console.log('It is open.')
    }
}