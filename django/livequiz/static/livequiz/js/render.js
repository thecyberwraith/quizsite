const contentDiv = document.getElementById('livequiz_content_div');

export class ClientViewRenderer {
    renderTemplate(which) {
        let template = document.getElementById(which);
        if (!template) {
            console.error('Missing template id', which);
            return;
        }
        contentDiv.children[0].remove()
        contentDiv.appendChild(template.content.cloneNode(true));
    }

    renderView(payload) {
        let name = payload.view
        let data = payload.data
        switch (name) {
            case 'quiz_board':
                this.renderBoard(data);
                break;
            default:
                console.error('Cannot render view', name);
        }
    }

    renderBoard(categories) {
        contentDiv.children[0].remove();
    
        let board = document.createElement('div');
        board.id = 'livequiz_board'
    
        Object.keys(categories).forEach( function (category) {
            let category_div = document.createElement('div');
            let category_name = document.createElement('h2');
            category_name.innerHTML = category;
    
            category_div.appendChild(category_name);
    
            categories[category].forEach( (question) => {
                if (question == null) {
                    category_div.appendChild(document.createElement('div'));
                }
                else {
                    category_div.appendChild(this.renderBoardQuestion(question));
                }
            }, this);
    
            board.appendChild(category_div);
        }, this)
    
        contentDiv.appendChild(board);
    }

    renderBoardQuestion(question_data) {
        let element = document.createElement('p');
        element.innerHTML = question_data.value;
        return element;
    }
}