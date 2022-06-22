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
        this.socket.onopen = (e) => this.onSocketOpen(e);
        this.socket.onclose = (e) => this.onSocketClose(e);
        this.socket.onmessage = (e) => this.onSocketMessage(e);
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
        let data = JSON.parse(e.data);
        let type = data.type;
        let payload = data.payload;

        switch (type) {
            case 'set view':
                this.render_view(payload);
                break;
            default:
                console.error('Unmatched message');
                console.log(typeof(e.data));
            }
    }

    render_view(payload) {}
}