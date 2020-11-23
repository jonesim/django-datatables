




DataTables = {}

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

function geturl (cell , row, column)
{
    if (row[column + colOptions[column]['link']])  {
        return urls[column].replace ('999999',row[column + colOptions[column]['link']].toString());
    }
    if (row[column + colOptions[column]['javascript']])  {
        return urls[column].replace ('999999',row[column + colOptions[column]['javascript']].toString());
    }

    return null;

}




    function saveFilter()
    {
        filterStore = {}
        $(".filtercheck").each(function ()
        {
            filterStore[$(this).attr("id")] = $(this).prop('checked')
        }).promise().done(function()
        {
            localStorage.setItem('filterStore_'+window.location.pathname,JSON.stringify(filterStore))
        });
    }

    function restoreFilter()
    {
        filterStore = JSON.parse(localStorage.getItem('filterStore_'+window.location.pathname))
        for (i in filterStore)
        {
            $('#'+i).prop('checked', filterStore[i])
        }
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



function filter_tags(pTable, column, title)
{

    this.column = column
    this.pTable = pTable
    this.title = title
    this.html_title = title.replace(/\W/g,'')
    this.colOption = pTable.initsetup.colOptions[this.column]
    this.total = {}

    this.pTable.table.api().column(this.column).data().reduce(function (acc, current) {
            for (v=0;v<current.length;v++)
            {
                add_to_sum( current[v], acc, 1);
            }
            return acc;
            },  this.total  )



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
            this_filter.filter_data = []

            this_filter.filter_data={
                'required': [],
                'include': [],
                'exclude': [],
            }
                filter_section = $("#filter_"+this_filter.html_title + ' .tag-filter').each(function(){
                    id = parseInt(decodeURI($(this).attr("data-value")))
                    if ($(this).hasClass('option-3')){
                        this_filter.filter_data.required.push(id)
                    }
                    else if ($(this).hasClass('option-2')){
                        this_filter.filter_data.include.push(id)

                    }
                    else if ($(this).hasClass('option-4')){
                        this_filter.filter_data.exclude.push(id)

                    }
                }).promise().done( function ()
                { if (refresh) this_filter.pTable.table.api().draw(); })
        }




    this.refresh = function ()
        {

            reset_totals_single(this.total)
            this.pTable.table.api().column(this.column, {"filter":"applied"}).data().reduce(function (acc, current)
            {
                for (v=0;v<current.length;v++)
                {
                  add_to_sum( current[v], acc, 1)
                }
                return acc;
            },  this.total  )

            for (i in this.total)
            {
                partid = this.column + '-' + i.replace(/\W/g,'')
                badgeid = '#chbadge-'+ partid
                set_badge( badgeid, this.total[i][0] , this.total[i][1])
            }
        }

    this.filter = function ( data )
        {
            if (this.filter_data.length==this.colOption.filter_len) return true
            notfound = true
            for (req=0; req<this.filter_data.required.length; req++){
                    if (data[this.column].indexOf(this.filter_data.required[req])<0)
                    {
                        return false
                    }
                    notfound = false
            }
            for (ex=0; ex<this.filter_data.exclude.length; ex++){
                    if (data[this.column].indexOf(this.filter_data.exclude[ex])>=0)
                    {
                        return false
                    }
            }
            if (this.filter_data.include.length == 0) {return true}
            for (itag=0;itag<data[this.column].length;itag++)
            {
                if (data[this.column][itag]<0x10000)
                {
                    curtag = data[this.column][itag]
                    if (this.filter_data.include.indexOf(curtag)>=0 )
                    {
                        notfound = false
                    }
                }
            }
            if (notfound===true) return false
            return true
        }

    this.html = function ()
        {

            tagsection = `  <div class="filter-header" id="tagsec-%3-%1" data-target="#collapsesect%3_%4">
                            <li class="list-group-item list-group-item-secondary p-1 my-1">%1
                                <span id="chbadge-%3-%4" class="small badge badge-pill badge-primary mx-1">%2</span>
                            </li>
                            </div>
                            <div id="collapsesect%3_%4" class="collapse">`

            tagcheckbox = ` <div id="ch-div-%3-%4">

 
 
                            <div class="float-right">
                            <span id="chbadge-%3-%4" class="small badge badge-pill badge-primary">0</span>
                            </div> 
                            <span class="form-check-label small">
                            <span id="chkt-%3-%5" data-value="%4" class="tag-filter option-1"> </span>
                            %1</span>
                            </div>`
            endsection = `</div>`
            html = ""
            insection = false

            for (l=0;l<this.colOption['lookup'].length;l++)
            {
                curlookup = this.colOption['lookup'][l]
                if (curlookup[0]>=0x10000)
                {
                    if (insection) html += endsection
                    insection = true
                    html_source = tagsection
                }
                else
                {
                    html_source = tagcheckbox
                }
                textoptions =
                {
                    1: curlookup[1],
                    4: curlookup[0],
                    5: curlookup[1].replace(/\W/g,'')
                }
                html += rep_options( html_source, textoptions )
            }
            if (insection) html += endsection

            return filter_helper.add_header(this, html, filter_helper.all_none)

        }

    this.checkall = function(data)
        {
            this_filter = data.data.filter
            $("#filter_"+this_filter.html_title + ' .tag-filter').each(function ()
            {
                $(this).removeClass("option-2 option-3 option-4");
                $(this).addClass("option-1");
                }).promise().done(function()
                {
                    this_filter.buildfilter(data)
                });
        }

    this.change_multi_input = function(data)
    {
        option_pos = this.className.indexOf('option-') + 7;
        current_option = parseInt(this.className.substring(option_pos, option_pos + 1));
        $(this).removeClass('option-' + current_option.toString());
        current_option += 1;
        if (current_option == 5) {
            current_option = 1;
        }
        $(this).addClass('option-' + current_option.toString());
        data.data.filter.buildfilter(data)
    }
    this.setup_events = function ()
        {
            $("#filter_"+this.html_title).find(".filtercheck").change( {filter: this} , this.buildfilter )
            $("#filter_"+this.html_title).find(".all-check").click( {filter: this, checked: true} , this.checkall )
            $("#filter_"+this.html_title).find(".none-check").click( {filter: this, checked: false} , this.checkall )
            $("#filter_"+this.html_title +" .tag-filter").click(  {filter: this}, this.change_multi_input)
        }

}


