



function _createForOfIteratorHelper(o, allowArrayLike) { var it = typeof Symbol !== "undefined" && o[Symbol.iterator] || o["@@iterator"]; if (!it) { if (Array.isArray(o) || (it = _unsupportedIterableToArray(o)) || allowArrayLike && o && typeof o.length === "number") { if (it) o = it; var i = 0; var F = function F() {}; return { s: F, n: function n() { if (i >= o.length) return { done: true }; return { done: false, value: o[i++] }; }, e: function e(_e) { throw _e; }, f: F }; } throw new TypeError("Invalid attempt to iterate non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); } var normalCompletion = true, didErr = false, err; return { s: function s() { it = it.call(o); }, n: function n() { var step = it.next(); normalCompletion = step.done; return step; }, e: function e(_e2) { didErr = true; err = _e2; }, f: function f() { try { if (!normalCompletion && it.return != null) it.return(); } finally { if (didErr) throw err; } } }; }

function _unsupportedIterableToArray(o, minLen) { if (!o) return; if (typeof o === "string") return _arrayLikeToArray(o, minLen); var n = Object.prototype.toString.call(o).slice(8, -1); if (n === "Object" && o.constructor) n = o.constructor.name; if (n === "Map" || n === "Set") return Array.from(o); if (n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)) return _arrayLikeToArray(o, minLen); }

function _arrayLikeToArray(arr, len) { if (len == null || len > arr.length) len = arr.length; for (var i = 0, arr2 = new Array(len); i < len; i++) { arr2[i] = arr[i]; } return arr2; }

if (typeof Object.assign != 'function') {
  Object.assign = function(target) {
    'use strict';
    if (target == null) {
      throw new TypeError('Cannot convert undefined or null to object');
    }

    target = Object(target);
    for (var index = 1; index < arguments.length; index++) {
      var source = arguments[index];
      if (source != null) {
        for (var key in source) {
          if (Object.prototype.hasOwnProperty.call(source, key)) {
            target[key] = source[key];
          }
        }
      }
    }
    return target;
  };
}

if (typeof django_datatables === 'undefined') {
  var django_datatables = function () {
    var setup = {};
    var DataTables = {};

    function b_r(button) {
      var command = $(button).attr('data-command');
      var row_id = $(button).closest('tr').attr('id');
      var table_id = $(button).closest('table').attr('id');
      DataTables[table_id].send_row(command, row_id);
    }

    ajax_helpers.command_functions.delete_row = function (command) {
      DataTables[command.table_id].table.api().row('#' + command.row_no).remove();
      DataTables[command.table_id].table.api().draw(false);
    };

    ajax_helpers.command_functions.refresh_row = function (command) {
      DataTables[command.table_id].table.api().row('#' + command.row_no).data(command.data).invalidate();
    };

    ajax_helpers.command_functions.reload_table = function (command) {
      DataTables[command.table_id].table.api().ajax.reload(null, false);
    };

    var utilities = {
      numberWithCommas: function numberWithCommas(x) {
        var decimal_places = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 0;
        return x.toFixed(decimal_places).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
      }
    };

    var columnsearch = function columnsearch(settings, data, dataIndex, row_data) {
      if (settings.sTableId in DataTables) {
        for (var f = 0; f < DataTables[settings.sTableId].filters.length; f++) {
          if (!DataTables[settings.sTableId].filters[f].filter(row_data)) return false;
        }

        return true;
      }

      return true;
    };

    $.fn.dataTable.ext.search.push(columnsearch);

    function init_setup(table_id) {
      if (typeof setup[table_id] === 'undefined') setup[table_id] = {};
    }

    function add_to_setup_list(table_id, setup_type, value) {
      init_setup(table_id);

      if (typeof setup[table_id][setup_type] === "undefined") {
        setup[table_id][setup_type] = [];
      }

      setup[table_id][setup_type].push(value);
    }

    function add_to_setup(table_id, setup_key, value) {
      init_setup(table_id);

      if (typeof setup[table_id].datatable_setup === "undefined") {
        setup[table_id].datatable_setup = {};
      }

      setup[table_id].datatable_setup[setup_key] = value;
    }

    function add_filter(table_id, filter) {
      add_to_setup_list(table_id, 'filters', filter);
    }

    function add_plugin(table_id, plugin) {
      add_to_setup_list(table_id, 'plugins', plugin);
    }

    function FilterCalcs(column_no) {
      this.column = column_no;
      this.calcs = {};
      this.count = 0;
      this.sorted_keys = null;
      this.sort_keys = /*#__PURE__*/regeneratorRuntime.mark(function _callee() {
        var i;
        return regeneratorRuntime.wrap(function _callee$(_context) {
          while (1) {
            switch (_context.prev = _context.next) {
              case 0:
                if (this.sorted_keys == null) {
                  this.sorted_keys = [];

                  for (i in this.calcs) {
                    this.sorted_keys.push(i);
                  }

                  this.sorted_keys.sort();
                }

                i = 0;

              case 2:
                if (!(i < this.sorted_keys.length)) {
                  _context.next = 8;
                  break;
                }

                _context.next = 5;
                return this.sorted_keys[i];

              case 5:
                i++;
                _context.next = 2;
                break;

              case 8:
              case "end":
                return _context.stop();
            }
          }
        }, _callee, this);
      });

      this.badge_string = function (key) {
        var result = this.calcs[key];

        if (result == undefined) {
          return '-';
        } else if (result[0] === result[1]) {
          return result[0].toString();
        } else {
          return result[0].toString() + ' / ' + result[1].toString();
        }
      };

      this.badge_colour = function (key) {
        if (this.calcs[key] == undefined) {
          return ['badge-secondary', 'badge-primary'];
        } else if (this.calcs[key][0] > 0) {
          return ['badge-primary', 'badge-secondary'];
        } else {
          return ['badge-secondary', 'badge-primary'];
        }
      };

      this.get_key = function (row) {
        var value = row[this.column];
        if (value === "") value = 'null';
        return value;
      };

      this.get_value = function (row) {
        return 1;
      };

      this.init_calcs = function (row) {
        var value = this.get_value(row);
        this.count += 1;
        var key = this.get_key(row);

        if (!Array.isArray(key)) {
          key = [key];
        }

        for (var k = 0; k < key.length; k++) {
          if (key[k] in this.calcs) {
            this.calcs[key[k]][1] += value;
          } else {
            this.calcs[key[k]] = [0, value];
          }
        }
      };

      this.clear_calcs = function () {
        for (var i in this.calcs) {
          this.calcs[i][0] = 0;
        }
      };

      this.add_calcs = function (row) {
        var value = this.get_value(row);
        var item = this.get_key(row);

        if (Array.isArray(item)) {
          for (var i = 0; i < item.length; i++) {
            this.calcs[item[i]][0] += value;
          }
        } else {
          this.calcs[item][0] += value;
        }
      };
    }

    function FilterBase(column_no, html_id, options) {
      this.column_no = column_no;
      this.html_id = html_id;
      this.options = options;
      this.filter_data = [];
      this.filter_calcs = new django_datatables.FilterCalcs(this.column_no);
    }

    FilterBase.prototype.save_state = function (data) {
      try {
        data.columns[this.column_no][this.storage_key] = this.save_data();
      } catch (e) {
        console.log(e);
      }
    };

    FilterBase.prototype.this_fn = function (call_function, parameter) {
      var this_filter = this;
      return function () {
        this_filter[call_function](parameter, this);
      };
    };

    FilterBase.prototype.restore_state = function (data) {
      try {
        var state_data = this.pTable.table.api().state.loaded().columns[this.column_no][this.storage_key];
      } catch (e) {
        console.log(e);
        return;
      }

      if (typeof state_data !== 'undefined') {
        this.load_state(state_data);
      }
    };

    FilterBase.prototype.this_fn_parameter = function (call_function) {
      var this_filter = this;
      return function (param) {
        return this_filter[call_function](param);
      };
    };

    FilterBase.prototype.init = function (table) {
      this.pTable = table;
    };

    FilterBase.prototype.refresh = function () {};

    FilterBase.prototype.set_status_class = function (status) {
      var element = $("#" + this.html_id);

      switch (status) {
        case 'all':
          element.removeClass('filter-none filter-active');
          element.addClass('filter-all');
          break;

        case 'none':
          element.removeClass('filter-active filter-all');
          element.addClass('filter-none');
          break;

        default:
          element.removeClass('filter-none filter-all');
          element.addClass('filter-active');
      }
    };

    FilterBase.prototype.set_badge = function (badge, key) {
      var colours = this.filter_calcs.badge_colour(key);
      $(badge).addClass(colours[0]);
      $(badge).removeClass(colours[1]);
      $(badge).html(this.filter_calcs.badge_string(key));
    };

    function PivotFilter(column_no, html_id, options) {
      this.storage_key = 'pivot_filter';
      django_datatables.FilterBase.call(this, column_no, html_id, options);

      this.load_state = function (state_data) {
        $('.filtercheck', '#' + this.html_id).each(function () {
          $(this).prop('checked', state_data[$(this).attr('data-value')]);
        });
      };

      this.save_data = function () {
        var pivot_data = {};
        $(".filtercheck", '#' + this.html_id).each(function () {
          pivot_data[$(this).attr('data-value')] = $(this).prop('checked');
        });
        return pivot_data;
      };

      this.filter = function (data) {
        var col_data = data[this.column_no];
        if (typeof col_data === 'number') col_data = col_data.toString();

        if (this.filter_data.indexOf(col_data) < 0) {
          if (col_data == "" | col_data == null) {
            if (this.filter_data.indexOf("null") < 0) return false;
          } else return false;
        }

        return true;
      };

      this.refresh = function () {
        var this_filter = this;
        $(".badge", '#' + this.html_id).each(function () {
          this_filter.set_badge(this, decodeURI($(this).attr("data-value")));
        });
      };

      this.buildfilter = function (refresh) {
        this.filter_data = [];
        var checkboxes = $(".filtercheck:checked", '#' + this.html_id);

        for (var c = 0; c < checkboxes.length; c++) {
          this.filter_data.push(decodeURI($(checkboxes[c]).attr("data-value")));
        }

        if (this.filter_data.length === Object.keys(this.filter_calcs.calcs).length) {
          status = 'all';
        } else if (this.filter_data.length === 0) {
          status = 'none';
        } else {
          status = '';
        }

        this.set_status_class(status);

        if (refresh) {
          this.pTable.table.api().draw();
        }
      };

      this.html = function () {
        var htmldata = '';

        var _iterator = _createForOfIteratorHelper(this.filter_calcs.sort_keys()),
            _step;

        try {
          for (_iterator.s(); !(_step = _iterator.n()).done;) {
            var k = _step.value;
            htmldata += this.options.htmlcheckbox.replace(/%1/g, k).replace(/%6/g, encodeURI(k));
          }
        } catch (err) {
          _iterator.e(err);
        } finally {
          _iterator.f();
        }

        var context = $('#' + this.html_id);
        $('.filter-content', context).html(htmldata);
        $(".filtercheck", context).change(this.this_fn('buildfilter', true));
        $(".all-check", context).click(this.this_fn('checkall', true));
        $(".none-check", context).click(this.this_fn('checkall', false));
        this.restore_state();
        this.buildfilter(false);
      };

      this.checkall = function (checked) {
        $("#" + this.html_id + " .filtercheck").each(function () {
          $(this).prop('checked', checked);
        }).promise().done(this.this_fn('buildfilter', true));
      };

      this.clear = function () {
        this.checkall(true);
      };
    }

    PivotFilter.prototype = Object.create(FilterBase.prototype);

    var column_render = function column_render(column, render_functions, tablesetup) {
      var rf = [];

      for (var r = 0; r < render_functions.length; r++) {
        rf.push(new django_datatables.data_processing[render_functions[r].function](column, render_functions[r], tablesetup));
      }

      return function (data, type, row, meta) {
        data = rf[0].process(data, type, row, meta);

        for (r = 1; r < rf.length; r++) {
          data = rf[r].process(data, type, row, meta);
        }

        return data;
      };
    };

    var BaseProcessAjaxData = function BaseProcessAjaxData(column, params, table) {
      this.column = column;

      if (table.initsetup.colOptions[column].field_array == true) {
        this.field_array = true;
      }

      if (typeof params.column === 'string') {
        var column_index = params.column.split(':');
        params.column = table.find_column(column_index[0]);

        if (column_index.length > 1) {
          params.index = parseInt(column_index[1]);
        }
      } else if (params.column === undefined) {
        params.column = column;
      }

      if (params.var != undefined) {
        if (Array.isArray(params.var)) {
          this.reg_exp = [];

          for (var i = 0; i < params.var.length; i++) {
            this.reg_exp.push(RegExp(params.var[i], 'g'));
          }
        } else {
          this.reg_exp = RegExp(params.var, 'g');
        }
      }

      if (params.null_value === undefined) {
        this.null_value = '';
      } else {
        this.null_value = params.null_value;
      }

      this.params = params;

      if (table.initsetup.colOptions[this.column].lookup != undefined) {
        this.lookup = {};

        for (var lv = 0; lv < table.initsetup.colOptions[this.column].lookup.length; lv++) {
          this.lookup[table.initsetup.colOptions[this.column].lookup[lv][0]] = table.initsetup.colOptions[this.column].lookup[lv][1];
        }
      }
    };

    BaseProcessAjaxData.prototype.determine_value = function (value) {
      if (this.field_array && value != null && this.params.index != undefined) {
        return value[this.params.index];
      }

      return value;
    };

    BaseProcessAjaxData.prototype.determine_html = function (value, current) {
      if (value == null) {
        return this.null_value;
      }

      if (this.params.gte != undefined && value >= this.params.gte) {
        return this.params.alt_html;
      }

      if (this.params.html == undefined) return String(current);
      return this.params.html;
    };

    BaseProcessAjaxData.prototype.process = function (column_data, type, row, meta) {
      if (Array.isArray(column_data) && !this.field_array) {
        var column_val = [];

        for (var a = 0; a < column_data.length; a++) {
          if (this.params.column === meta.col) {
            column_val[a] = this.convert(column_data[a], row[this.params.column][a], meta, row);
          } else {
            column_val[a] = this.convert(column_data[a], row[this.params.column], meta, row);
          }
        }

        return column_val.join(' ');
      } else {
        return this.convert(column_data, row[this.params.column], meta, row);
      }
    };

    var data_processing = {
      Row: function Row(column, params, table) {
        django_datatables.BaseProcessAjaxData.call(this, column, params, table);

        if (params.html === undefined) {
          this.convert = function (current, value, meta, row) {
            return current.replace(params.var, meta.settings.rowId(row));
          };
        } else {
          this.convert = function (current, value, meta, row) {
            return params.html.replace(params.var, meta.setup.rowId(row));
          };
        }
      },
      Replace: function Replace(column, params, table) {
        django_datatables.BaseProcessAjaxData.call(this, column, params, table);

        if (Array.isArray(this.reg_exp) && table.initsetup.colOptions[column].field_array) {
          this.convert = function (current, value) {
            var html = this.determine_html(value, current);

            try {
              for (var v = 0; v < this.reg_exp.length; v++) {
                html = html.replace(this.reg_exp[v], this.determine_value(value[v]));
              }

              return html;
            } catch (e) {
              return '';
            }
          }.bind(this);
        } else {
          this.convert = function (current, value) {
            var convert_value = this.determine_value(value);
            return this.determine_html(convert_value, current).replace(this.reg_exp, convert_value);
          }.bind(this);
        }
      },
      ReplaceLookup: function ReplaceLookup(column, params, table) {
        django_datatables.BaseProcessAjaxData.call(this, column, params, table);

        if (Array.isArray(this.reg_exp)) {
          this.convert = function (current, value) {
            var html = this.params.html;

            for (var v = 0; v < this.reg_exp.length; v++) {
              html = html.replace(this.reg_exp[v], this.lookup[value][v]);
            }

            return html;
          };
        } else {
          this.convert = function (current, value) {
            var convert_value = this.determine_value(value);
            return this.determine_html(convert_value, current).replace(this.reg_exp, this.lookup[convert_value]);
          }.bind(this);
        }
      },
      Html: function Html(column, params, table) {
        django_datatables.BaseProcessAjaxData.call(this, column, params, table);

        this.convert = function () {
          return params.html;
        };
      },
      ValueInColumn: function ValueInColumn(column, params, table) {
        django_datatables.BaseProcessAjaxData.call(this, column, params, table);
        var new_value;

        this.convert = function (current, value) {
          if (value.indexOf(params.value) >= 0) {
            new_value = params.choices[0];
          } else {
            new_value = params.choices[1];
          }

          if (params.html === undefined) {
            return current.replace(params.var, new_value);
          } else {
            return params.html.replace(params.var, new_value);
          }
        }.bind(this);
      },
      MergeArray: function MergeArray(column, params, table) {
        django_datatables.BaseProcessAjaxData.call(this, column, params, table);

        if (params.separator == undefined) {
          this.separator = ' ';
        } else {
          this.separator = params.separator;
        }

        if (params.default) {
          this.convert = function (current, row) {
            try {
              var return_val = current.slice(0, current.length - 1).filter(function (l) {
                return l != '' && l != null;
              }).join(this.separator);
            } catch (e) {
              return '';
            }

            if (return_val == '' && current[current.length - 1] != null && current[current.length - 1].length > 0) {
              return current[current.length - 1];
            }

            return return_val;
          }.bind(this);
        } else {
          this.convert = function (current, row) {
            try {
              return current.filter(function (l) {
                return l != '' && l != null;
              }).join(this.separator);
            } catch (e) {
              return '';
            }
          }.bind(this);
        }
      }
    };

    for (var dp in data_processing) {
      data_processing[dp].prototype = Object.create(BaseProcessAjaxData.prototype);
    }

    function PythonTable(html_id, tablesetup) {
      this.initsetup = tablesetup;
      this.filters = [];
      this.plugins = [];
      this.table_id = html_id;
      django_datatables.DataTables[html_id] = this;

      for (var i = 0; i < tablesetup.colOptions.length; i++) {
        if (tablesetup.colOptions[i]['render'] != undefined) {
          tablesetup.tableOptions.columnDefs[i].render = new django_datatables.column_render(i, tablesetup.colOptions[i]['render'], this);
        }
      }

      this.postInit = function () {
        this.table = $('#' + html_id).dataTable();
        this.table.api().on('stateSaveParams.dt', function (e, settings, data) {
          this.exec_filter('save_state', data);
        }.bind(this));

        if (typeof django_datatables.setup[html_id].filters !== 'undefined') {
          this.filters = django_datatables.setup[html_id].filters;
          django_datatables.setup[html_id].filters = [];
        }

        if (typeof django_datatables.setup[html_id].plugins !== 'undefined') {
          this.plugins = django_datatables.setup[html_id].plugins;
          django_datatables.setup[html_id].plugins = [];
        }

        this.exec_filter('init', this);
        this.init_filters();
        this.exec_filter('html');
        var state_data = this.table.api().state.loaded();
        this.exec_plugins('init', this, state_data);
        this.table.api().on('search', function () {
          this.exec_filter('reset');
        }.bind(this));
        this.table.api().on('draw', function () {
          this.proc_filters(this);
          this.exec_filter('refresh');
          this.exec_plugins('refresh', this);
        }.bind(this));
        this.exec_filter('reset');
        this.table.api().draw();
      }.bind(this);

      var dataTable_setup = {
        /*  stripeClasses:['a', 'a'], */
        orderCellsTop: true,
        pageLength: 25,
        fixedHeader: true,
        orderClasses: false,
        stateSave: true,
        deferRender: true,
        dom: 'rtip',
        initComplete: this.postInit
      };

      if (tablesetup.tableOptions.data === undefined) {
        var csrf = ajax_helpers.getCookie('csrftoken');
        var url;

        if (tablesetup.tableOptions.ajax_url !== undefined) {
          url = tablesetup.tableOptions.ajax_url;
        } else {
          url = window.location.search;
        }

        dataTable_setup.ajax = {
          'url': url,
          "type": "POST",
          "data": {
            "csrfmiddlewaretoken": csrf,
            table_id: html_id,
            datatable_data: true
          }
        };
      }

      if (tablesetup.tableOptions.column_id !== undefined && tablesetup.tableOptions.column_id != null) {
        dataTable_setup.rowId = function (row) {
          return 'i' + row[tablesetup.tableOptions.column_id];
        };
      }

      Object.assign(dataTable_setup, tablesetup.tableOptions);
      init_setup(html_id);

      if (django_datatables.setup[html_id].datatable_setup != undefined) {
        Object.assign(dataTable_setup, django_datatables.setup[html_id].datatable_setup);
      }

      if (typeof tablesetup.tableOptions.rowGroup != 'undefined') {
        dataTable_setup['rowGroup'] = {
          dataSrc: tablesetup.field_ids.indexOf(tablesetup.tableOptions.rowGroup.dataSrc),
          endRender: function endRender(rows, group) {
            var sums = Array(rows.data()[0].length).fill('');
            tablesetup.tableOptions.rowGroup.sumColumns.forEach(function (column) {
              var column_no = tablesetup.field_ids.indexOf(column);
              var sum = rows.data().pluck(column_no).reduce(function (a, b) {
                return a + parseFloat(b);
              }, 0);
              sums[column_no] = sum;
            });
            var sums_row = '';

            for (c = 0; c < sums.length; c++) {
              if (tablesetup.colOptions[c].hidden != true) {
                if (typeof sums[c] == 'number') {
                  sums_row += '<td class="dt-right">' + sums[c].toFixed(2) + '</td>';
                } else {
                  sums_row += '<td></td>';
                }
              }
            }

            return $('<tr>' + sums_row + '</tr>');
          },
          startClassName: 'table-info font-weight-bold',
          endClassName: 'font-weight-bold white text-right'
        };
      }

      $('#' + this.table_id).dataTable(dataTable_setup);

      if (this.initsetup.tableOptions.row_href) {
        $('#' + html_id + ' tbody').on('click', 'tr', function () {
          var p_table = django_datatables.DataTables[html_id];
          var row_id = $(this).attr('id');
          var row_data = p_table.table.api().row('#' + row_id).data();
          var href_render = new django_datatables.column_render(0, p_table.initsetup.tableOptions.row_href, p_table);
          window.location.href = href_render('', null, row_data);
        });
      }
    }

    PythonTable.prototype.exec_filter = function (function_name, data) {
      for (var i = 0; i < this.filters.length; i++) {
        if (function_name in this.filters[i]) {
          this.filters[i][function_name](data);
        }
      }
    };

    PythonTable.prototype.exec_plugins = function (function_name, data, extra_data) {
      for (var i = 0; i < this.plugins.length; i++) {
        if (function_name in this.plugins[i]) {
          this.plugins[i][function_name](data, extra_data);
        }
      }
    };

    PythonTable.prototype.init_filters = function () {
      this.table.api().rows().data().each(function (row) {
        this.filters.forEach(function (filter) {
          if (filter.filter_calcs != undefined) {
            filter.filter_calcs.init_calcs(row);
          }
        });
      }.bind(this));
    };

    PythonTable.prototype.proc_filters = function () {
      this.filters.forEach(function (filter) {
        if (filter.filter_calcs != undefined) {
          filter.filter_calcs.clear_calcs();
        }
      });
      this.table.api().rows({
        "filter": "applied"
      }).data().each(function (row) {
        this.filters.forEach(function (filter) {
          if (filter.filter_calcs != undefined) {
            filter.filter_calcs.add_calcs(row);
          }
        });
      }.bind(this));
    };

    PythonTable.prototype.find_column = function (id) {
      for (var j = 0; j < this.initsetup.tableOptions.columnDefs.length; j++) {
        if (this.initsetup.tableOptions.columnDefs[j]['name'] === id) {
          return j;
        }
      }
    };

    PythonTable.prototype.reset_table = function () {
      this.exec_filter('clear');
      this.exec_plugins('clear');

      if (this.initsetup.tableOptions.order !== undefined) {
        this.table.api().order(this.initsetup.tableOptions.order);
      } else {
        this.table.api().order([]);
      }

      for (var c = 0; c < this.initsetup.colOptions.length; c++) {
        this.table.api().column(c).visible(this.initsetup.colOptions[c].hidden != true);
      }

      this.table.api().draw();
    };

    PythonTable.prototype.send_row = function (command, row_id) {
      var row_data = this.table.api().row('#' + row_id).data();
      var data = {
        'row': command,
        'row_data': JSON.stringify(row_data),
        'row_no': row_id,
        table_id: this.table_id
      };
      ajax_helpers.post_json({
        data: data
      });
    };

    PythonTable.prototype.send_column = function (command, column) {
      var acc = this.table.api().column(this.find_column(column), {
        "filter": "applied"
      }).data().reduce(function (acc, current) {
        acc.push(current);
        return acc;
      }, []);
      var data = {
        column_data: JSON.stringify(acc),
        column: command,
        table_id: this.table_id
      };
      ajax_helpers.post_json({
        data: data
      });
    };

    return {
      BaseProcessAjaxData: BaseProcessAjaxData,
      data_processing: data_processing,
      setup: setup,
      add_filter: add_filter,
      add_plugin: add_plugin,
      DataTables: DataTables,
      FilterCalcs: FilterCalcs,
      FilterBase: FilterBase,
      PivotFilter: PivotFilter,
      column_render: column_render,
      utilities: utilities,
      add_to_setup: add_to_setup,
      b_r: b_r,
      PythonTable: PythonTable
    };
  }();
}

function rep_options(html, option_dict) {
  for (var o in option_dict) {
    var option = new RegExp('%' + o, 'g');
    html = html.replace(option, option_dict[o]);
  }

  return html;
}

$(document).ready(function () {
  $.fn.dataTable.moment("DD/MM/YYYY");
});