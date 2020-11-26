

if (typeof django_datatables === 'undefined'){
    var django_datatables = function(){
        setup = {}
        DataTables = {}

        function exec_filter(table, function_name, data ){
            for (i=0; i<table.filters.length; i++){
                if (function_name in table.filters[i]){
                    table.filters[i][function_name](data)
                }
            }
        }

        function init_setup(table_id){
            if (typeof(setup[table_id]) === 'undefined')
                setup[table_id] = {}
        }

        function add_to_setup_list(table_id, setup_type, value){
            init_setup(table_id)
            if (typeof(setup[table_id][setup_type]) === "undefined"){
                setup[table_id][setup_type] = []
            }
            setup[table_id][setup_type].push(value)
        }

        function add_filter(table_id, filter){
            add_to_setup_list(table_id, 'filters', filter)
        }

        function add_plugin(table_id, plugin){
            add_to_setup_list(table_id, 'plugins', plugin)
        }
        return {
            setup,
            add_filter,
            add_plugin,
            DataTables,
            exec_filter,
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

function geturl (cell , row, column) {
    if (row[column + colOptions[column]['link']]) {
        return urls[column].replace('999999', row[column + colOptions[column]['link']].toString());
    }
    if (row[column + colOptions[column]['javascript']]) {
        return urls[column].replace('999999', row[column + colOptions[column]['javascript']].toString());
    }

    return null;
}

function rep_options(html, option_dict)
{
    for (o in option_dict)
    {
        option = new RegExp('%' + o, 'g')
        html = html.replace(option, option_dict[o])
    }
    return html
}



function numberWithCommas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}



function filter_totals(pTable, column, title)
{
    this.column = column
    this.pTable = pTable
    if (title=='')
    {
        this.title = 'Calcs'
    }
    else
    {
        this.title = title
    }
    this.total = {}
    this.filter = function ( data ){return true}

    this.html = function ()
        {
            html = `<table class="table">

            <tr><td>Mean</td><td class="text-right" id="mean"></td></tr>
            <tr><td>Std Deviation</td><td class="text-right" id="stddev"></td></tr>
            </table> `
            return filter_helper.add_header(this, html)
        }
    this.refresh = function ()
    {

            this.total['total'] = 0.0
            this.total['count'] = 0
            this.total['mean'] = 0
            this.total['M2'] = 0

            this.pTable.table.api().column(this.column, {"filter":"applied"}).data().reduce(function (acc, current)
            {
                curval = parseFloat(current)
                acc['total'] += curval
                acc['count'] += 1
                delta = curval - acc['mean']
                acc['mean'] += delta/acc['count']
                delta2 = curval - acc['mean']
                acc['M2'] +=  delta * delta2
                return acc;
            },  this.total  )

            $("#total").text((this.total['total']).toFixed(1))
            $("#mean").text((this.total['mean']).toFixed(1))
            $("#count").text((this.total['count']))
            $("#stddev").text(Math.sqrt(this.total['M2']/(this.total['count']-1)).toFixed(1))
    }
    this.buildfilter = function(data) {}
    this.setup_events = function () {}
}


function filter_date(pTable, column, title)
{
    this.column = column
    this.pTable = pTable
    this.title = title
    this.datebefore = ''
    this.dateafter = ''

    this.str_to_date = function (datestr)
        {
            try
            {
                parts = datestr.split('/')
                return new Date(parts[2], parts[1], parts[0])
            }
            catch(err)
            {
                return null
            }
        }

    this.filter = function ( data )
        {
            if (this.dateafter!=null)
            {
                compdate = str_to_date(data[this.column])
                if (compdate!=null)
                {
                    if (this.dateafter>=compdate) return false
                }
            }
            if (this.datebefore!=null)
            {
                compdate = str_to_date(data[this.column])
                if (compdate!=null)
                {
                    if (this.datebefore<=compdate) return false
                }
            }
            return true
        }

    this.html = function ()
        {
            datebox = ` <div class="form-group form-inline">
                        <label for="date%1-%3">%1</label>
                        <input type="text" class="form-control filtertext" id="date%1-%3">
                        </div>`
            html = rep_options(datebox, {1:'After'})
            html += rep_options(datebox, {1:'Before'})
            return filter_helper.add_header(this, html)
        }


    this.buildfilter = function(data)
        {
            if (data!=undefined)
            {
                this_filter = data.data.filter
                refresh = true
            }
            else
            {
                this_filter = this
                refresh = false
            }
            this_filter.dateafter = this.str_to_date($('#dateAfter-' + this_filter.column.toString()).val())
            this_filter.datebefore = this.str_to_date($('#dateBefore-' + this_filter.column.toString()).val())
            if (refresh) this_filter.pTable.table.api().draw()
        }

    this.setup_events = function ()
        {
            $("#filter_"+this.title).find(".filtertext").change( {filter: this} , this.buildfilter )
        }

    this.refresh = function (){return}
}


renderHelpers =
{

    initUrl : function ( renderer , column, setup)
    {
        renderer.url = setup['url']

        if (!renderer.url)
        {
            renderer.url = setup['rawurl']
            renderer.column = 0
        }
        else
        {
            renderer.column = column + setup['link']
        }
    },

    find_column: function(id, tablesetup){
        for (j=0;j<tablesetup.colDefs.length;j++)
        {
            if (tablesetup.colDefs[j]['name']==id)
            {
                return j
            }
        }
    },

    initColRef : function ( renderer , column, setup, tablesetup)
    {
        if (typeof(setup['colRef'])!='undefined')
        {
            for (j=0;j<tablesetup.colDefs.length;j++)
            {
                if (tablesetup.colDefs[j]['name']==setup['colRef'])
                {
                    renderer.column = j
                    return
                }
            }
        }
    }


}

renderFunctions =
{

    mouseOver: function (column, setup , title, tablesetup)
    {

        renderHelpers.initUrl(this, column, setup)
        this.js = setup['mouseover']
        this.css_class = ''
        if (setup['css_class']!=undefined) this.css_class = ' class="' + setup['css_class'] + '"'
        this.title = title
        if (setup['text']!=undefined) this.globaltext = setup['text']; else this.globaltext = title
        this.render = function (data, type, row, meta)
        {
            if (data === null || data === "") text = this.globaltext; else text = data;
            js = this.js
            if (this.url)
            {
                cell_url = this.url.replace ('999999',row[this.column].toString());
                js = js.replace('%url%', "'" + cell_url + "'")
            }
            js = js.replace('%row%', meta.row)
            return '<button href=# onmouseover="' + js + '"' + this.css_class +'">' + text + '</button>';
        }
    },

    lookupRender:function(column, setup , title, tablesetup)
    {
        make_lookup_dict(tablesetup.colOptions[column])
        this.dict = tablesetup.colOptions[column].dict
        this.tagbadge = '<span class="small badge badge-pill badge-info m-1">%1</span>'
        this.groupbadge = '<span class="small badge badge-pill badge-secondary m-1">%1</span>'
        this.render = function (data, type, row, meta){
        html = ''
        for (count=0;count<data.length;count++){
            if (data[count]>=0x10000)
            {
                 html += this.groupbadge.replace('%1',this.dict[data[count]])
            }
            else
            {
                 html += this.tagbadge.replace('%1',this.dict[data[count]])
            }
        }
        return html
    }
},

    BadgeList:function(column, setup , title, tablesetup)
    {
        this.tagbadge = '<span class="small badge badge-pill badge-info m-1">%1</span>'
        this.render = function (data, type, row, meta){
            html = ''
            for (count=0;count<data.length;count++){
                html += this.tagbadge.replace('%1',data[count])
            }
            return html
        }
    },

    urlRender: function (column, setup , title, tablesetup)
    {
        renderHelpers.initUrl(this, column, setup)
        renderHelpers.initColRef(this, column, setup, tablesetup)
        this.nonull = setup['nonull']
        this.linktag = '<a'
        if (setup['css_class']!=undefined) this.linktag += ' class="' + setup['css_class'] + '"'
        if (setup['target']!=undefined) this.linktag += ' target="' + setup['target'] +'"'
        this.title = title
        if (setup['text']!=undefined) this.globaltext = setup['text']; else this.globaltext = title
        this.render = function (data, type, row, meta)
        {
            if (data === null || data === "")
            {
                if (this.nonull) return '';
                else text = this.globaltext
            }
            else
            {
                text = data;
            }
            if (typeof(row[this.column])!='undefined' & row[this.column]!=null)
            {
                cell_url = this.url.replace ('999999',row[this.column].toString());
                return this.linktag + ' href="'+ cell_url + '">' + text + '</a>';
            }
            else
            {
                return ''
            }
        }
        return null;

    },


    jsRender : function (column, setup, title, tablesetup)
    {
        renderHelpers.initUrl(this, column, setup)
        renderHelpers.initColRef(this, column, setup, tablesetup)
        this.js = setup['javascript']
        this.nonull = setup['nonull']
        this.nonullref = setup['nonullref']
        this.css_class = ''
        if (setup['css_class']!=undefined) this.css_class = ' class="' + setup['css_class'] + '"'
        this.title = title
        if (setup['text']!=undefined) this.globaltext = setup['text']; else this.globaltext = title
        this.render = function (data, type, row, meta)
        {
            if (this.nonullref)
            {
                if (row[this.column]==null | row[this.column]=="") return '';
            }
            if (data === null || data === "")
            {
                if (this.nonull) return '';
                else text = this.globaltext
            }
            else
            {
                text = data;
            }
            if (text=='') return ''
            js = this.js
            if (this.url)
            {
                cell_url = this.url.replace ('999999',row[this.column].toString());
                js = js.replace('%url%', "'" + cell_url + "'")
            }
            if (row[this.column]!=null)
            {
                js = js.replace('%ref%', row[this.column].toString())
                js = js.replace('%id%', row[this.column].toString())
            }
            js = js.replace('%row%', meta.row)
            return '<a href="javascript:' + js + '"' + this.css_class +'">' + text + '</a>';
        }
    },

    imageRender : function (column, setup, title, tablesetup)
    {
        this.render = function (data, type, row, meta)
        {
            if (data === null || data === "") return '';
            else  return '<img src="' + tablesetup.tableOptions.media + data +'" height="50" class="img-zoom">'
        }
    },

    iconRender: function (column, setup , title, tablesetup)
    {
        renderHelpers.initUrl(this, column, setup)
        renderHelpers.initColRef(this, column, setup, tablesetup)
        this.linktag = '<img'
        if (setup['css_class']!=undefined) this.linktag += ' class="' + setup['css_class'] + '"'
        if (setup['target']!=undefined) this.linktag += ' target="' + setup['target'] +'"'
        this.title = title
        this.render = function (data, type, row, meta)
        {
            if (data === null || data === "") text = this.title; else text = data;
            if (typeof(row[this.column])!='undefined' & row[this.column]!=null)
            {
                cell_url = this.url.replace ('999999',row[this.column].toString().replace(/\ /g,'-'));
                return this.linktag + ' src="'+ cell_url + '" title="'+ row[this.column] +'">';
            }
            else return ''
        }
        return null;
    },

    universalRender:  function (column, setup , title, tablesetup){

        if (Array.isArray(setup.replace_list)){
            for (r=0; r<setup.replace_list.length; r++){
                if (typeof (setup.replace_list[r].column) == 'string')
                {
                    setup.replace_list[r].column = renderHelpers.find_column(setup.replace_list[r].column, tablesetup)
                }
            }
        }
        this.setup = setup

        function replace_data(row_data, col_def){
            column_data = row_data[col_def.column]
            var x;
            for (x=0;x < col_def.comparisons.length; x++){
                if (column_data == col_def.comparisons[x][0]){
                    return col_def.comparisons[x][1]
                }
            }
            return col_def.default
        }

        this.render = function (data, type, row, meta){
            var y;
            html = this.setup.html.replace(/%row%/g, meta.row)
            for (y=0; y<this.setup.replace_list.length; y++){
                if (typeof(this.setup.replace_list[y].comparisons)!='undefined'){
                    if (typeof (replace_data(row, this.setup.replace_list[y])) == 'undefined' || replace_data(row, this.setup.replace_list[y]) == ''){
                        html = ''
                    } else {
                        html = html.replace(RegExp(this.setup.replace_list[y].var, 'g'), replace_data(row, this.setup.replace_list[y]))
                    }
                }
                else if (typeof(this.setup.replace_list[y].in)!='undefined'){
                    if (row[this.setup.replace_list[y].column].includes(this.setup.replace_list[y].in)){
                        html = html.replace(RegExp(this.setup.replace_list[y].var, 'g'), this.setup.replace_list[y].values[0])
                    }else{
                        html = html.replace(RegExp(this.setup.replace_list[y].var, 'g'), this.setup.replace_list[y].values[1])
                    }
                }
                else{
                    if (typeof (row[this.setup.replace_list[y].column]) === 'undefined' || row[this.setup.replace_list[y].column] === '' || row[this.setup.replace_list[y].column] === null){
                        html = ''
                    } else {
                        html = html.replace(RegExp(this.setup.replace_list[y].var, 'g'), row[this.setup.replace_list[y].column])
                    }
                }
            }
            return html
        }
    },

    tagToggleRender:  function (column, setup , title, tablesetup)
    {
        renderHelpers.initColRef(this, column, setup, tablesetup);
        this.tagid = setup.tagid;
        this.tag = setup.tag;
        if (typeof(setup.tag_ref)!='undefined')
        {
            this.tag_ref = renderHelpers.find_column(setup.tag_ref, tablesetup);
        }

        if (typeof(setup.disabled)=='undefined')
        {
            this.disabled = this.tag
        }
        else
        {
            this.disabled = setup.disabled
        }

        if (typeof(setup.modal)=='undefined')
        {
            this.modalform = 'modaltag'
        }
        else
        {
            this.modalform = setup.modal
        }
        this.render = function (data, type, row, meta)
        {
            start = ''
            if (data!=1)
            {
                btn_class =  'btn-outline-secondary'
                button_text = this.disabled
            }
            else
            {
                btn_class =  'btn-success'
                button_text = this.tag
             //   start = '&zwnj;'
            }
            if (typeof(this.tag_ref) !='undefined')
            {
                button_text = row[this.tag_ref]
            }
            json_data = {
                col: row[this.column].toString(),
                row: meta.row,
                tagid: this.tagid
            }
           return (start + "<button onclick='modal.send_inputs(" + JSON.stringify(json_data) + ")' class='btn " + btn_class + " btn-sm'>" + button_text +"</button>")
         }
    },
}

datatable_config = {}

function setRowClass( row, data, dataIndex, rowDefn)
{
    rowclass = rowDefn.values[data[rowDefn.column]]
    if (typeof(rowclass)!='undefined'){
    $(row).addClass(rowclass)
    }
}


function PythonTable(html_id, tablesetup, ajax_url , options = {})
{
    self = this
    self.initsetup = tablesetup
    self.filters = []
    datatable_config[html_id] = {}
    col_defs = tablesetup.colDefs
    url_renderers = {}
    if (typeof(mobile)=='undefined') mobile=false;
    for (i=0; i< tablesetup.colOptions.length;i++)
    {
        if (mobile && (col_defs[i]['mobile']==false))
        {
            col_defs[i].visible = false
        }
        if (tablesetup.colOptions[i]['renderfn']!=undefined)
        {
            datatable_config[html_id][i] = new renderFunctions[tablesetup.colOptions[i]['renderfn']](i, tablesetup.colOptions[i], tablesetup.titles[i], tablesetup)
            col_defs[i]['render'] = function ( data, type, row, meta ) {
                return datatable_config[meta.settings.sTableId][meta.col].render( data, type, row, meta ) }
        }
    }
    self.columnRender = []

    this.postInit = function (settings, json) {
        var table = self
        self.table.api().on('stateSaveParams.dt', function (e, settings, data) {
            django_datatables.exec_filter(table, 'save_state', data)
        })
        self.table = this
        self.filters = django_datatables.setup[html_id].filters
        self.filters.forEach(function (filter) {
            filter.init(self);
            filter.buildfilter();
            filter.refresh();
        })
        columnsearch = function (settings, data, dataIndex, rowdata) {
            if (settings.sTableId !== self.table_id) {
                return true;
            }
            for (f = 0; f < self.filters.length; f++) {
                if (!self.filters[f].filter(rowdata)) return false
            }
            return true
        }
        $.fn.dataTable.ext.search.push(columnsearch)

        django_datatables.setup[html_id].plugins.forEach(function (plugin) {
            plugin.init(self);
        })

        this.api().draw()
        this.api().on('draw', function () {
            self.filters.forEach(function (filter) {
                filter.refresh()
            })
        });
    }

    if (ajax_url!=''){
        csrf = getCookie('csrftoken');
        ajax_dict = {'url':ajax_url , "type":"POST", "data":{ "csrfmiddlewaretoken":csrf },}
        tabledata = null
       }
    else
    {
        ajax_dict = null
        tabledata = options['data']
    }

    this.all_totals = null
    this.table_id = html_id
    this.tableColumnFilter = {}

    this.filter_section_id = tablesetup.tableOptions['filtersection']

    if (this.filter_section_id==null) this.filter_section_id = '#filterSection'
    buttons = tablesetup.tableOptions['buttons']
    if (buttons==null) buttons = ['csv']
    dom_options = tablesetup.tableOptions.domOptions
    if (dom_options == null) dom_options = 'rtip'

    dataTable_setup = {
  /*  stripeClasses:['a', 'a'],
 /*   rowGroup: {
        dataSrc: '8',
        endRender: function ( rows, group){
        var sum = rows.data().pluck(10).reduce( function( a, b){
        return a + parseInt(b)
            },0)
        return sum
        },
        startClassName:'table-info font-weight-bold',
        endClassName:'font-weight-bold row-border'
    },
 */
        rowReorder:tablesetup.tableOptions.rowReorder,
        orderCellsTop: true,
        pageLength : tablesetup.tableOptions.pageLength,
        fixedHeader: true,
        orderClasses: false,
        stateSave: true,
        ajax: ajax_dict,
        data:tabledata,
        deferRender: true,
        order: tablesetup.tableOptions.order,
        dom: dom_options,
        buttons: buttons,
        columnDefs: col_defs,
        initComplete: this.postInit,
    }
    if (typeof(tablesetup.tableOptions.rowGroup) != 'undefined')
    {
        dataTable_setup['rowGroup'] =
        {
            dataSrc: tablesetup.field_ids.indexOf(tablesetup.tableOptions.rowGroup.dataSrc),
            endRender: function (rows, group)
                       {
                            sums = Array(rows.data()[0].length).fill('')
                            tablesetup.tableOptions.rowGroup.sumColumns.forEach(
                            function (column)
                            {
                                column_no = tablesetup.field_ids.indexOf(column)
                                var sum = rows.data().pluck(column_no).reduce(
                                    function(a, b)
                                    {
                                        return a + parseFloat(b)
                                    },0)
                                sums[column_no] = sum
                            })
                            sums_row = ''
                            for (c=0;c<sums.length;c++)
                            {
                                if (tablesetup.colOptions[c].hidden != true)
                                {
                                    if (typeof(sums[c])=='number')
                                    {
                                        sums_row += '<td class="pr-4">' + sums[c].toFixed(2); + '</td>'
                                    }
                                    else
                                    {
                                        sums_row += '<td></td>'
                                    }
                                }
                            }
                            return $('<tr>' + sums_row + '</tr>')
                       },
            startClassName:'table-info font-weight-bold',
            endClassName:'font-weight-bold white text-right'
        }
    }
    if (typeof(tablesetup.tableOptions.rowColor) !='undefined'){
    dataTable_setup['createdRow'] = function (row,data,dataIndex){
            if (Array.isArray(tablesetup.tableOptions.rowColor))
            {
                for (rc=0;rc<tablesetup.tableOptions.rowColor.length;rc++)
                {
                    setRowClass ( row, data, dataIndex, tablesetup.tableOptions.rowColor[rc])
                }
            }
            else
            {
                setRowClass ( row, data, dataIndex, tablesetup.tableOptions.rowColor)
            }
        }
    }

    this.table = $('#' + this.table_id).dataTable(dataTable_setup);

    if (mobile)
    {
        that = this
        $(html_id + ' tbody').on('click', 'tr', function ()
        {
            window.location.href = that.initsetup.colOptions[0].url.replace('999999', that.table.api().row(this).data()[0])
        })
    }


}



function set_badge( badgeid, curval, total)
{

   // $(badgeid).toggleClass('badge-primary badge-secondary')

   if (curval==0)
    {
        $(badgeid).removeClass('badge-primary')
        $(badgeid).addClass('badge-secondary')
    }
    else
    {
        $(badgeid).addClass('badge-primary')
        $(badgeid).removeClass('badge-secondary')
    }

    if (curval!=total)
    {
        $(badgeid).html(curval + ' / ' + total)
    }
   else
   {
       $(badgeid).html(curval)
   }
}



function add_to_sum(cur_col_val, count_dict , addval )
{
    if (isNaN(addval)) addval = 0;
    if (cur_col_val === "") cur_col_val = 'null'
    if (count_dict[cur_col_val]===undefined)
    {
        count_dict[cur_col_val] = [addval]
    }
    else
    {
        count_dict[cur_col_val][0] += addval
    }
}

function reset_totals_single(total_dict)
{
        for (i in total_dict)
        {
            if (total_dict[i].length == 1)
            {
                total_dict[i] = [0, total_dict[i][0], -1]
            }
            else
            {
                total_dict[i] = [0, total_dict[i][1], total_dict[i][0]]
            }
        }

}



filter_helper =
{
    all_none :` <div class="col-6 text-center">
                    <a class="small all-check" href="javascript:void(0);">all</a>
                </div>
                <div class="col-6 text-center">
                    <a class="small none-check" href="javascript:void(0);">none</a>
                </div>`,

    add_header : function ( filter, htmldata, extra )
    {
         filtersection = `<div class="card my-2">
                            <div class="card-header py-2 filter-header" data-target="#filter_%4">%1</div>
                                <div class="card-body p-2 collapse show" id="filter_%4">
                                    <div class="row pb-2">%9
                                    </div>%2</div></div>`
         if (!extra) extra = ''
         headeroptions = { 9: extra}
         filterheader = rep_options(filtersection , headeroptions )
         textoptions =
         {
            1: filter.title,
            2: htmldata,
            3: filter.column,
            4: filter.title.replace(/\W/g,'')
         }
         return rep_options(filterheader , textoptions )
    }
}

$(document).ready(function() {
    $.fn.dataTable.moment( "DD/MM/YYYY" );
   });
