if (typeof spreadsheets == 'undefined') {
    var spreadsheets = function () {
        var sheets = {};
        ajax_helpers.command_functions.send_spreadsheet = function (command) {
            data = sheets[command.table_id].getData();
            ajax_helpers.post_json({data: {button: 'spreadsheet', data: data}});
        };

        ajax_helpers.command_functions.set_cell = function (command) {
            data = sheets[command.table_id].setValue(command.cell, command.value);
        };

        var custom_column = {
            closeEditor: function (cell, save) {
                var value = cell.children[0].value;
                cell.innerHTML = value;
                return {'data': value, class: cell.data['class']};
            },

            openEditor: function (cell, obj) {
                var createEditor = function (type) {
                    var info = cell.getBoundingClientRect();
                    var editor = document.createElement(type);
                    editor.style.width = (info.width) + 'px';
                    editor.style.height = (info.height - 2) + 'px';
                    editor.style.minHeight = (info.height - 2) + 'px';
                    cell.classList.add('editor');
                    cell.innerHTML = '';
                    cell.appendChild(editor);
                    return editor;
                };

                value = cell.innerHTML;
                var editor = createEditor('input');
                editor.focus();
                editor.value = value;
                editor.onblur = function () {
                    obj.jspreadsheet.closeEditor(cell, true);
                };
                editor.scrollLeft = editor.scrollWidth;
            },

            createCell: function (cell) {
                try {
                    cell.data = JSON.parse(cell.innerHTML);
                } catch (e) {
                    cell.data = {data: ''};
                }
                cell.innerHTML = cell.data['data'];
                $(cell).addClass(cell.data['class']);
                return cell;
            },

            getValue: function (cell) {
                return cell.data;
            },

            setValue: function (cell, value) {
                if (typeof (value) == 'object') {
                    cell.data = value;
                    $(cell).removeClass();
                    $(cell).addClass(value.class);
                } else if (value.slice(-1) === '}' && value.slice(0, 1) == '{') {
                    cell.data = JSON.parse(value);
                } else {
                    cell.data['data'] = value;
                }
                cell.innerHTML = cell.data['data'];
            }
        };

        function get_sheet_data(){
            var modal_div = django_modal.modal_div();
            var sheets = $('.sheet-div', modal_div);
            var sheet_data = {};
            for (var i=0; i<sheets.length; i++){
                sheet_data[sheets[i].id] = JSON.stringify(sheets[i].jspreadsheet.getData())
            }
            return sheet_data;
        }

        function spreadsheet_change(instance, cell, x, y, value) {
            ajax_helpers.post_json({data: {row: 'changed', data: instance.jspreadsheet.getRowData(y), row_no: y, column: x}})
        }

        function spreadsheet_change_whole(instance, cell, x, y, value) {
            ajax_helpers.post_json({data: {row: 'changed', data: instance.jspreadsheet.getData(), row_no: y, column: x}})
        }

        return {
            sheets,
            custom_column,
            get_sheet_data,
            spreadsheet_change,
            spreadsheet_change_whole,
        };
    }();
}
