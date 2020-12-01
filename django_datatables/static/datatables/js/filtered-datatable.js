if (typeof django_datatables === 'undefined') {
    var django_datatables = function () {
        var setup = {}
        var DataTables = {}

        columnsearch = function (settings, data, dataIndex, rowdata) {
            if (settings.sTableId in DataTables) {
                for (var f = 0; f < DataTables[settings.sTableId].filters.length; f++) {
                    if (!self.filters[f].filter(rowdata)) return false
                }
                return true
            }
        }
        $.fn.dataTable.ext.search.push(columnsearch)

        function exec_filter(table, function_name, data) {
            for (var i = 0; i < table.filters.length; i++) {
                if (function_name in table.filters[i]) {
                    table.filters[i][function_name](data)
                }
            }
        }

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
                item = this.get_val(row)
                if (Array.isArray(item)) {
                    for (var i = 0; i < item.length; i++) {
                        this.calcs[item[i]][0] += value
                    }
                } else {
                    this.calcs[item][0] += value
                }
            }
        }


        this.filters = {
            init_filters: function (p_table) {

                p_table.table.api().rows().data().each(function (row) {
                    p_table.filters.forEach(function (filter) {
                        filter.filter_calcs.init_calcs(row)
                    })
                })
            },

            proc_filters: function (p_table) {
                p_table.filters.forEach(function (filter) {
                    filter.filter_calcs.clear_calcs()
                })
                p_table.table.api().rows({"filter": "applied"}).data().each(function (row) {
                    p_table.filters.forEach(function (filter) {
                        filter.filter_calcs.add_calcs(row)
                    })
                })
            },
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
            return
        }

        FilterBase.prototype.set_status_class = function (status) {
            element = $("#" + this.html_id)
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
                htmldata = ''
                for (k of this.filter_calcs.sort_keys()) {
                    htmldata += this.options.htmlcheckbox.replace(/%1/g, k).replace(/%6/g, encodeURI(k))
                }
                context = $('#' + this.html_id)
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
        }

        PivotFilter.prototype = Object.create(FilterBase.prototype);

        return {
            setup,
            add_filter,
            add_plugin,
            DataTables,
            exec_filter,
            FilterCalcs,
            filters,
            FilterBase,
            PivotFilter,
        }
    }()
}


function make_lookup_dict(lookup_data) {

    if (lookup_data['dict'] != undefined) return;
    lookup_data.dict = {}
// filter_len used to know if all items checked
    filter_len = 0
    for (j = 0; j < lookup_data.lookup.length; j++) {
        if (lookup_data.lookup[j][0] < 0x10000) filter_len += 1
        lookup_data.dict[lookup_data.lookup[j][0]] = lookup_data.lookup[j][1]
    }
    lookup_data.filter_len = filter_len
}


function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function geturl(cell, row, column) {
    if (row[column + colOptions[column]['link']]) {
        return urls[column].replace('999999', row[column + colOptions[column]['link']].toString());
    }
    if (row[column + colOptions[column]['javascript']]) {
        return urls[column].replace('999999', row[column + colOptions[column]['javascript']].toString());
    }

    return null;
}

function rep_options(html, option_dict) {
    for (o in option_dict) {
        option = new RegExp('%' + o, 'g')
        html = html.replace(option, option_dict[o])
    }
    return html
}


function numberWithCommas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}


renderHelpers =
    {

        initUrl: function (renderer, column, setup) {
            renderer.url = setup['url']

            if (!renderer.url) {
                renderer.url = setup['rawurl']
                renderer.column = 0
            } else {
                renderer.column = column + setup['link']
            }
        },

        find_column: function (id, tablesetup) {
            for (j = 0; j < tablesetup.colDefs.length; j++) {
                if (tablesetup.colDefs[j]['name'] == id) {
                    return j
                }
            }
        },

        initColRef: function (renderer, column, setup, tablesetup) {
            if (typeof (setup['colRef']) != 'undefined') {
                for (j = 0; j < tablesetup.colDefs.length; j++) {
                    if (tablesetup.colDefs[j]['name'] == setup['colRef']) {
                        renderer.column = j
                        return
                    }
                }
            }
        }


    }