function numberWithCommas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function pivot_totals(pTable, column, title)
{
    this.column = column
    this.pTable = pTable
    this.title = title
    this.html_title = title.replace(/\W/g,'')
    this.total = {}
    this.filter_data = []
    this.colOption = pTable.initsetup.colOptions[this.column]
    this.sortkeys = []

    for (j=0;j<pTable.initsetup.colDefs.length;j++)
    {
                if (pTable.initsetup.colDefs[j]['name']==this.colOption['sumRef'])
                {
                    this.sumcolumn = j
                }
            }
    that = this
    this.pTable.table.api().data().toArray().reduce(function (acc, current) {
            add_to_sum( current[that.column], acc, parseInt(current[that.sumcolumn]));
            return acc;
            },  that.total )

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
            this_filter.filter_data = []
            $("#filter_"+this_filter.html_title).find(".filtercheck:checked").each(function (){
                    this_filter.filter_data.push (decodeURI($(this).attr("data-value")))
            }).promise().done( function ()
                { if (refresh) this_filter.pTable.table.api().draw();
                 saveFilter();
                 })
        }

    this.filter = function ( data )
        {
            var col_data = data[this.column]
            if (typeof(col_data) == 'number') col_data = col_data.toString();
            if (this.filter_data.indexOf(col_data)<0)
            {
                if (col_data=="" | col_data==null)
                {
                    if (this.filter_data.indexOf("null")<0) return false
                }
            else return false
            }
            return true
        }
    this.refresh = function ()
        {
            reset_totals_single(this.total)
            that = this
            this.pTable.table.api().rows({ filter : 'applied'}).data().toArray().reduce(function (acc, current) {
            add_to_sum( current[that.column], acc, parseInt(current[that.sumcolumn]));
            return acc;
            },  that.total )
            graph_data = []
            for (j=0;j<this.sortkeys.length;j++)
            {
                i = this.sortkeys[j]
                graph_data.push({xaxis:i, yaxis:this.total[i][0]})
                if (this.total[i][0] != this.total[i][2])
                {
                    partid = this.column + '-' + i.replace(/\W/g,'')
                    $('#chfilteredtotal-' + partid).html(numberWithCommas(this.total[i][0]))
                    if (this.total[i][0]!=this.total[i][1])
                    {
                        $('#chtotal-' + partid).html(numberWithCommas(this.total[i][1]));
                    }
                    else
                    {
                        $('#chtotal-' + partid).html('');

                    }
                }

            }
            if (typeof (chart)!='undefined') chart.data = graph_data;
        }

    this.html = function ()
        {
            htmlcheckbox = `<tr><td>
                                    <div id="ch-div-%3-%5" class="form-check float-left">
                                        <label class="form-check-label">
                                        <input id="chkf-%3-%5" data-value="%6" type="checkbox" class="form-check-input filtercheck" checked>%1</label>
                                    </div>
                                </td>
                                <td class="pr-1 text-right text-secondary" id="chtotal-%3-%5" >
                                </td>
                                <td class="text-right" id="chfilteredtotal-%3-%5">
                                </td>
                             </tr>`
            htmldata = '<table class="small w-100"><tr><td></td><td class="text-right text-secondary">Total</td><td class="text-right">Filtered</td></tr>'
            this.sortkeys = []
            for (i in this.total)
            {
                if (this.total[i][0]>0) this.sortkeys.push(i)
            }
            this.sortkeys.sort()
            for (j=0;j<this.sortkeys.length;j++)
            {
                i = this.sortkeys[j]
                replace_options =
                {
                    1: i,
                    5: i.replace(/\W/g,''),
                    6: encodeURI(i)
                }
                htmldata += rep_options( htmlcheckbox, replace_options)
            }
            htmldata += '</table>'
            return filter_helper.add_header(this, htmldata, filter_helper.all_none)
        }
    this.checkall = function(data)
        {
            this_filter = data.data.filter
            $("#filter_"+this_filter.html_title).find(".filtercheck").each(function ()
            {
                $(this).prop('checked',data.data.checked)
                }).promise().done(function()
                {
                    this_filter.buildfilter(data)
                });
        }

    this.setup_events = function ()
        {
            $("#filter_"+this.html_title).find(".filtercheck").change( {filter: this} , this.buildfilter )
            $("#filter_"+this.html_title).find(".all-check").click( {filter: this, checked: true} , this.checkall )
            $("#filter_"+this.html_title).find(".none-check").click( {filter: this, checked: false} , this.checkall )
        }
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



