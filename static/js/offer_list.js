function convertDate(inputFormat) {
    function pad(s) {
        return (s < 10) ? '0' + s : s;
    }

    var d = new Date(inputFormat);
    var dt1 = [pad(d.getDate()), pad(d.getMonth() + 1), d.getFullYear()].join('/');
    var dt2 = [pad(d.getHours()), pad(d.getMinutes()), pad(d.getSeconds())].join(':');

    return dt1 + " " + dt2;
}

function loadTab(page, tab_name) {
    var table = $('#loadedfiles');
    var pager = $('.pagination');
    table.empty();
    pager.empty();

    $.ajax({
            url: '/cycom/load-offer-list-tab/',
            type: 'POST',
            dataType: 'HTML',
            data: "page=" + page + "&tab_name=" + tab_name,
            success: function (response, status) {
                response = jQuery.parseJSON(response);
                if (response != null) {
                    response.offers.forEach(function (offer) {
                        if (!offer.is_deleting) {
                            var state = 100 * offer.line_ok / (offer.line_ko + offer.line_ok);
                            var input_checked = (offer.is_active ? "" : "checked");
                            var tr_class = (offer.is_active ? "" : "danger");
                            var tr_style = "";
                            var line = '<tr style="' + tr_style + '" class="' + tr_class + '"><td style="text-align: center;"><img class="loader ' + (offer.is_loaded ? "hidden" : "") + '" src="/static/img/spin_loader.GIF" />';
                            line += '<img class="tick ' + ((!offer.is_to_process && offer.is_loaded) ? "" : "hidden") + '" src="/static/img/tick.png" />';
                            line += '<button class="btn btn-default btn-sm publish ' + ((offer.is_to_process && offer.is_loaded) ? "" : "hidden") + '" type="button" data-toggle="modal" data-target="#publish-offer-modal">publier</button>';
                            line += "</td>";
                            line += '<td><div style="text-align: center;">';
                            if (offer.is_producer == true)
                                line += "<span class='glyphicon glyphicon-tower' style='margin: 7px; color: #414043;'></span>";
                            line += '</div></td>';

                            line += '<td><div style="text-align: center;">';
                            if (offer.is_spot == true)
                                line += "<span class='glyphicon glyphicon-time' style='margin: 7px; color: #e24c1e;'></span>";
                            line += '</div></td>';

                            line += '<td>' + convertDate(offer.offer_date) + '</td>';

                            line += '<td class="endOfferDate">';
                            if (offer.is_spot == true)
                                line += convertDate(offer.spot_date);
                            else if (offer.disable_date != null && offer.disable_date != "") {
                                line += convertDate(offer.disable_date);
                            }
                            line += '</td>';

                            line += '<td class="partner">' + offer.partner + '</td>';

                            line += '<td><a href="/cycom/file/' + offer.file_id + '/' + offer.file_name + '">' + offer.file_name + '</a></td>';
                            if (offer.line_ok == 0) {
                                line += '<td><span class="ok_line">0</span></td>';
                            } else {
                                line += '<td><span class="ok_line"><a href="/cycom/ok-line-list/' + offer.id + '">' + offer.line_ok + '</a></span></td>';
                            }
                            if (offer.line_ko == 0)
                                line += '<td><span class="ko_line">0</span></td>';
                            else
                                line += '<td><span class="ko_line"><a href="/cycom/ko-line-list/' + offer.id + '">' + offer.line_ko + '</a></span></td>';
                            if (offer.best_price == 0)
                                line += '<td><span class="best_price">0</span></td>';
                            else
                                line += '<td><span class="best_price"><a href="/cycom/best-price-list/' + offer.id + '">' + offer.best_price + '</a></span></td>';

                            line += '<td class="state_bar"><div class="progress" style="margin-bottom:0px;">';
                            line += '   <div class="progress-bar progress-bar-' + (state == 100 ? 'success' : 'warning') + '" role="progressbar" style="width: ' + state + '%">';
                            line += '     <span class="sr-only">' + state + '% Complete</span>';
                            line += '   </div></div></td>';
                            line += '<td style="text-align: center;"><input class="offer_status" type="checkbox" ' + input_checked + '/></td>';
                            line += '<td style="text-align: center;"><img class="loader ' + (offer.is_loaded ? "hidden" : "") + '" src="/static/img/spin_loader.GIF" />';
                            line += '<button type="button" class="btn btn-sm btn-danger remove-offer ' + (offer.is_loaded ? '' : 'hidden') + '" data-toggle="modal" data-target="#remove-offer-modal"><span class="glyphicon glyphicon-trash" aria-hidden="true"></span></button></td>';
                            line += '<td class="offer_id hidden">' + offer.id + '</td>';

                            table.append(line);
                        }
                    });
                    var pagination_html = '';
                    for (var i = 1; i <= response.page_count; i++) {
                        pagination_html += '<li' + (i == page ? ' class="active"' : '') + '><a class="page-button" href="#">' + i + '</a></li>'
                    }
                    pager.html(pagination_html);
                }

                var interval = setInterval(checkLoadedOffers, 2000);

                function checkLoadedOffers() {
                    var checked = false;
                    $('#loadedfiles tr').each(function () {
                        $this = $(this);
                        offer_id = $this.find(".offer_id").html().toString();
                        if ($this.find(".loader").attr("class").indexOf("hidden") < 0) {
                            checked = true;
                            $.ajax({
                                url: '/cycom/offer-loaded/',
                                type: 'POST',
                                dataType: 'HTML',
                                data: "offer_id=" + offer_id,
                                success: function (response, status) {
                                    response = jQuery.parseJSON(response);
                                    var content = response.content;
                                    var offer = jQuery.parseJSON(content.offer);
                                    if (response.status == "OK" && offer.IsLoaded) {
                                        $('.offer_id').each(function () {
                                            var $this = $(this);
                                            if ($this.html() == content.offerId) {
                                                var parent = $this.parent();
                                                parent.find(".loader").addClass("hidden");
                                                if (!offer.IsToProcess) {
                                                    parent.find(".tick").removeClass("hidden");
                                                } else {
                                                    parent.find(".publish").removeClass("hidden");
                                                }
                                                parent.find(".remove-offer").removeClass("hidden");
                                                parent.find(".ok_line").html('<span class="ok_line"><a href="/cycom/ok-line-list/' + content.offerId + '">' + offer.LineOK + '</a></span>');
                                                parent.find(".ko_line").html('<span class="ko_line"><a href="/cycom/ko-line-list/' + content.offerId + '">' + offer.LineKO + '</a></span>');
                                                var state = 100 * offer.LineOK / (offer.LineKO + offer.LineOK);
                                                var progress = '<div class="progress" style="margin-bottom:0px;">';
                                                progress += '<div class="progress-bar progress-bar-' + (state == 100 ? 'success' : 'warning') + '" role="progressbar" style="width: ' + state + '%">';
                                                progress += '<span class="sr-only">' + state + '% Complete</span>';
                                                progress += '</div></div>'
                                                parent.find(".state_bar").html(progress);
                                            }
                                        });
                                    } else if (response.status == "ERROR") {
                                        console.log(response);
                                    }
                                },
                                error: function (response, status, error) {
                                    console.log(response);
                                }
                            });
                        }
                    });
                    if (!checked) {
                        clearInterval(interval);
                    }
                }
            },
            error: function (response, status, error) {
                console.log("Error func of ajax call: response = " + response);
            }
        }
    );
}