renderFunctions =
    {

        mouseOver: function (column, setup, title, tablesetup) {

            renderHelpers.initUrl(this, column, setup)
            this.js = setup['mouseover']
            this.css_class = ''
            if (setup['css_class'] != undefined) this.css_class = ' class="' + setup['css_class'] + '"'
            this.title = title
            if (setup['text'] != undefined) this.globaltext = setup['text']; else this.globaltext = title
            this.render = function (data, type, row, meta) {
                if (data === null || data === "") text = this.globaltext; else text = data;
                js = this.js
                if (this.url) {
                    cell_url = this.url.replace('999999', row[this.column].toString());
                    js = js.replace('%url%', "'" + cell_url + "'")
                }
                js = js.replace('%row%', meta.row)
                return '<button href=# onmouseover="' + js + '"' + this.css_class + '">' + text + '</button>';
            }
        },

        lookupRender: function (column, setup, title, tablesetup) {
            make_lookup_dict(tablesetup.colOptions[column])
            this.dict = tablesetup.colOptions[column].dict
            this.tagbadge = '<span class="small badge badge-pill badge-info m-1">%1</span>'
            this.groupbadge = '<span class="small badge badge-pill badge-secondary m-1">%1</span>'
            this.render = function (data, type, row, meta) {
                html = ''
                for (count = 0; count < data.length; count++) {
                    if (data[count] >= 0x10000) {
                        html += this.groupbadge.replace('%1', this.dict[data[count]])
                    } else {
                        html += this.tagbadge.replace('%1', this.dict[data[count]])
                    }
                }
                return html
            }
        },

        BadgeList: function (column, setup, title, tablesetup) {
            this.tagbadge = '<span class="small badge badge-pill badge-info m-1">%1</span>'
            this.render = function (data, type, row, meta) {
                html = ''
                for (count = 0; count < data.length; count++) {
                    html += this.tagbadge.replace('%1', data[count])
                }
                return html
            }
        },

        imageRender: function (column, setup, title, tablesetup) {
            this.render = function (data, type, row, meta) {
                if (data === null || data === "") return '';
                else return '<img src="' + tablesetup.tableOptions.media + data + '" height="50" class="img-zoom">'
            }
        },

        iconRender: function (column, setup, title, tablesetup) {
            renderHelpers.initUrl(this, column, setup)
            renderHelpers.initColRef(this, column, setup, tablesetup)
            this.linktag = '<img'
            if (setup['css_class'] != undefined) this.linktag += ' class="' + setup['css_class'] + '"'
            if (setup['target'] != undefined) this.linktag += ' target="' + setup['target'] + '"'
            this.title = title
            this.render = function (data, type, row, meta) {
                if (data === null || data === "") text = this.title; else text = data;
                if (typeof (row[this.column]) != 'undefined' & row[this.column] != null) {
                    cell_url = this.url.replace('999999', row[this.column].toString().replace(/\ /g, '-'));
                    return this.linktag + ' src="' + cell_url + '" title="' + row[this.column] + '">';
                } else return ''
            }
            return null;
        },

        universalRender: function (column, setup, title, tablesetup) {

            if (Array.isArray(setup.replace_list)) {
                for (r = 0; r < setup.replace_list.length; r++) {
                    if (typeof (setup.replace_list[r].column) == 'string') {
                        setup.replace_list[r].column = renderHelpers.find_column(setup.replace_list[r].column, tablesetup)
                    }
                }
            }
            this.setup = setup

            function replace_data(row_data, col_def) {
                column_data = row_data[col_def.column]
                var x;
                for (x = 0; x < col_def.comparisons.length; x++) {
                    if (column_data == col_def.comparisons[x][0]) {
                        return col_def.comparisons[x][1]
                    }
                }
                return col_def.default
            }

            this.render = function (data, type, row, meta) {
                var y;
                html = this.setup.html.replace(/%row%/g, meta.row)
                for (y = 0; y < this.setup.replace_list.length; y++) {
                    if (typeof (this.setup.replace_list[y].comparisons) != 'undefined') {
                        if (typeof (replace_data(row, this.setup.replace_list[y])) == 'undefined' || replace_data(row, this.setup.replace_list[y]) == '') {
                            html = ''
                        } else {
                            html = html.replace(RegExp(this.setup.replace_list[y].var, 'g'), replace_data(row, this.setup.replace_list[y]))
                        }
                    } else if (typeof (this.setup.replace_list[y].in) != 'undefined') {
                        if (row[this.setup.replace_list[y].column].includes(this.setup.replace_list[y].in)) {
                            html = html.replace(RegExp(this.setup.replace_list[y].var, 'g'), this.setup.replace_list[y].values[0])
                        } else {
                            html = html.replace(RegExp(this.setup.replace_list[y].var, 'g'), this.setup.replace_list[y].values[1])
                        }
                    } else {
                        if (typeof (row[this.setup.replace_list[y].column]) === 'undefined' || row[this.setup.replace_list[y].column] === '' || row[this.setup.replace_list[y].column] === null) {
                            html = ''
                        } else {
                            html = html.replace(RegExp(this.setup.replace_list[y].var, 'g'), row[this.setup.replace_list[y].column])
                        }
                    }
                }
                return html
            }
        },

        tagToggleRender: function (column, setup, title, tablesetup) {
            renderHelpers.initColRef(this, column, setup, tablesetup);
            this.tagid = setup.tagid;
            this.tag = setup.tag;
            if (typeof (setup.tag_ref) != 'undefined') {
                this.tag_ref = renderHelpers.find_column(setup.tag_ref, tablesetup);
            }

            if (typeof (setup.disabled) == 'undefined') {
                this.disabled = this.tag
            } else {
                this.disabled = setup.disabled
            }

            if (typeof (setup.modal) == 'undefined') {
                this.modalform = 'modaltag'
            } else {
                this.modalform = setup.modal
            }
            this.render = function (data, type, row, meta) {
                start = ''
                if (data != 1) {
                    btn_class = 'btn-outline-secondary'
                    button_text = this.disabled
                } else {
                    btn_class = 'btn-success'
                    button_text = this.tag
                    //   start = '&zwnj;'
                }
                if (typeof (this.tag_ref) != 'undefined') {
                    button_text = row[this.tag_ref]
                }
                json_data = {
                    col: row[this.column].toString(),
                    row: meta.row,
                    tagid: this.tagid
                }
                return (start + "<button onclick='modal.send_inputs(" + JSON.stringify(json_data) + ")' class='btn " + btn_class + " btn-sm'>" + button_text + "</button>")
            }
        },
    }

