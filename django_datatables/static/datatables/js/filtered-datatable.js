if (typeof django_datatables === 'undefined') {
    var django_datatables = function () {
        var setup = {}
        var DataTables = {}

        function b_r(button){
            var command = $(button).attr('data-command')
            var row_id = $(button).closest('tr').attr('id')
            var table_id = $(button).closest('table').attr('id')
            DataTables[table_id].send_row(command, row_id)
        }

        var utilities = {

            getCookie: function (name) {
                var cookieValue = null;
                if (document.cookie && document.cookie !== '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        if (cookie.substring(0, name.length + 1) === (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            },

            process_commands: function(commands){
                for (var c = 0; c < commands.length; c++){
                    var dt_api = django_datatables.DataTables[commands[c].table].table.api()
                    switch (commands[c].command) {
                        case 'delete_row':
                            dt_api.row('#' + commands[c].row).remove()
                            dt_api.draw(false)
                            break;
                        case 'refresh_row':
                            dt_api.row('#' + commands[c].row).data(commands[c].data).invalidate()
                    break;
                    }
                }
            },

            post_data: function (url, data) {
                $.ajax({
                    url: url,
                    method: 'post',
                    data: data,
                    beforeSend: function (xhr) {
                        xhr.setRequestHeader("X-CSRFToken", utilities.getCookie('csrftoken'));
                    },
                    cache: false,
                    success: function (form_response, status, jqXHR) {
                        content_disposition = jqXHR.getResponseHeader('Content-Disposition')
                        if (typeof (content_disposition) == 'string' && content_disposition.indexOf('attachment') > -1) {
                            blob = new Blob([form_response], {type: "octet/stream"})
                            download_url = window.URL.createObjectURL(blob);
                            a = document.createElement('a');
                            a.style.display = 'none';
                            a.href = download_url;
                            a.download = content_disposition.split('"')[1];
                            document.body.appendChild(a);
                            a.click();
                            window.URL.revokeObjectURL(download_url);
                            alert('your file has downloaded');
                        } else if (typeof (form_response) == 'object') {
                            utilities.process_commands(form_response)
                        }
                    }
                })
            }
        }

        var columnsearch = function (settings, data, dataIndex, row_data) {
            if (settings.sTableId in DataTables) {
                for (var f = 0; f < DataTables[settings.sTableId].filters.length; f++) {
                    if (!DataTables[settings.sTableId].filters[f].filter(row_data)) return false
                }
                return true
            }
        }
        $.fn.dataTable.ext.search.push(columnsearch)

        function init_setup(table_id) {
            if (typeof (setup[table_id]) === 'undefined')
                setup[table_id] = {}
        }

        function add_to_setup_list(table_id, setup_type, value) {
            init_setup(table_id)
            if (typeof (setup[table_id][setup_type]) === "undefined") {
                setup[table_id][setup_type] = []
            }
            setup[table_id][setup_type].push(value)
        }

        function add_to_setup(table_id, setup_key, value) {
            init_setup(table_id)
            if (typeof (setup[table_id].datatable_setup) === "undefined") {
                setup[table_id].datatable_setup = {}
            }
            setup[table_id].datatable_setup[setup_key] = value
        }

        function add_filter(table_id, filter) {
            add_to_setup_list(table_id, 'filters', filter)
        }

        function add_plugin(table_id, plugin) {
            add_to_setup_list(table_id, 'plugins', plugin)
        }

        function FilterCalcs(column_no) {
            this.column = column_no
            this.calcs = {}
            this.count = 0
            this.sorted_keys = null

            this.sort_keys = function* () {
                if (this.sorted_keys == null) {
                    this.sorted_keys = []
                    for (var i in this.calcs) {
                        this.sorted_keys.push(i)
                    }
                    this.sorted_keys.sort()
                }
                for (i = 0; i < this.sorted_keys.length; i++) {
                    yield this.sorted_keys[i]
                }
            }

            this.badge_string = function (key) {
                let result = this.calcs[key]
                if (result[0] === result[1]) {
                    return result[0].toString()
                } else {
                    return result[0].toString() + ' / ' + result[1].toString()
                }
            }

            this.badge_colour = function (key) {
                if (this.calcs[key][0] > 0) {
                    return ['badge-primary', 'badge-secondary']
                } else {
                    return ['badge-secondary', 'badge-primary']
                }
            }

            this.get_val = function (row) {
                var value = row[this.column]
                if (value === "") value = 'null'
                return value
            }

            this.init_calcs = function (row, value = 1) {
                this.count += 1
                let key = this.get_val(row);
                if (!Array.isArray(key)) {
                    key = [key]
                }
                for (var k = 0; k < key.length; k++) {
                    if (key[k] in this.calcs) {
                        this.calcs[key[k]][1] += value
                    } else {
                        this.calcs[key[k]] = [0, value]
                    }
                }
            }

            this.clear_calcs = function () {
                for (var i in this.calcs) {
                    this.calcs[i][0] = 0
                }
            }

            this.add_calcs = function (row, value = 1) {
                var item = this.get_val(row)
                if (Array.isArray(item)) {
                    for (var i = 0; i < item.length; i++) {
                        this.calcs[item[i]][0] += value
                    }
                } else {
                    this.calcs[item][0] += value
                }
            }
        }

        function FilterBase(column_no, html_id, options) {
            this.column_no = column_no
            this.html_id = html_id
            this.options = options
            this.filter_data = [];
            this.filter_calcs = new django_datatables.FilterCalcs(this.column_no)
        }

        FilterBase.prototype.save_state = function (data) {
            try {
                data.columns[this.column_no][this.storage_key] = this.save_data()
            } catch (e) {
                console.log(e)
            }
        }

        FilterBase.prototype.this_fn = function (call_function, parameter) {
            var this_filter = this
            return function () {
                this_filter[call_function](parameter, this)
            }
        }

        FilterBase.prototype.restore_state = function (data) {
            try {
                state_data = this.pTable.table.api().state.loaded().columns[this.column_no][this.storage_key]
            } catch (e) {
                console.log(e)
                return
            }
            if (typeof (state_data) !== 'undefined') {
                this.load_state(state_data)
            }

        }
        FilterBase.prototype.this_fn_parameter = function (call_function) {
            var this_filter = this
            return function (param) {
                return this_filter[call_function](param)
            }
        }

        FilterBase.prototype.init = function (table) {
            this.pTable = table;
        }

        FilterBase.prototype.refresh = function () {
        }

        FilterBase.prototype.set_status_class = function (status) {
            var element = $("#" + this.html_id)
            switch (status) {
                case 'all':
                    element.removeClass('filter-none filter-active')
                    element.addClass('filter-all')
                    break;
                case 'none':
                    element.removeClass('filter-active filter-all')
                    element.addClass('filter-none')
                    break;
                default:
                    element.removeClass('filter-none filter-all')
                    element.addClass('filter-active')
            }
        }

        FilterBase.prototype.set_badge = function (badge, key) {
            var colours = this.filter_calcs.badge_colour(key)
            $(badge).addClass(colours[0])
            $(badge).removeClass(colours[1])
            $(badge).html(this.filter_calcs.badge_string(key))
        }


        function PivotFilter(column_no, html_id, options) {

            this.storage_key = 'pivot_filter'
            django_datatables.FilterBase.call(this, column_no, html_id, options)

            this.load_state = function (state_data) {
                $('.filtercheck', '#' + this.html_id).each(function () {
                    $(this).prop('checked', state_data[$(this).attr('data-value')])
                })
            }

            this.save_data = function () {
                let pivot_data = {}
                $(".filtercheck", '#' + this.html_id).each(function () {
                    pivot_data[$(this).attr('data-value')] = $(this).prop('checked')
                })
                return pivot_data
            }

            this.filter = function (data) {
                var col_data = data[this.column_no]
                if (typeof (col_data) === 'number') col_data = col_data.toString();
                if (this.filter_data.indexOf(col_data) < 0) {
                    if (col_data == "" | col_data == null) {
                        if (this.filter_data.indexOf("null") < 0) return false
                    } else return false
                }
                return true
            }

            this.refresh = function () {
                var this_filter = this
                $(".badge", '#' + this.html_id).each(function () {
                    this_filter.set_badge(this, decodeURI($(this).attr("data-value")))
                })
            }

            this.buildfilter = function (refresh) {
                this.filter_data = [];
                var checkboxes = $(".filtercheck:checked", '#' + this.html_id)
                for (var c = 0; c < checkboxes.length; c++) {
                    this.filter_data.push(decodeURI($(checkboxes[c]).attr("data-value")))
                }
                if (this.filter_data.length === Object.keys(this.filter_calcs.calcs).length) {
                    status = 'all'
                } else if (this.filter_data.length === 0) {
                    status = 'none'
                } else {
                    status = ''
                }
                this.set_status_class(status)
                if (refresh) {
                    this.pTable.table.api().draw();
                }
            }

            this.html = function () {
                var htmldata = ''
                for (k of this.filter_calcs.sort_keys()) {
                    htmldata += this.options.htmlcheckbox.replace(/%1/g, k).replace(/%6/g, encodeURI(k))
                }
                var context = $('#' + this.html_id)
                $('.filter-content', context).html(htmldata)
                $(".filtercheck", context).change(this.this_fn('buildfilter', true))
                $(".all-check", context).click(this.this_fn('checkall', true))
                $(".none-check", context).click(this.this_fn('checkall', false))
                this.restore_state()
                this.buildfilter(false)
            }

            this.checkall = function (checked) {
                $("#" + this.html_id + " .filtercheck").each(function () {
                    $(this).prop('checked', checked)
                }).promise().done(this.this_fn('buildfilter', true));
            }

            this.clear = function () {
                this.checkall(true)
            }
        }

        PivotFilter.prototype = Object.create(FilterBase.prototype);

        var column_render = function (column, render_functions, tablesetup) {
            var rf = []
            for (var r = 0; r < render_functions.length; r++) {
                rf.push(new django_datatables.data_processing[render_functions[r].function](column, render_functions[r], tablesetup))
            }
            return function (data, type, row, meta) {
                data = rf[0].process(data, type, row, meta)
                for (r = 1; r < rf.length; r++) {
                    data = rf[r].process(data, type, row, meta)
                }
                return data
            }
        }

        var BaseProcessAjaxData = function (column, params, table) {
            this.column = column
            if (table.initsetup.colOptions[column].field_array == true){
                this.field_array = true
            }
            if (typeof params.column === 'string'){
                var column_index = params.column.split(':')
                params.column =  table.find_column(column_index[0])
                if (column_index.length > 1){
                    params.index = parseInt(column_index[1])
                } else {
                    params.index = 0
                }
            }
            this.params = params
        }

        BaseProcessAjaxData.prototype.process = function (column_data, type, row, meta) {
            if (Array.isArray(column_data) && !this.field_array) {
                var column_val = []
                for (var a = 0; a < column_data.length; a++) {
                    if (this.params.column === meta.col) {
                        column_val[a] = this.convert(column_data[a], row[this.params.column][a], meta, row)
                    } else {
                        column_val[a] = this.convert(column_data[a], row[this.params.column], meta, row)
                    }
                }
                return column_val.join(' ')
            } else {
                return this.convert(column_data, row[this.params.column], meta, row)
            }
        }

        var data_processing = {
            Row: function (column, params, table) {
                django_datatables.BaseProcessAjaxData.call(this, column, params, table)
                this.reg_exp = RegExp(params.var, 'g')
                if (params.html === undefined) {
                    this.convert = function (current, value, meta, row) {
                        return current.replace(params.var, meta.settings.rowId(row))
                    }
                } else {
                    this.convert = function (current, value, meta, row) {
                        return params.html.replace(params.var, meta.setup.rowId(row))
                    }
                }
            },

            Replace: function (column, params, table) {
                this.reg_exp = RegExp(params.var, 'g')
                django_datatables.BaseProcessAjaxData.call(this, column, params, table)

                this.convert = function (current, value) {
                    if (params.html === undefined) {
                        if (this.field_array){
                            return current.replace(params.var, value[params.index])
                        } else{
                            return current.replace(params.var, value)
                        }

                    } else {
                        if (this.field_array) {
                            return params.html.replace(params.var, value[params.index])
                        } else {
                            return params.html.replace(params.var, value)
                        }
                    }
                }.bind(this)
            },

            ReplaceLookup: function (column, params, table) {
                django_datatables.BaseProcessAjaxData.call(this, column, params, table)
                this.reg_exp = RegExp(params.var, 'g')
                if (params.column === undefined){
                    params.column = column
                }
                params.lookup = {}
                for (var lv=0; lv<table.initsetup.colOptions[params.column].lookup.length; lv++ ){
                    params.lookup[table.initsetup.colOptions[params.column].lookup[lv][0]] = table.initsetup.colOptions[params.column].lookup[lv][1]
                }
                if (params.html === undefined){
                    this.convert = function (current, value) {
                        return this.params.lookup[value]
                    }.bind(this)
                }else{
                    this.convert = function (current, value) {
                        return this.params.html.replace(this.reg_exp, this.params.lookup[value])
                    }.bind(this)
                }
            },

            Html: function(column, params, table){
                django_datatables.BaseProcessAjaxData.call(this, column, params, table)
                this.convert = function () {
                    return params.html
                }
            },

            ValueInColumn: function(column, params, table){
                django_datatables.BaseProcessAjaxData.call(this, column, params, table)
                var new_value
                this.convert = function (current, value) {
                    if (value.includes(params.value)){
                        new_value = params.choices[0]
                    } else {
                        new_value = params.choices[1]
                    }
                    if (params.html === undefined) {
                        return current.replace(params.var, new_value)
                    } else {
                        return params.html.replace(params.var, new_value)
                    }
                }.bind(this)

            },

            MergeArray: function (column, params) {
                this.column = column
                this.process = function (new_row, row) {
                    console.log(new_row)
                    new_row[this.column] = new_row[this.column].join(' ')
                }
            }
        }

        for (var dp in data_processing){
            data_processing[dp].prototype = Object.create(BaseProcessAjaxData.prototype);
        }

        return {
            BaseProcessAjaxData,
            data_processing,
            setup,
            add_filter,
            add_plugin,
            DataTables,
            FilterCalcs,
            FilterBase,
            PivotFilter,
            column_render,
            utilities,
            add_to_setup,
            b_r,
        }
    }()
}


function rep_options(html, option_dict) {
    for (var o in option_dict) {
        var option = new RegExp('%' + o, 'g')
        html = html.replace(option, option_dict[o])
    }
    return html
}


function numberWithCommas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}


function PythonTable(html_id, tablesetup) {
    // tablesetup.html_id = html_id
    this.initsetup = tablesetup
    this.filters = []
    this.table_id = html_id

    col_defs = tablesetup.tableOptions.columnDefs

    django_datatables.DataTables[html_id] = this
    if (typeof (mobile) == 'undefined') mobile = false;
    for (i = 0; i < tablesetup.colOptions.length; i++) {
        if (mobile && (col_defs[i]['mobile'] == false)) {
            col_defs[i].visible = false
        }
        if (tablesetup.colOptions[i]['render'] != undefined) {
            col_defs[i].render = new django_datatables.column_render(i, tablesetup.colOptions[i]['render'], this)
        }
    }

    this.postInit = function () {
        this.table =  $('#' + html_id).dataTable()

        this.table.api().on('stateSaveParams.dt', function (e, settings, data) {
            this.exec_filter('save_state', data)
        }.bind(this))
        if (typeof (django_datatables.setup[html_id].filters) !== 'undefined') {
            this.filters = django_datatables.setup[html_id].filters
        }
        if (typeof (django_datatables.setup[html_id].plugins) !== 'undefined') {
            this.plugins = django_datatables.setup[html_id].plugins
        }
        this.exec_filter('init', this)
        this.init_filters()
        this.exec_filter('html')
        var state_data = this.table.api().state.loaded()
        this.exec_plugins('init', this, state_data)

        this.table.api().on('draw', function () {
            this.proc_filters(this)
            this.exec_filter( 'refresh')
            this.exec_plugins('refresh', this)
        }.bind(this));
        this.table.api().draw()
    }.bind(this)


    var dataTable_setup = {
        /*  stripeClasses:['a', 'a'], */
        orderCellsTop: true,
        pageLength: 25,
        fixedHeader: true,
        orderClasses: false,
        stateSave: true,
        deferRender: true,
        dom: 'rtip',
        initComplete: this.postInit,
    }
    if (tablesetup.tableOptions.data === undefined){
        var csrf = django_datatables.utilities.getCookie('csrftoken');
        dataTable_setup.ajax = {'url': '?datatable-data=true', "type": "POST", "data": {"csrfmiddlewaretoken": csrf, table_id: html_id}}
    }

    if (tablesetup.tableOptions.column_id !== undefined && tablesetup.tableOptions.column_id != null){
        dataTable_setup.rowId = function(row) {
            return 'i' + row[tablesetup.tableOptions.column_id];
            }
    }
    Object.assign(dataTable_setup, tablesetup.tableOptions)
    Object.assign(dataTable_setup, django_datatables.setup[html_id].datatable_setup)

    if (typeof (tablesetup.tableOptions.rowGroup) != 'undefined') {
        dataTable_setup['rowGroup'] =
            {
                dataSrc: tablesetup.field_ids.indexOf(tablesetup.tableOptions.rowGroup.dataSrc),
                /*
                endRender: function (rows, group) {
                    sums = Array(rows.data()[0].length).fill('')
                    tablesetup.tableOptions.rowGroup.sumColumns.forEach(
                        function (column) {
                            column_no = tablesetup.field_ids.indexOf(column)
                            var sum = rows.data().pluck(column_no).reduce(
                                function (a, b) {
                                    return a + parseFloat(b)
                                }, 0)
                            sums[column_no] = sum
                        })
                    sums_row = ''
                    for (c = 0; c < sums.length; c++) {
                        if (tablesetup.columnDefs[c].hidden != true) {
                            if (typeof (sums[c]) == 'number') {
                                sums_row += '<td class="pr-4">' + sums[c].toFixed(2);
                                +'</td>'
                            } else {
                                sums_row += '<td></td>'
                            }
                        }
                    }
                    return $('<tr>' + sums_row + '</tr>')
                },
                startClassName: 'table-info font-weight-bold',
                endClassName: 'font-weight-bold white text-right'
                */
            }
    }

    $('#' + this.table_id).dataTable(dataTable_setup);

    if (this.initsetup.tableOptions.row_href) {
        $('#' + html_id + ' tbody').on('click', 'tr', function () {
            p_table = django_datatables.DataTables[html_id]
            var row_id = $(this).attr('id')
            var row_data = p_table.table.api().row('#' + row_id).data()
            var href_render  = new django_datatables.column_render(0, p_table.initsetup.tableOptions.row_href, p_table)
            window.location.href = href_render('',null, row_data)
        })
    }
}

PythonTable.prototype.exec_filter = function (function_name, data) {
    for (var i = 0; i < this.filters.length; i++) {
        if (function_name in this.filters[i]) {
            this.filters[i][function_name](data)
        }
    }
}

PythonTable.prototype.exec_plugins = function (function_name, data, extra_data) {
    for (var i = 0; i < this.plugins.length; i++) {
        if (function_name in this.plugins[i]) {
            this.plugins[i][function_name](data, extra_data)
        }
    }
}

PythonTable.prototype.init_filters = function () {
    this.table.api().rows().data().each(function (row) {
        this.filters.forEach(function (filter) {
            filter.filter_calcs.init_calcs(row)
        })
    }.bind(this))
}

PythonTable.prototype.proc_filters = function () {
    this.filters.forEach(function (filter) {
        filter.filter_calcs.clear_calcs()
    })
    this.table.api().rows({"filter": "applied"}).data().each(function (row) {
        this.filters.forEach(function (filter) {
            filter.filter_calcs.add_calcs(row)
        })
    }.bind(this))
}

PythonTable.prototype.find_column = function (id) {
    for (var j = 0; j < this.initsetup.tableOptions.columnDefs.length; j++) {
        if (this.initsetup.tableOptions.columnDefs[j]['name'] === id) {
            return j
        }
    }
}

PythonTable.prototype.reset_table = function () {
    this.exec_filter('clear')
    this.exec_plugins('clear')
    if (this.initsetup.tableOptions.order !== undefined) {
        this.table.api().order(this.initsetup.tableOptions.order)
    } else {
        this.table.api().order([])
    }
    this.table.api().draw()
}

PythonTable.prototype.send_row = function (command, row_id) {
    var row_data = this.table.api().row('#' + row_id).data()
    var data = {
        'row': JSON.stringify(row_data), 'command': command, 'row_no': row_id, table_id: this.table_id
    }
    django_datatables.utilities.post_data('?datatable-row=true', data)
}

PythonTable.prototype.send_column = function (command, column) {
    var acc = this.table.api().column(this.find_column(column), {"filter": "applied"}).data().reduce(function (acc, current) {
        acc.push(current)
        return acc
    }, [])
    var data = {
        column: JSON.stringify(acc), command: command, table_id: this.table_id
    }
    django_datatables.utilities.post_data('?datatable-column=true', data)
}


$(document).ready(function () {
    $.fn.dataTable.moment("DD/MM/YYYY");
});
