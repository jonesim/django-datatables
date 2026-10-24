// The filter panel beside a table ({% filter_control %}): showing and hiding it, its saved state, the reset
// highlight, resizing (resizable_filter) and dragging filters to reorder them (sortable_filters). Loaded after
// filtered-datatable.js, which it adds django_datatables.filter_panel to; filter_control.html calls it once per panel
if (typeof django_datatables !== 'undefined' && !django_datatables.filter_panel) {
    (function (django_datatables) {

        // Shows or hides a panel, swapping it for its collapsed bar. Called from the panel's menu items
        // (DatatableTable.collapse_filter_menu_item and expand_filter_menu_item), so it is a global
        function show_hide_filter_block(table_id, show, save_state) {
            if (show) {
                $('#fb-c-' + table_id).addClass('fb-collapsed');
                $('#fb-' + table_id).removeClass('fb-collapsed');
            } else {
                $('#fb-' + table_id).addClass('fb-collapsed');
                $('#fb-c-' + table_id).removeClass('fb-collapsed');
            }
            if (save_state === true) {
                django_datatables.DataTables[table_id].table.api().state.save()
            }
        }

        // Fold or unfold every filter in a panel (DatatableTable.collapse_all / expand_all menu items)
        function collapse_all(table_id) {
            $("#" + table_id + "-filter-block .card-body").collapse('hide')
        }

        function show_all(table_id) {
            $("#" + table_id + "-filter-block .card-body").collapse('show')
        }

        window.show_hide_filter_block = show_hide_filter_block
        window.collapse_all = collapse_all
        window.show_all = show_all

    // The keys (data-filter-key, see DatatableFilter.order_key) of a panel's filters, in the order they are shown
    function filter_order(container) {
        return Array.prototype.map.call(container.querySelectorAll(':scope > .filter-block'), function (el) {
            return el.getAttribute('data-filter-key')
        })
    }

    // Shows a panel's filters in a saved order of keys. A filter the order doesn't name (added to the code since it
    // was saved) goes after the filter it follows in code; a key with no filter (removed since) is skipped
    function apply_filter_order(container, keys) {
        var blocks = Array.prototype.slice.call(container.querySelectorAll(':scope > .filter-block'))
        if (!blocks.length || !Array.isArray(keys)) {
            return
        }
        var by_key = {}
        blocks.forEach(function (el) {
            by_key[el.getAttribute('data-filter-key')] = el
        })
        var ordered = keys.filter(function (key) {
            return by_key[key]
        }).map(function (key) {
            return by_key[key]
        })
        blocks.forEach(function (el, i) {
            if (ordered.indexOf(el) === -1) {
                ordered.splice(i ? ordered.indexOf(blocks[i - 1]) + 1 : 0, 0, el)
            }
        })
        var anchor = document.createComment('')
        container.insertBefore(anchor, blocks[0])
        ordered.forEach(function (el) {
            container.insertBefore(el, anchor)
        })
        anchor.remove()
    }

    // The side panel's filters are reordered by dragging their title (table_options['sortable_filters']): never
    // from its icons, and only once the pointer has moved a few px, so a slightly missed click stays a click.
    // While a filter is dragged every filter is folded to its title, so the list is short enough to drop into;
    // each opens again as it was. Only the filter blocks move; each filter's <script> tags stay where they are.
    // on_change is called after a drop that changed the order
    function sortable_filters(container, on_change) {
        var press = null, block = null, gap = null, spacer = null, grab_y = 0, pointer_y = 0, scroller = null
        var frame = null, start_order = null

        container.classList.add('filter-sortable')

        var other_blocks = function () {
            return Array.prototype.filter.call(container.children, function (el) {
                return el.classList.contains('filter-block') && el !== block
            })
        }

        // the gap goes before the first block whose middle is below the pointer, else after the last block
        var place_gap = function () {
            var blocks = other_blocks()
            var before = null
            blocks.some(function (el) {
                var rect = el.getBoundingClientRect()
                if (pointer_y < rect.top + rect.height / 2) {
                    before = el
                    return true
                }
            })
            if (before) {
                if (gap.nextElementSibling !== before) {
                    container.insertBefore(gap, before)
                }
            } else if (blocks.length && blocks[blocks.length - 1].nextElementSibling !== gap) {
                container.insertBefore(gap, blocks[blocks.length - 1].nextSibling)
            }
        }

        // the scrolling box to move when the pointer nears its top or bottom edge (a sticky panel's body), or the window
        var find_scroller = function () {
            for (var el = container; el && el !== document.body; el = el.parentElement) {
                var overflow = getComputedStyle(el).overflowY
                if ((overflow === 'auto' || overflow === 'scroll') && el.scrollHeight > el.clientHeight) {
                    return el
                }
            }
            return null
        }

        var auto_scroll = function () {
            var top = 0, bottom = window.innerHeight
            if (scroller) {
                var rect = scroller.getBoundingClientRect()
                top = rect.top
                bottom = rect.bottom
            }
            var step = pointer_y < top + 40 ? -10 : (pointer_y > bottom - 40 ? 10 : 0)
            // a sticky panel doesn't move with the window, so scrolling the window would only move the table
            if (step && (scroller || !container.closest('.side-filter-sticky'))) {
                if (scroller) {
                    scroller.scrollTop += step
                } else {
                    window.scrollBy(0, step)
                }
                place_gap()
            }
            frame = requestAnimationFrame(auto_scroll)
        }

        var lift = function () {
            block = press.block
            start_order = filter_order(container)
            var title_top = block.getBoundingClientRect().top
            grab_y = press.y - title_top
            container.classList.add('filter-sorting-collapsed')
            var rect = block.getBoundingClientRect()
            gap = document.createElement('div')
            gap.className = 'filter-drag-gap'
            gap.style.height = rect.height + 'px'
            gap.style.margin = getComputedStyle(block).margin
            container.insertBefore(gap, block)
            // Folding the filters above this one moves its slot up, away from the pointer. Bring the slot back
            // under the pointer: scroll the window back up by that much where it can, and make up the rest with a
            // spacer above the filters. A sticky panel doesn't move with the window (scrolling it would only move
            // the table), and its folded list is too short to scroll, so it takes the spacer
            var shift = title_top - gap.getBoundingClientRect().top
            if (shift > 0 && !container.closest('.side-filter-sticky')) {
                window.scrollBy(0, -shift)
                shift = title_top - gap.getBoundingClientRect().top
            }
            if (shift > 0) {
                spacer = document.createElement('div')
                spacer.className = 'filter-drag-spacer'
                spacer.style.height = shift + 'px'
                container.insertBefore(spacer, container.querySelector(':scope > .filter-block, :scope > .filter-drag-gap'))
            }
            block.classList.add('filter-dragging')
            block.style.width = rect.width + 'px'
            block.style.left = rect.left + 'px'
            block.style.top = (press.y - grab_y) + 'px'
            document.body.classList.add('filter-sorting')
            scroller = find_scroller()
            frame = requestAnimationFrame(auto_scroll)
        }

        var move = function (e) {
            pointer_y = e.clientY
            if (!block) {
                if (Math.abs(e.clientX - press.x) < 5 && Math.abs(e.clientY - press.y) < 5) {
                    return
                }
                lift()
            }
            block.style.top = (e.clientY - grab_y) + 'px'
            place_gap()
        }

        var end = function () {
            document.removeEventListener('pointermove', move)
            document.removeEventListener('pointerup', end)
            document.removeEventListener('pointercancel', end)
            if (block) {
                cancelAnimationFrame(frame)
                container.insertBefore(block, gap)
                gap.remove()
                if (spacer) {
                    spacer.remove()
                }
                block.classList.remove('filter-dragging')
                block.style.width = block.style.left = block.style.top = ''
                container.classList.remove('filter-sorting-collapsed')
                document.body.classList.remove('filter-sorting')
                if (on_change && filter_order(container).join() !== start_order.join()) {
                    on_change()
                }
            }
            press = block = gap = spacer = start_order = null
        }

        container.addEventListener('pointerdown', function (e) {
            if (press) {
                return
            }
            var header = e.button === 0 && e.target.closest('.filter-header')
            if (!header || !container.contains(header) || e.target.closest('a, input, textarea, button, select, option')) {
                return
            }
            press = {x: e.clientX, y: e.clientY, block: header.closest('.filter-block')}
            pointer_y = e.clientY
            document.addEventListener('pointermove', move)
            document.addEventListener('pointerup', end)
            document.addEventListener('pointercancel', end)
        })
    }

        // The panel's width is a per-browser preference, kept apart from the table state (which resets each session).
        // Drag the bar right of the panel to resize it; double-click it, or drag well past the minimum, to hide the panel
        function resizable_panel(table_id, local_storage_key) {
            var panel = $('#fb-' + table_id);
            var handle = $('#fb-h-' + table_id);
            var storage_key = local_storage_key + '_filter_width';
            var min_width = 200, max_width = 520;

            function set_width(width) {
                width = Math.max(min_width, Math.min(max_width, Math.round(width)));
                panel[0].style.setProperty('--fb-width', width + 'px');
                return width;
            }

            function adjust_table() {
                var table = django_datatables.DataTables[table_id];
                if (table && table.table) {
                    var api = table.table.api();
                    api.columns.adjust();
                    if (api.fixedHeader) {
                        api.fixedHeader.adjust();
                    }
                }
            }

            try {
                var saved = parseInt(localStorage.getItem(storage_key));
                if (saved) {
                    set_width(saved);
                }
            } catch (e) {
            }

            handle.on('pointerdown', function (e) {
                if (e.button !== 0) {
                    return;
                }
                e.preventDefault();
                var start_x = e.pageX;
                var start_width = panel.outerWidth();
                var width = start_width;
                $('body').addClass('fb-resizing');
                $(document).on('pointermove.fb_resize', function (e) {
                    width = start_width + e.pageX - start_x;
                    set_width(width);
                }).on('pointerup.fb_resize pointercancel.fb_resize', function () {
                    $(document).off('.fb_resize');
                    $('body').removeClass('fb-resizing');
                    if (width < min_width - 60) {
                        // dragged well past the minimum: hide the panel, and keep the width it had before
                        set_width(start_width);
                        show_hide_filter_block(table_id, false, true);
                    } else {
                        try {
                            localStorage.setItem(storage_key, set_width(width));
                        } catch (e) {
                        }
                    }
                    adjust_table();
                });
            }).on('dblclick', function () {
                show_hide_filter_block(table_id, false, true);
            });
        }

        // Sets up one panel. options (from filter_control.html): local_storage_key (DatatableTable.local_storage_key),
        // hidden_side_bar (whether the panel starts hidden when nothing is saved), resizable, sortable
        function filter_panel(table_id, options) {
            var container = document.getElementById(table_id + '-filter-block')

            // open or hidden as the browser last left it, else as the table's options say
            var saved = null
            try {
                saved = JSON.parse(localStorage.getItem(options.local_storage_key))
            } catch (e) {
            }
            show_hide_filter_block(table_id, saved != null ? !saved.hidden_side_bar : !options.hidden_side_bar)

            if (options.sortable) {
                sortable_filters(container, function () {
                    django_datatables.DataTables[table_id].table.api().state.save()
                })
            }

            // A filter order the user dragged is kept in the table state as the filters' keys (filter_order). The order
            // they are added in code is the default, and Reset Table returns to it
            var code_order = options.sortable ? filter_order(container) : null

            django_datatables.add_filter(table_id, {
                init: function (table) {
                    this.pTable = table
                    var loaded = table.table.api().state.loaded()
                    if (options.sortable && loaded && loaded.filter_order) {
                        apply_filter_order(container, loaded.filter_order)
                    }
                },
                clear: function () {
                    if (options.sortable) {
                        apply_filter_order(container, code_order)
                    }
                },
                filter: function () {
                    return true
                },
                save_state: function (data) {
                    data.hidden_side_bar = $('#fb-' + table_id).hasClass('fb-collapsed')
                    // which way the pivot ticks were made, so a page opened in the other mode can move them over
                    data.filter_mode = this.pTable.filter_mode()
                    // only an order that differs from the code's is saved, so a later change to the code's order
                    // still reaches everyone who hasn't moved their filters
                    if (options.sortable) {
                        var order = filter_order(container)
                        if (order.join() !== code_order.join()) {
                            data.filter_order = order
                        }
                    }
                },
                load_state: function (state_data) {
                    show_hide_filter_block(table_id, !state_data.hidden_side_bar)
                    if (options.sortable) {
                        apply_filter_order(container, state_data.filter_order || code_order)
                    }
                }
            })

            // the reset button turns amber while a search or filter hides any rows
            django_datatables.add_plugin(table_id, {
                refresh: function (table) {
                    var page_info = table.table.api().page.info()
                    $('.' + table_id + '-reset-button').toggleClass('text-warning', page_info.recordsTotal !== page_info.recordsDisplay)
                }
            })

            if (options.resizable) {
                resizable_panel(table_id, options.local_storage_key)
            }
        }

        django_datatables.filter_panel = filter_panel
        django_datatables.filter_order = filter_order
        django_datatables.apply_filter_order = apply_filter_order
    })(django_datatables)
}