function filter_pivot(pTable, column, title)
{
    this.column = column
    this.pTable = pTable
    this.title = title
    this.html_title = title.replace(/\W/g,'')
    this.total = {}
    this.filter_data = []

    this.pTable.table.api().column(this.column).data().reduce(function (acc, current) {
            add_to_sum( current, acc, 1);
            return acc;
            },  this.total  )



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
            this_filter.filter_data = []
            $("#filter_" + this_filter.html_title).find(".filtercheck:checked").each(function (){
                    this_filter.filter_data.push (decodeURI($(this).attr("data-value")))
            }).promise().done( function ()
                { if (refresh) this_filter.pTable.table.api().draw();
                 saveFilter();
                 })
        }


    this.filter = function ( data )
        {
            var col_data = data[this.column]
            if (typeof(col_data) == 'number') col_data = col_data.toString();
            if (this.filter_data.indexOf(col_data)<0)
            {
                if (col_data=="" | col_data==null)
                {
                    if (this.filter_data.indexOf("null")<0) return false
                }
            else return false
            }
            return true
        }

    this.refresh = function ()
        {
            reset_totals_single(this.total)
            this.pTable.table.api().column(this.column, {"filter":"applied"}).data().reduce(function (acc, current)
            {
                add_to_sum( current, acc, 1);
                return acc;
            },  this.total  )
            for (i in this.total)
            {
                if (this.total[i][0] != this.total[i][2]){
                partid = this.column + '-' + i.replace(/\W/g,'')
                badgeid = $('#chbadge-'+ partid)
                set_badge( badgeid, this.total[i][0] , this.total[i][1])
            }
          /* remove items if none
            if (this.total[i][0]==0)  $('#ch-div-' + partid).hide();      */
            }
        }


    this.html = function ()
        {
            htmlcheckbox = `
                           <div class="w-100 float-left">
                                <div id="ch-div-%3-%5" class="form-check float-left">
                                    <label class="form-check-label small">
                                    <input id="chkf-%3-%5" data-value="%6" type="checkbox" class="form-check-input filtercheck" checked>%1</label>
                                </div>
                                <span id="chbadge-%3-%5" class="small badge badge-pill badge-primary float-right">-</span>
                            </div>`
            htmldata = ''
            sortkeys = []
            for (i in this.total)
            {
                if (this.total[i][0]>0) sortkeys.push(i)
            }
            sortkeys.sort()

            for (j=0;j<sortkeys.length;j++)
            {
                i = sortkeys[j]
                replace_options =
                {
                    1: i,
                    5: i.replace(/\W/g,''),
                    6: encodeURI(i)
                }
                htmldata += rep_options( htmlcheckbox, replace_options)
            }
            return filter_helper.add_header(this, htmldata, filter_helper.all_none)
        }

    this.checkall = function(data)
        {
            this_filter = data.data.filter
            $("#filter_"+this_filter.html_title).find(".filtercheck").each(function ()
            {
                $(this).prop('checked',data.data.checked)
                }).promise().done(function()
                {
                    this_filter.buildfilter(data)
                });
        }

    this.setup_events = function ()
        {
            $("#filter_"+this.html_title).find(".filtercheck").change( {filter: this} , this.buildfilter )
            $("#filter_"+this.html_title).find(".all-check").click( {filter: this, checked: true} , this.checkall )
            $("#filter_"+this.html_title).find(".none-check").click( {filter: this, checked: false} , this.checkall )
        }
}



