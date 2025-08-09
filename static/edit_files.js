const input_file_names = [];
const input_file_contents = [];
const output_file_names = [];
const input_file_list = document.getElementById('input-file-list');
const output_file_list = document.getElementById('output-file-list');

const input_file_input = [];
const input_content_input = [];
const output_file_input = [];

let version = 0;
function initialize_file_list(files) {
    console.log(files);
    if (files["input_name"] !== undefined) {
        console.log(files["input_name"]);
        for (let i = 0; i < files["input_name"].length; i++) {
            input_file_names.push(files["input_name"][i]);
            input_file_contents.push(files["input_content"][i]);
        }
    }
    if (files["output_name"] !== undefined) {
        console.log(files["output_name"]);
        for (let i = 0; i < files["output_name"].length; i++) {
            output_file_names.push(files["output_name"][i]);
        }
    }
    // idx_input = 0;
    // idx_output = 0;
    // files.forEach((file) => {
    // const parts = file.split(',');
    // if (parts[0] === 'input') {
    //     input_file_names.push(parts[1]);
    //     input_files_index.push(idx_input++);
    // } else if (parts[0] === 'output') {
    //     output_file_names.push(parts[1]);
    //     output_files_index.push(idx_output++);
    // }
    // });
    refresh_file_list();
}

function refresh_file_list() {
    input_file_list.innerHTML = '';
    output_file_list.innerHTML = '';
    input_file_input.length = 0;
    output_file_input.length = 0;
    console.log(input_file_names);
    console.log(output_file_names);
    if (input_file_names.length == 0) {
        const file_item = document.createElement('li');
        file_item.innerHTML = `
            <button class="btn btn-outline-primary" onclick="add_prev_input(0)">追加</button>
        `;
        input_file_list.appendChild(file_item);
    }
    input_file_names.forEach((name, i) => {
        const file_item = document.createElement('li');
        file_item.innerHTML = `
            <button class="btn btn-outline-primary" onclick="add_prev_input(${i})">上に追加</button>
            <input type="text" class="editable" id="file-${i}" value="${name}">
            <textarea class="editable w-100" id="file-${i}-content" rows="10"></textarea>
            <button class="btn btn-outline-primary" onclick="add_next_input(${i})">下に追加</button>
            <button class="btn btn-outline-secondary" onclick="move_up_input(${i})">↑</button>
            <button class="btn btn-outline-secondary" onclick="move_down_input(${i})">↓</button>
            <button class="btn btn-outline-danger" onclick="delete_file_input(${i})">削除</button>
        `;
        input_file_list.appendChild(file_item);
        input_file_input[i] = document.getElementById(`file-${i}`);
        input_file_input[i].addEventListener('input', () => { input_file_names[i] = input_file_input[i].value; });

        input_content_input[i] = document.getElementById(`file-${i}-content`);
        input_content_input[i].addEventListener('input', () => { input_file_contents[i] = input_content_input[i].value; });
        input_content_input[i].value = input_file_contents[i];

    });

    if (output_file_names.length == 0) {
        const file_item = document.createElement('li');
        file_item.innerHTML = `
            <button class="btn btn-outline-primary" onclick="add_prev_output(0)">追加</button>
        `;
        output_file_list.appendChild(file_item);
    }
    output_file_names.forEach((name, i) => {
        const file_item = document.createElement('li');
        file_item.innerHTML = `
            <button class="btn btn-outline-primary" onclick="add_prev_output(${i})">上に追加</button>
            <input type="text" class="editable" id="output-file-${i}" value="${name}">
            <button class="btn btn-outline-primary" onclick="add_next_output(${i})">下に追加</button>
            <button class="btn btn-outline-secondary" onclick="move_up_output(${i})">↑</button>
            <button class="btn btn-outline-secondary" onclick="move_down_output(${i})">↓</button>
            <button class="btn btn-outline-danger" onclick="delete_file_output(${i})">削除</button>
        `;
        output_file_list.appendChild(file_item);
        output_file_input[i] = document.getElementById(`output-file-${i}`);
        output_file_input[i].addEventListener('input', () => { output_file_names[i] = output_file_input[i].value; });
    });
}

function add_next_input(index) {
    input_file_names.splice(index + 1, 0, '');
    input_file_contents.splice(index + 1, 0, '');
    refresh_file_list();
}

function add_next_output(index) {
    output_file_names.splice(index + 1, 0, '');
    refresh_file_list();
}

function add_prev_input(index) {
    input_file_names.splice(index, 0, '');
    input_file_contents.splice(index, 0, '');
    refresh_file_list();
}
function add_prev_output(index) {
    output_file_names.splice(index, 0, '');
    refresh_file_list();
}

function move_up_input(index) {
    if (index > 0) {
        [input_file_names[index - 1], input_file_names[index]] = [input_file_names[index], input_file_names[index - 1]];
        [input_file_contents[index - 1], input_file_contents[index]] = [input_file_contents[index], input_file_contents[index - 1]];
        refresh_file_list();
    }
}
function move_up_output(index) {
    if (index > 0) {
        [output_file_names[index - 1], output_file_names[index]] = [output_file_names[index], output_file_names[index - 1]];
        refresh_file_list();
    }
}

function move_down_input(index) {
    if (index < input_file_names.length - 1) {
        [input_file_names[index + 1], input_file_names[index]] = [input_file_names[index], input_file_names[index + 1]];
        [input_file_contents[index + 1], input_file_contents[index]] = [input_file_contents[index], input_file_contents[index + 1]];
        refresh_file_list();
    }
}

function move_down_output(index) {
    if (index < output_file_names.length - 1) {
        [output_file_names[index + 1], output_file_names[index]] = [output_file_names[index], output_file_names[index + 1]];
        refresh_file_list();
    }
}

function delete_file_input(index) {
    const file_name = input_file_names[index];
    if (!confirm(`本当に「${file_name}」を削除して良いですか？`)) {
        return;
    }
    input_file_names.splice(index, 1);
    input_file_contents.splice(index, 1);
    refresh_file_list();
}

function delete_file_output(index) {
    const file_name = output_file_names[index];
    if (!confirm(`本当に「${file_name}」を削除して良いですか？`)) {
        return;
    }
    output_file_names.splice(index, 1);
    refresh_file_list();
}

function save_files(report_index, prevurl = "#") {
    const file_data = { report_index: report_index, input_name: input_file_names, output_name: output_file_names, input_content: input_file_contents };
    const file_data_json = JSON.stringify(file_data);
    console.log(file_data_json);
    if (!confirm('変更を保存しますか？')) {
        return;
    }

    fetch('/save_files', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: file_data_json
    });
    location.replace(prevurl);
}

function cancel_edit_files(prevurl = "#") {
    if (!confirm('変更を破棄しますか？')) {
        return;
    }
    location.replace(prevurl);
}