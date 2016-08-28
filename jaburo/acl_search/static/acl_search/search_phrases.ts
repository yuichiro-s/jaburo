declare var $;

function show_examples(data) {
    var pl = $("#paper-list");
    pl.empty();  // clear results

    var total_hits = data["total"];
    $("#total-hits").text(total_hits + " hits");
    
    var hits = data["hits"];
    if (hits.length === 0) {
        pl.append("<p>No example found.</p>");
    } else {
        for (var d of hits) {
            var count = d["count"];
            var paper_panel = $('<div class="panel panel-default"></div>');

            // show paper info
            var paper_title = d["title"];
            var authors = d["authors"];
            var year = d["year"];
            var conference = d["conference"];
            var url = d["url"];
            var paper_panel_heading = $(
                '<div class="panel-heading"><h4 class="panel-title">' +
                '<a href="' + url + '" target="_blank">' + paper_title +
                '</a> ' +
                '<span class="badge">' + count + '</span></h4>' +
                '<p>[' + conference + ' ' + year + '] ' + authors.join(', ') + '</p>' +
                '</div>');
            paper_panel.append(paper_panel_heading);

            // show sections
            var paper_panel_collapse = $('<div class="panel-collapse collapse in"></div>');
            paper_panel.append(paper_panel_collapse);
            var sections_ul = $('<ul class="list-group"></ul>');
            paper_panel_collapse.append(sections_ul);
            for (var section of d["sections"]) {
                // show section
                var section_li = $('<li class="list-group-item"></li>');
                sections_ul.append(section_li);

                var num = section["num"];
                var section_title = section["section"];
                if (num !== "") {
                    section_title = num + " " + section_title;
                }
                section_li.append($("<a>" + section_title + "</a>"));

                // show examples
                var sens_ul = $('<ul class="list-group"></ul>');
                section_li.append(sens_ul);
                for (var sen of section["sens"]) {
                    sens_ul.append('<li class="list-group-item">' + sen + '</li>');
                }
            }
            pl.append(paper_panel);
        }
    }
}

function show_phrases(data) {
    var pl = $("#phrase-list");
    var hits = data["hits"];
    if (hits.length === 0) {
        pl.append("<p>No phrase found.</p>");
    } else {
        for (var d of hits) {
            var phrase = d["phrase"];
            var score = d["score"];
            var tags = d["tags"];
            var freq = d["freq"];
            var node = $('<a href="#" class="list-group-item"><span class="candidate-phrase">' + phrase + '</span> <span class="badge">' + freq + '</span></a>');
            pl.append(node)
        }
    }
}

function get_sections() {
    var arr = [];
    $("button.section-btn").each((index, element) => {
        var e = $(element);
        if (e.hasClass("active")) {
            arr.push(e.text());
        }
    });
    return arr.join(" ");
}

function search_phrases() {
    var search_phrases_url = $("#search-phrases-url").attr("value");
    $("#phrase-list").empty();
    $("#paper-list").empty();
    var query = $("#phrase-search-input").val();
    $.get(search_phrases_url, {
        'q': query,
        'like': $("#similar-button").hasClass('active'),
    }, show_phrases);
}

function search_phrase_occurrences() {
    var query = $("#phrase-list > a.active").find(".candidate-phrase").text();
    var search_examples_url = $("#search-examples-url").attr("value");
    $.get(search_examples_url,
        {
            'q': query,
            'like': $("#similar-button").hasClass('active'),
            'sections': get_sections(),
        },
        show_examples);
}

function search_full_text() {
    var query = $("#phrase-search-input").val();
    var search_examples_url = $("#search-examples-url").attr("value");
    $("#phrase-list").empty();
    var like = $("#similar-button").hasClass('active');

    $.get(search_examples_url,
        {
            'q': query,
            'like': like,
            'prefix': 'True',
            'slop': 3,
            'sections': get_sections(),
        },
        show_examples);
}

function do_search() {
    if ($("#search-mode-phrase").hasClass('active')) {
        // phrase search
        search_phrases();
    } else {
        // full-text search
        search_full_text();
    }
}

$(() => {
    // search-as-you-type
    var timeout_id = null;
    $("#phrase-search-input").keyup(
        () => {
            clearTimeout(timeout_id);
            timeout_id = setTimeout(() => {
                if ($("#search-mode-phrase").hasClass('active')) {
                    // phrase search
                    search_phrases();
                } else {
                    // full-text search
                    search_full_text();
                }
            }, 300);
        }
    );
    
    // click phrase
    $(document).on("click", "#phrase-list a",
        (evt) => {
            $("#phrase-list").find("a").removeClass("active");
            $(evt.currentTarget).addClass("active");
            search_phrase_occurrences();
            return false;
        }
    );

    var update_results = () => {
        if ($("#search-mode-phrase").hasClass('active') && $("#phrase-list a.active").length > 0) {
            search_phrase_occurrences();
        } else {
            search_full_text();
        }
    };
    $(document).on("click", ".section-btn", (evt) => {
        $("#all-sections-button").removeClass("active");
        var btn = $(evt.currentTarget);
        if (btn.hasClass("active")) {
            btn.removeClass("active");
            if ($(".section-btn.active").length === 0) {
                // all disabled
                $("#all-sections-button").addClass("active");
            }
        } else {
            btn.addClass("active");
        }
        update_results();
        return true;
    });
    $(document).on("click", "#all-sections-button", (evt) => {
        $(".section-btn").removeClass("active");
        $(evt.currentTarget).addClass("active");
        update_results();
        return true;
    });

    $(document).on("click", "#search-mode-phrase", search_phrases);
    $(document).on("click", "#search-mode-full-text", search_full_text);
    //$(document).on("click", "#similar-checkbox", () => { do_search(); return true; });

    var init_query = $("#init-query").attr('value');
    var init_mode = $("#init-mode").attr('value');
    var init_like = $("#init-like").attr('value');
    
    $('#phrase-search-input').val(init_query);
    /*
    if (init_mode === 'phrase') {
        $('search-mode-phrase-radio').prop('checked');
    } else if (init_mode === 'full-text') {
        $('search-mode-full-text-radio').prop('checked');
    }
    if (init_like !== 'None') {
        $('similar-checkbox').prop('checked');
    }
    */

    do_search();
});