$(document).ready(function () {
    var company = $('#company').text();
    var $body = $("body");

    $('#nav-tabs a').click(function () {
        loadTab(1, $(this).attr('name'));
    });
    $('#nav-tabs a[name="to_process"]').click();

    $body.on("click", ".page-button", function () {
        loadTab($(this).text(), $("#nav-tabs li[class='active'] a").attr('name'));
    });

    var offerToHide = null;
    $body.on("click", ".remove-offer", function () {
        $('#remove-offer-id').text($(this).parent().parent().find(".offer_id").text());
        offerToHide = $(this).parent().parent();
    });

    $('#confirm-remove-offer').click(function () {
        var id = $('#remove-offer-id').text();
        $.ajax({
            url: '/cycom/offer-status/',
            type: 'POST',
            dataType: 'HTML',
            data: "table=" + JSON.stringify({
                "offer_id": id,
                "offer_status": false
            }),
            success: function (response, status) {
            },
            error: function (response, status, error) {
                console.log(response);
            }
        });
        $.ajax({
            url: '/cycom/update-best-price/' + id,
            type: 'GET',
            dataType: 'HTML',
            success: function (response, status) {
            },
            error: function (response, status, error) {
                console.log(response);
            }
        });
        $.ajax({
            url: '/cycom/remove-offer/' + id,
            type: 'GET',
            dataType: 'HTML',
            success: function (response, status) {
            },
            error: function (response, status, error) {
                console.log(response);
            }
        });
        $('.close-modal').click();
        $(offerToHide).fadeOut("normal", function () {
            $(this).remove();
        });
    });

    var offerToPublish = null;
    $body.on("click", ".publish", function () {
        $("#publish-offer-id").text($(this).parent().parent().find(".offer_id").text());
        offerToPublish = $(this).parent().parent();
        $("#publish-offer-modal table tbody tr").remove();
        $.ajax({
            url: "/cycom/offers-from-partner/" + offerToPublish.find(".partner").text(),
            type: "GET",
            success: function(response) {
                response = jQuery.parseJSON(response).content;
                var line = "<tr>";
                for (i in response) {
//                    console.log(response[i]);
                    line += '<td><div style="text-align: center;">' + (response[i].is_producer ? "<span class='glyphicon glyphicon-tower' style='margin: 7px; color: #414043;'></span>" : "") + "</div></td>";
                    line += '<td><div style="text-align: center;">' + (response[i].is_spot ? "<span class='glyphicon glyphicon-time' style='margin: 7px; color: #e24c1e;'></span>" : "") + "</div></td>";
                    line += '<td>' + convertDate(response[i].offer_date) + '</td>';
                    line += '<td>' + convertDate(response[i].spot_date) + '</td>';
                    line += '<td>' + (response[i].is_new_price ? 'pas de fichier associé' : '<a href="/cycom/file/' + response[i].file_id + '/' + response[i].file_name + '">' + response[i].file_name + '</a>') + '</td>';
                }
                line += "</tr>";
                if (response.length > 0)
                    $("#publish-offer-modal table tbody").append(line);
            }
        })
    });

    $('#confirm-publish-offer').click(function () {
        var id = $("#publish-offer-id").text();
        $.ajax({
            url: '/cycom/publish-offer/' + id,
            type: 'GET',
            dataType: 'HTML',
            success: function (response, status) {
            },
            error: function (response, status, error) {
                console.log(response);
            }
        });
//        $.ajax({
//            url: '/bigwine/update-best-price/' + id,
//            type: 'GET',
//            dataType: 'HTML',
//            success: function (response, status) {
//            },
//            error: function (response, status, error) {
//                console.log(response);
//            }
//        });
        $('.close-modal').click();
        $(offerToPublish).find('.tick').removeClass("hidden");
        $(offerToPublish).find('.publish').remove();
        $(offerToPublish).removeClass("danger");
        $(offerToPublish).fadeOut();
    });

    $body.on("change", '.offer_status', function () {
        $this = $(this);
        if ($this.is(":checked")) {
            data = {
                "offer_id": $this.parent().parent().find(".offer_id").html(),
                "offer_status": false
            };
            $this.parent().parent().addClass("danger");
            var d = new Date();
            var dString = d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2) + " " + ("0" + d.getHours()).slice(-2);
            dString += ":" + ("0" + d.getMinutes()).slice(-2) + ":" + ("0" + d.getSeconds()).slice(-2);
            $this.parent().parent().find(".endOfferDate").text(dString);
        } else {
            data = {
                "offer_id": $this.parent().parent().find(".offer_id").html(),
                "offer_status": true
            };
            $this.parent().parent().removeClass("danger");
            $this.parent().parent().find(".endOfferDate").html("");
        }
        $.ajax({
            url: '/cycom/offer-status/',
            type: 'POST',
            dataType: 'HTML',
            data: "table=" + JSON.stringify(data),
            success: function (response, status) {
            },
            error: function (response, status, error) {
                console.log(response);
            }
        });
        $.ajax({
            url: '/cycom/update-best-price/' + data['offer_id'],
            type: 'GET',
            dataType: 'HTML',
            success: function (response, status) {
            },
            error: function (response, status, error) {
                console.log(response);
            }
        });
    });
});
