
// Support TLS-specific URLs, when appropriate.
if (window.location.protocol == "https:") {
    var ws_scheme = "wss://";
} else {
    var ws_scheme = "ws://"
};

var inbox = new ReconnectingWebSocket(ws_scheme + location.host + "/updates");

inbox.onmessage = function(message) {
    var data = JSON.parse(message.data);
    console.log(message.data);

    //$("#chat-text").append("<div class='panel panel-default'><div class='panel-heading'>" + $('<span/>').text(data.handle).html() + "</div><div class='panel-body'>" + $('<span/>').text(data.text).html() + "</div></div>");
    //$("#chat-text").stop().animate({
    //    scrollTop: $('#chat-text')[0].scrollHeight
    //}, 800);
};

inbox.onclose = function(){
    console.log('inbox closed');
    this.inbox = new WebSocket(inbox.url);

};