datatable_config = {}

function setRowClass(row, data, dataIndex, rowDefn) {
    rowclass = rowDefn.values[data[rowDefn.column]]
    if (typeof (rowclass) != 'undefined') {
        $(row).addClass(rowclass)
    }
}


function PythonTable(html_id, tablesetup, ajax_url, options = {}) {
    self = this
    self.initsetup = tablesetup
    self.filters = []
    datatable_config[html_id] = {}
    col_defs = tablesetup.colDefs

    if (typeof (mobile) == 'undefined') mobile = false;
    for (i = 0; i < tablesetup.colOptions.length; i++) {
        if (mobile && (col_defs[i]['mobile'] == false)) {
            col_defs[i].visible = false
        }
        if (tablesetup.colOptions[i]['renderfn'] != undefined) {
            datatable_config[html_id][i] = new renderFunctions[tablesetup.colOptions[i]['renderfn']](i, tablesetup.colOptions[i], tablesetup.titles[i], tablesetup)
            col_defs[i]['render'] = function (data, type, row, meta) {
                return datatable_config[meta.settings.sTableId][meta.col].render(data, type, row, meta)
            }
        }
    }

    this.postInit = function (settings, json) {
        var p_table = self
        p_table.table.api().on('stateSaveParams.dt', function (e, settings, data) {
            django_datatables.exec_filter(p_table, 'save_state', data)
        })
        if (typeof (django_datatables.setup[html_id].filters) !== 'undefined') {
            p_table.filters = django_datatables.setup[html_id].filters
        }
        django_datatables.exec_filter(p_table, 'init', p_table)
        django_datatables.filters.init_filters(p_table)
        django_datatables.exec_filter(p_table, 'html')
        django_datatables.setup[html_id].plugins.forEach(function (plugin) {
            plugin.init(p_table);
        })
        p_table.table.api().on('draw', function () {
            django_datatables.filters.proc_filters(p_table)
            django_datatables.exec_filter(p_table, 'refresh')
            }
        );
        p_table.table.api().draw()
    }

    if (ajax_url != '') {
        csrf = getCookie('csrftoken');
        ajax_dict = {'url': ajax_url, "type": "POST", "data": {"csrfmiddlewaretoken": csrf},}
        tabledata = null
    } else {
        ajax_dict = null
        tabledata = options['data']
    }

    this.table_id = html_id

    buttons = tablesetup.tableOptions['buttons']
    if (buttons == null) buttons = ['csv']
    dom_options = tablesetup.tableOptions.domOptions
    if (dom_options == null) dom_options = 'rtip'

    dataTable_setup = {
        /*  stripeClasses:['a', 'a'], */

        rowReorder: tablesetup.tableOptions.rowReorder,
        orderCellsTop: true,
        pageLength: tablesetup.tableOptions.pageLength,
        fixedHeader: true,
        orderClasses: false,
        stateSave: true,
        ajax: ajax_dict,
        data: tabledata,
        deferRender: true,
        order: tablesetup.tableOptions.order,
        dom: dom_options,
        buttons: buttons,
        columnDefs: col_defs,
        initComplete: this.postInit,
    }
    if (typeof (tablesetup.tableOptions.rowGroup) != 'undefined') {
        dataTable_setup['rowGroup'] =
            {
                dataSrc: tablesetup.field_ids.indexOf(tablesetup.tableOptions.rowGroup.dataSrc),
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
                        if (tablesetup.colOptions[c].hidden != true) {
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
            }
    }
    if (typeof (tablesetup.tableOptions.rowColor) != 'undefined') {
        dataTable_setup['createdRow'] = function (row, data, dataIndex) {
            if (Array.isArray(tablesetup.tableOptions.rowColor)) {
                for (rc = 0; rc < tablesetup.tableOptions.rowColor.length; rc++) {
                    setRowClass(row, data, dataIndex, tablesetup.tableOptions.rowColor[rc])
                }
            } else {
                setRowClass(row, data, dataIndex, tablesetup.tableOptions.rowColor)
            }
        }
    }

    this.table = $('#' + this.table_id).dataTable(dataTable_setup);

    if (mobile) {
        that = this
        $(html_id + ' tbody').on('click', 'tr', function () {
            window.location.href = that.initsetup.colOptions[0].url.replace('999999', that.table.api().row(this).data()[0])
        })
    }
}

$(document).ready(function () {
    $.fn.dataTable.moment("DD/MM/YYYY");
});
