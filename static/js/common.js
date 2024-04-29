'use strict';

function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", Cookies.get('csrftoken'));
        }
    }
});

jQuery.postJSON = function(url, data) {
    return $.ajax({
        type: 'POST',
        url: url,
        dataType: 'json',
        data: {'json': JSON.stringify(data)}
    })
};

function datetimeFormat(datetime, timezone) {
    if (moment.isMoment(datetime))
        return datetime.format('YYYY-MM-DD HH:mm z');
    else
        return moment.tz(datetime, timezone).format('YYYY-MM-DD HH:mm z');
}

function datetimeSecFormat(datetime, timezone) {
    if (moment.isMoment(datetime))
        return datetime.format('YYYY-MM-DD HH:mm:ss z');
    else
        return moment.tz(datetime, timezone).format('YYYY-MM-DD HH:mm:ss z');
}
