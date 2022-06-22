import { LiveQuizWebsocket } from "./websocket.js"

const contentDiv = document.getElementById('livequiz_content_div');
const templateBoard = document.getElementById('template_livequiz_board');
let connection = null;

export function setup(quiz_code) {
    connection = new LiveQuizWebsocket('/ws/live/host/' + quiz_code);
    connection.render_view = render_view;
}

function render_view(payload) {
    const view = payload.view;
    const data = payload.data;
    contentDiv.children[0].remove();

    let board = document.createElement('div');
    board.id = 'livequiz_board'

    Object.keys(data).forEach( function (category) {
        let category_div = document.createElement('div');
        let category_name = document.createElement('h2');
        category_name.innerHTML = category;

        category_div.appendChild(category_name);

        data[category].forEach( (question) => {
            if (question == null) {
                category_div.appendChild(document.createElement('div'));
            }
            else {
                let element = document.createElement('a');
                element.innerHTML = question.value;
                category_div.appendChild(element);
            }
        })

        board.appendChild(category_div);
    })

    contentDiv.appendChild(board);
}