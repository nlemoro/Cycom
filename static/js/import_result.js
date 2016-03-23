function escapeRegExp(string) {
    return string.replace(/([.*+?^=!:${}()|\[\]\/\\])/g, "\\$1");
}

function replaceAll(string, find, replace) {
    return string.replace(new RegExp(escapeRegExp(find), 'g'), replace);
}

$(document).ready(function () {

    var patterns = {};
    var patternsName = $('.patternName');
    var patternsList = $('.patternList');
    for (var i in patternsName) {
        patterns[$(patternsName[i]).text()] = replaceAll($(patternsList[i]).text(), "'", "\"");
    }

    function getPatternList(name) {
        if (patterns.hasOwnProperty(name)) {
            return patterns[name];
        }
        return null;
    }

    function getSelectFromPatternList(patternList, id) {
        var select = "<select class=\"form-control\" id=\"" + id + "\" name=\"" + id + "\">";

        patternList = JSON.parse(patternList);
        for (var i in patternList) {
            if (patternList[i].toLowerCase().includes("cl")) {
                select += "<option selected>"
            } else {
                select += "<option>"
            }
            select += patternList[i]
            select += "</option>"
        }
        select += "</select>"
        return select;
    }

    function getFirstCaseFromCol(columnIndex) {
        return $('table tr').find('td:eq(' + columnIndex + ')')[0]
    }

    function hideOptionFromSelects(string) {
        if (string != "Non reconnu") {
            $('.menu-select').each(function () {
                $(this).children().each(function () {
                    if ($.trim($(this).text()) == string) {
                        $(this).hide();
                    }
                });
            });
        }
    }

    function showOptionFromSelects(string) {
        if (string != "Non reconnu") {
            $('.menu-select').each(function () {
                $(this).children().each(function () {
                    if ($.trim($(this).text()) == string) {
                        $(this).show();
                    }
                });
            });
        }
    }

    function changeColumnColor(index, color) {
        $('table tr').find('td:eq(' + index + ')').css("background-color", color);
    }

    var previous;

    $('.menu-select').on('focus', function () {
        previous = this.value;
    }).change(function () {
        var columnIndex = $(this).parent().index();
        var firstCase = getFirstCaseFromCol(columnIndex);
        $(firstCase).html("-");
        if ($.trim(previous) == "") {
            changeColumnColor(columnIndex, "#fff");
        }
        hideOptionFromSelects($.trim($(this).val()));
        showOptionFromSelects($.trim(previous));

        var name = $(this).val().toLowerCase();
        var patternList = getPatternList($(this).val().toLowerCase());
        if (patternList) {
            fillPatternCol(name, patternList);
        }
        $(this).blur();
    });

    $('#clear_select').click(function () {
        $('.cancel_import').each(function () {
            $(this).click();
        });
    });

    $('.cancel_import').click(function () {
        var select = $(this).parent().children(':first-child');
        showOptionFromSelects(select.val());
        select.val("");
        var columnIndex = $(this).parent().index();
        changeColumnColor(columnIndex, "#eee");
        var firstCase = getFirstCaseFromCol(columnIndex);
        $(firstCase).html("-");
    });

    function initSelectValue() {

        var i;
        var current = 0;
        var currentSelect;

        var matched_cols_list = $('#matched_cols_list').children();
        $('.menu-select').each(function () {
            i = 0;
            currentSelect = $(this);
            currentSelect.children().each(function () {
                if (i == current) {
                    var matched_val = matched_cols_list[i].text;
                    if (matched_val != "Non reconnu") {
                        hideOptionFromSelects($.trim(matched_val));
                        currentSelect.val($.trim(matched_val));

                        var name = matched_val.toLowerCase();
                        var patternList = getPatternList(name);
                        if (patternList) {
                            fillPatternCol(name, patternList);
                        }
                        $(this).blur();
                    }
                    else {
                        currentSelect.val("");
                        var columnIndex = currentSelect.parent().index();
                        changeColumnColor(columnIndex, "#eee");
                        var firstCase = getFirstCaseFromCol(columnIndex);
                        $(firstCase).html("-");
                    }
                }
                ++i;
            });
            ++current;
        });
    }

    $('form').submit(function (event) {
        var obj = [];
        var nbCols = 0;
        var valueV;

        event.preventDefault();
        $(".menu-select").each(function () {
            valueV = $(this).val() ? $(this).val() : "";
            obj.push(valueV);
            //nbCols += 1;
        });
//        i = 0;
//        $("td").each(function() {
//            obj.push({category: obj[i].category, value: $.trim($(this).text())});
//            i += 1;
//            if (i == nbCols)
//                i = 0;
//        });
        if ($("#format").size() != 0) {
            $("#format").hide();
            $(this).append($("#format"));
        }
        string = JSON.stringify(obj);
        $('#tableToSend').val(string);
        $.ajax({
            url: "/cycom/validation",
            data: $(this).serialize(),
        });
        alert("L'import peut prendre quelques minutes, vous pouvez continuer la navigation");
        $('#submit_link')[0].click();
    });

    function fillPatternCol(name, patternList) {
        var val;

        $('th').each(function () {
            val = $($(this).children()[0]).val();
            if (val && val.toLowerCase() == name) {
                $(getFirstCaseFromCol($(this).index())).html(getSelectFromPatternList(patternList, name));
            }
        });
    }

    initSelectValue();

    for (var i in patterns) {
        if (patterns[i].length) {
            fillPatternCol(i, patterns[i]);
        }
    }

});