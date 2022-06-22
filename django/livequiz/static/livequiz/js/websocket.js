import { getWebsocketURLFromLocation } from "./util.js"

export class LiveQuizWebsocket {
    constructor(relative_url) {
        this.relative_url = relative_url;
        this.socket = null;
        this.establishConnection();
    }

    establishConnection() {
        let url = getWebsocketURLFromLocation(this.relative_url);
        this.socket = new WebSocket(url);
        this.socket.onopen = this.onSocketOpen;
        this.socket.onclose = this.onSocketClose;
        this.socket.onmessage = this.onSocketMessage;
    }

    onSocketOpen(e) {
        console.log(e);
    }

    onSocketClose(e) {
        if (!e.wasClean) {
            if (this.socket !== null) {
                this.socket.close();
            }
            console.log('Attempting to reconnect in 5 seconds.');
            setTimeout(this.establishConnection, 5000);
        }
        else {
            console.info('Server intentionally closed connection.');
        }
    }

    onSocketMessage(e) {
        console.log('Message: ', e.data);
    }
}