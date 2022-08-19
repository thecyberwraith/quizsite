import { getWebsocketURLFromLocation } from "./util.js"

export class LiveQuizWebsocket {
    constructor(relativeURL, renderer) {
        this.renderer = renderer;
        this.relativeURL = relativeURL;
        this.socket = null;
        this.lastMessage = null;
        this.establishConnection();
    }

    establishConnection() {
        let url = getWebsocketURLFromLocation(this.relativeURL);
        console.log('Attempting websocket at', url);
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
            console.warn('Detecting unclean disconnect from server.');
            if (this.socket !== null) {
                this.socket.close();
            }
            this.renderer.renderTemplate('connection-error-template');
            console.log('Attempting to reconnect in 5 seconds.');
            setTimeout(() => {this.establishConnection();}, 5000);
        }
        else {
            console.info('Server intentionally closed connection.');
            if (this.lastMessage) {
                if (this.lastMessage.type == 'error') {
                this.renderer.renderTemplate('connection-refused-template', this.lastMessage.payload)
                }
                else if (this.lastMessage.type != 'terminated') {
                    this.renderer.renderTemplate('unknown-error-template');
                }
            }
            else {
                this.renderer.renderTemplate('unknown-error-template');
            }
        }
    }

    onSocketMessage(e) {
        let data = JSON.parse(e.data);
        let type = data.type;
        let payload = data.payload;

        switch (type) {
            case 'set view':
                this.renderer.renderView(payload);
                break;
            case 'buzz event':
                this.renderer.renderBuzzArea(payload);
                break;
            case 'player update':
                this.renderer.renderPlayerInfo(payload);
                break;
            case 'info':
                console.log('Server Message:', payload);
                break;
            case 'error':
                payload.forEach( line => console.error('Server Error:', line) )
                break;
            case 'terminated':
                console.warn('The quiz has been destroyed!');
                this.renderer.renderTemplate('terminated-quiz-template');
            default:
                console.error('Unmatched message', type, e.data);
        }
        this.lastMessage = data;
    }

}