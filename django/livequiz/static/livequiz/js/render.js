export class ClientViewRenderer {
    constructor() {
        this.contentDiv = document.getElementById('livequiz_content_div');

    }

    swapContent(new_child) {
        this.contentDiv.children[0].remove();
        this.contentDiv.appendChild(new_child);
    }

    renderTemplate(which, data=null) {
        let template = document.getElementById(which);
        if (!template) {
            console.error('Missing template id', which);
            return;
        }
        this.swapContent(template.content.cloneNode(true));

        switch (which) {
            case 'connection-refused-template':
                let ul = this.contentDiv.children[0].querySelector('ul');
                data.forEach( (line) => {
                    let li = document.createElement('li');
                    li.innerHTML = line;
                    ul.appendChild(li);
                });
        }
    }

    renderView(payload) {
        let name = payload.view
        let data = payload.data
        switch (name) {
            case 'quiz_board':
                this.renderBoard(data);
                break;
            case 'question':
                this.renderQuestion(data);
                break;
            case 'answer':
                this.renderAnswer(data);
                break;
            default:
                console.error('Cannot render view', name);
        }
    }

    renderBoard(categories) {
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
    
        this.swapContent(board);
    }

    renderBoardQuestion(question_data) {
        let element = document.createElement('p');
        element.innerHTML = question_data.value;
        return element;
    }

    renderQuestion(question_data) {
        let element = document.createElement('div');
        let question = document.createElement('p');
        question.innerHTML = question_data.text;
        element.appendChild(question);

        this.swapContent(element);
    }

    renderAnswer(question_data) {
        let element = document.createElement('div');
        let question = document.createElement('p');
        question.innerHTML = question_data.text;
        element.appendChild(question);

        let answer = document.createElement('p');
        answer.innerHTML = question_data.answer;
        element.appendChild(answer);
        
        this.swapContent(element);
    }
}