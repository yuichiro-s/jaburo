function toks_to_spans(toks) {
    var _this = this;
    var t_div = $('<div>');
    for (var _i = 0, toks_1 = toks; _i < toks_1.length; _i++) {
        var tok_d = toks_1[_i];
        var tok = tok_d["tok"];
        var tag = tok_d["tag"];
        var lm = tok_d["lm"];
        var color = tok_d["color"];
        var lm_score = lm["prob"];
        var t_span = $('<span>');
        t_span.append(' ');
        var a = $('<a class="token" data-toggle="popover" data-placement="bottom">');
        t_span.append(a);
        // popover
        var alternative_div = $('<div>');
        var alternative_table = $('<table class="table table-striped">');
        alternative_table.append($('<thead><tr><th>word</th><th>prob.</th></tr></thead>'));
        var alternative_table_body = $('<tbody>');
        alternative_table.append(alternative_table_body);
        alternative_div.append(alternative_table);
        var ok = false;
        var tok_lower = tok.toLowerCase();
        for (var _a = 0, _b = lm["top"]; _a < _b.length; _a++) {
            var w_p = _b[_a];
            var w = w_p["w"];
            var p = w_p["p"].toString().substring(0, 5);
            var tr = $('<tr>');
            var td1 = $('<td>').text(w);
            var td2 = $('<td>').text(p);
            if (lm_score === w_p.p) {
                ok = true;
                td1.css('font-weight', 'bold');
                td2.css('font-weight', 'bold');
                if (w !== '<UNK>') {
                    a.css('font-weight', 'bold');
                }
            }
            tr.append(td1);
            tr.append(td2);
            alternative_table_body.append(tr);
        }
        if (!ok) {
            var w = tok_lower;
            var p = lm_score.toString().substring(0, 5);
            var tr = $('<tr>');
            var td1 = $('<td>').text(w);
            var td2 = $('<td>').text(p);
            td1.css('font-weight', 'bold');
            td2.css('font-weight', 'bold');
            tr.append(td1);
            tr.append(td2);
            alternative_table_body.append(tr);
        }
        a.popover({
            content: alternative_div.html(),
            html: true
        }).click(function () {
            $(_this).popover('show');
        });
        a.css('color', 'black');
        a.css('background-color', color);
        a.text(tok);
        t_div.append(t_span);
    }
    return t_div;
}
function analyze_text() {
    var section_str = $("#section-title-text").val();
    var text_str = $("#section-textarea").val();
    $.get("/acl_search/analyze", { 'section': section_str, 'text': text_str }, function (obj) {
        var section_div = $("#analysis-panel-title");
        section_div.empty();
        section_div.append(toks_to_spans(obj["section"]));
        var text_div = $("#analysis-panel-body");
        text_div.empty();
        for (var _i = 0, _a = obj["text"]; _i < _a.length; _i++) {
            var sen_obj = _a[_i];
            var sen_div = toks_to_spans(sen_obj);
            sen_div.addClass('well');
            sen_div.css('padding', '5px');
            sen_div.css('margin-bottom', '0px');
            var query = $.map(sen_obj, function (o) { return o.tok; }).join(' ');
            var search_button = $('<button type="button" class="btn btn-sm"><i class="glyphicon glyphicon-search"></i></button>');
            search_button.css('margin-bottom', '10px');
            search_button.click(function () {
                var win = window.open('/acl_search/?mode=full-text&like=True&query=' + query, '_blank');
            });
            var sen_div_wrapper = $('<div class="row">');
            text_div.append(sen_div_wrapper);
            sen_div_wrapper.append(sen_div);
            sen_div_wrapper.append(search_button);
            sen_div_wrapper.append($('<div>'));
        }
    });
}
$(function () {
    // analyze-as-you-type
    var timeout_id = null;
    var f = function () {
        clearTimeout(timeout_id);
        timeout_id = setTimeout(analyze_text, 300);
    };
    $("#section-title-text").keyup(f);
    $("#section-textarea").keyup(f);
    $("#search-phrase-button").click(function () {
        var text = $("#section-textarea").selection();
        var win = window.open('/acl_search/?query=' + text + '&mode=phrase&like=True', '_blank');
    });
});
//# sourceMappingURL=analyze_text.js.map