function filter_select2(pTable, column, title)
{
    this.column = column
    this.pTable = pTable
    this.title = title
    this.total = {}
    this.filter_data = []

    this.pTable.table.api().column(this.column).data().reduce(function (acc, current) {
            add_to_sum( current, acc, 1);
            return acc;
            },  this.total  )



    this.buildfilter = function(data)
        {
            if (data!=undefined)
            {
                this_filter = data.data.filter
                refresh = true
            }
            else return
            this_filter.filter_data = []
            selected = $("#select2_"+this_filter.title).select2('data')
            for (i=0;i<selected.length;i++)
            {
                this_filter.filter_data.push(selected[i].text)
            }
            this_filter.pTable.table.api().draw()
        }


    this.filter = function ( data )
        {
        col_data = data[this.column]
            if (this.filter_data.length==0) return true
            if (this.filter_data.indexOf(col_data)<0)
            {
                if (col_data=="" | data[this.column]==null)
                {
                    if (this.filter_data.indexOf("null")<0) return false
                }
            else return false
            }
            return true
        }

    this.refresh = function ()
        {
            reset_totals_single(this.total)
            this.pTable.table.api().column(this.column, {"filter":"applied"}).data().reduce(function (acc, current)
            {
                add_to_sum( current, acc, 1);
                return acc;
            },  this.total  )
            for (i in this.total)
            {
                if (this.total[i][0] != this.total[i][2]){
                partid = this.column + '-' + i.replace(/\W/g,'')
                badgeid = $('#chbadge-'+ partid)
                set_badge( badgeid, this.total[i][0] , this.total[i][1])
            }
          /* remove items if none
            if (this.total[i][0]==0)  $('#ch-div-' + partid).hide();      */
            }
        }


    this.html = function ()
        {
            optionhtml = `<option value="%6">%1</option>`
            htmldata = ''
            sortkeys = []
            for (i in this.total)
            {
                if (this.total[i][0]>0) sortkeys.push(i)
            }
            sortkeys.sort()

            for (j=0;j<sortkeys.length;j++)
            {
                i = sortkeys[j]
                replace_options =
                {
                    1: i,
                    5: i.replace(/\W/g,''),
                    6: encodeURI(i)
                }
                htmldata += rep_options( optionhtml, replace_options)
            }

            htmldata = '<select style="width:100%" multiple="multiple" id="select2_'+ this.title +  '">' + htmldata + '</select>'
            return filter_helper.add_header(this, htmldata)
        },


    this.format_template = function(that) { return function (state)
    {

        if (state.loading) return
        if (that.total[state.text][0]>0)
        {
            retstr = $('<span>' + state.text +'<span class="mx-1 small badge badge-pill badge-primary">' + that.total[state.text][0] + '/' + that.total[state.text][1] + '</span></span>')
        }
        else
        {
            retstr = $('<span>' + state.text +'<span class="mx-1 small badge badge-pill badge-secondary">' + that.total[state.text][0] + '/' + that.total[state.text][1] + '</span></span>')

        }
        return retstr
    }
    }
    this.setup_events = function ()
        {

       //     this.format_template('',null,this.total)
      //      console.log("#select2_"+this.title)


             $("#select2_"+this.title).select2({
              templateResult: this.format_template(this),
              templateSelection: this.formattemplate,}).change({filter: this} , this.buildfilter);


         //   $("#select2_"+this.title).select2().change({filter: this} , this.buildfilter);
  //          $("#filter_"+this.title).find(".filtercheck").change( {filter: this} , this.buildfilter )
   //         $("#filter_"+this.title).find(".all-check").click( {filter: this, checked: true} , this.checkall )
    //        $("#filter_"+this.title).find(".none-check").click( {filter: this, checked: false} , this.checkall )
        }
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

function testswitch(control)
{
    console.log(control)
    console.log($(control).closest('tr'))
    table_id = ($(control).closest('table')[0].id)
    console.log(DataTables[table_id])
    console.log(DataTables[table_id].table.api().row( $(control).closest('tr') ).data())
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


    toggleRender : function (column, setup, title, tablesetup)
    {
        toggle = '<input onchange="testswitch(this)" class="checkboxinput" type="checkbox" data_toggle="toggle" data_size="small", data_on="YES", data_off="NO">'
        renderHelpers.initUrl(this, column, setup)
        renderHelpers.initColRef(this, column, setup, tablesetup)
        this.js = setup['javascript']
        this.css_class = ''
        if (setup['css_class']!=undefined) this.css_class = ' class="' + setup['css_class'] + '"'
        this.title = title
        if (setup['text']!=undefined) this.globaltext = setup['text']; else this.globaltext = title
        this.render = function (data, type, row, meta)
        {
            if (data === null || data === "") text = this.globaltext; else text = data;
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
            return toggle
            return '<a href="javascript:' + js + '"' + this.css_class +'">' + text + '</a>';
        }
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
            console.log('g')
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
    DataTables[html_id] = this
    self.filters = []
    datatable_config[html_id.substring(1)] = {}
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
            datatable_config[html_id.substring(1)][i] = new renderFunctions[tablesetup.colOptions[i]['renderfn']](i, tablesetup.colOptions[i], tablesetup.titles[i], tablesetup)
            col_defs[i]['render'] = function ( data, type, row, meta ) {
                return datatable_config[meta.settings.sTableId][meta.col].render( data, type, row, meta ) }
        }
    }
    self.columnRender = []

    this.columnsearch = function( settings, data, dataIndex , rowdata ) {
            for (f=0; f<self.filters.length;f++)
            {
                if (!self.filters[f].filter(rowdata)) return false
            }
            return true
    }


    this.postInit = function (settings, json){
            self.table = this
            header = self.table.api().columns().header()
            self.no_columns = header.length
            for (o=0;o<self.no_columns;o++)
            {
                if (tablesetup.colOptions[o]['select2']==true) self.filters.push(new filter_select2(self, o, $(header[o]).html()))
                if (tablesetup.colOptions[o]['pivot']==true) self.filters.push(new filter_pivot(self, o, $(header[o]).html()))
                if (typeof(tablesetup.colOptions[o]['lookup'])=='object') self.filters.push(new filter_tags(self, o, $(header[o]).html()))
                if (tablesetup.colOptions[o]['datefilter']==true) self.filters.push(new filter_date(self, o, $(header[o]).html()))
                if (tablesetup.colOptions[o]['total']==true) self.filters.push(new filter_totals(self, o, $(header[o]).html()))
                if (tablesetup.colOptions[o]['pivottotals']==true) self.filters.push(new pivot_totals(self, o, $(header[o]).html()))
            }

            a = self.table.api().data()
            filterHtml = '<input id="search_'+ html_id.substring(1) +'" type="text" class="form-control" placeholder="Search">'
            self.filters.forEach(function(filter){filterHtml += filter.html()})
            $(self.filter_section_id).html(filterHtml)
            restoreFilter()

            $('#search_' + html_id.substring(1)).keyup(function() {
                self.table.api().search( this.value ).draw();
             });

            $(self.filter_section_id).addClass('filtersection')

            self.filters.forEach(function(filter){
                filter.buildfilter()
                filter.setup_events()
                })
            $('.'+ self.table_id.substring(1) + '-column-search').each(function (){
                searchterm = this.value
                if ($(this).attr('data-col')!='') {
                    self.table.api().column($(this).attr('data-col') + ':name').search(searchterm, false, true, true)
                }
               })
            this.api().draw()
            self.filters.forEach(function(filter){
                filter.refresh()
                })

            $(".filter-header").click(function(){ $($(this).attr('data-target')).toggle(200) })

            self.table.api().on('draw', function (){
                self.filters.forEach(function(filter)
                {filter.refresh()
                })
                    //$('.checkboxinput').bootstrapToggle();
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

    this.table = $(this.table_id).dataTable(dataTable_setup);

    $.fn.dataTable.ext.search.push(this.columnsearch)

    this.configureSelect = function ()
    {
        $(this.table_id + ' tbody').on( 'change', 'select', function () {
            var cell = this.table.api().cell( $(this).parents('td') );
            var row = this.table.api().row( $(this).parents('tr') );
            var row_data = row.data();
            var column = cell.index().column;
            var url = geturl(cell, row_data, column);
    	    var update_column = column + colOptions[column]['selected'];
            $.post(
                url,
                { 'new_status': $("option:selected", this).text() },
                function(result, status){
                row_data[ update_column ] = result.new_status;
                    this.table.api().row( row ).data( row_data ).draw();
                }
            );
        });
    }

    this.configureSelect()

    if (mobile)
    {
        that = this
        $(html_id + ' tbody').on('click', 'tr', function ()
        {
            window.location.href = that.initsetup.colOptions[0].url.replace('999999', that.table.api().row(this).data()[0])
        })
    }

  //  $('#dt_search').val(this.table.api().search());
/*    $(this.table_id + ' thead tr:eq(1) th').each( function () {
        var title = $(this).text();
        colnumber = $(this).attr('id').replace('colSearch','')-1
        $(this).html( '<input type="text" class="form-control form-control-sm small ' + self.table_id.substring(1) + '-column-search" value="' + self.table.api().column(colnumber).search()+'" data-col="' + colnumber + '"/>' );
    } );
*/

//    this.table.api().columns().every(function (index)
 //   {
//        $(self.table_id + ' thead tr:eq(1) th:eq(' + index + ') input').on('keyup change', function ()
        $('.'+ self.table_id.substring(1) + '-column-search').on('keyup change', function ()
        {
                if ($(this).is('select'))
                {
                    id = $(this).attr('id')
                    searchterm = ($('#' + id +' option:selected').text())
                }
                else
                {
                    searchterm = this.value
                }
                 self.table.api().column($(this).attr('data-col') + ':name')
                .search(searchterm, false ,true, true)
                .draw();

        })
     //   })
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
