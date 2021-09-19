django_datatables.data_processing.hhmm = function (column, params, table) {
    django_datatables.BaseProcessAjaxData.call(this, column, params, table)
    this.convert = function (current, value) {
        value = this.determine_value(value)
        const divmod = (x, y) => [Math.floor(x / y), x % y];
        var total_seconds = value ? value : 0
        if (total_seconds === 0) {
            return ''
        }
        var sign = ""
        if (total_seconds < 0) {
            sign = '-'
        }
        total_seconds = Math.abs(total_seconds)
        var result = divmod(total_seconds, 60)
        //var seconds = result[1]
        result = divmod(result[0], 60)

        var mins = result[1]
        if (mins < 10) {
            mins += '0'
        }
        return sign + result[0] + ':' + mins
    }.bind(this)
}
django_datatables.data_processing.hhmm.prototype = Object.create(django_datatables.BaseProcessAjaxData.prototype);
