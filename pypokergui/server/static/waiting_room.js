$(document).ready(function() {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function() {};

    $("#registration_form").on("submit", function() {
        registerPlayer($(this));
        return false;
    });
    $("#start_game_form").on("submit", function() {
        startGame()
        return false;
    });
    //$("#message").select();
    updater.start();
});

function registerPlayer(form) {
    var message = form.formToDict();
    message['type'] = "action_new_member"
    message['name'] = message['body']
    delete message.body
    updater.socket.send(JSON.stringify(message));
}

function startGame() {
    message = {}
    message['type'] = "action_start_game"
    updater.socket.send(JSON.stringify(message));
}

function declareAction(form) {
  var message = form.formToDict();
  message['type'] = "action_declare_action"
  updater.socket.send(JSON.stringify(message))
}

jQuery.fn.formToDict = function() {
    var fields = this.serializeArray();
    var json = {}
    for (var i = 0; i < fields.length; i++) {
        json[fields[i].name] = fields[i].value;
    }
    if (json.next) delete json.next;
    return json;
};

var updater = {
    socket: null,

    start: function() {
        var url = "ws://" + location.host + "/pokersocket";
        updater.socket = new WebSocket(url);
        updater.socket.onmessage = function(event) {
            window.console.log(event.data)
            message = JSON.parse(event.data)
            if ('config_update' == message['message_type']) {
              updater.updateConfig(message)
            } else if ('start_game' == message['message_type']) {
              updater.startGame(message)
            } else if ('update_game' == message['message_type']) {
              updater.updateGame(message)
            } else {
              window.console.error(message)
            }
        }
    },

    updateConfig: function(message) {
        var node = $(message.html);
        $("#config_box").html(node)
        if (message.registered) {
          $("#registration_form input[type=submit]").prop("disabled", true);
        }
        //node.hide();
        //$("#player_box ul").append(node);
        //node.slideDown();
    },

    startGame: function(message) {
      var node = $(message.html)
      $("#container").html(node)
      $("#declare_action_form").on("submit", function() {
        declareAction($(this));
        return false;
      });
    },

    updateGame: function(message) {
        content = message['content']
        window.console.log("updateGame: " + JSON.stringify(content))
        message_type = content['update_type']
        if ('round_start_message' == message_type) {
          window.console.log("round_start_message: " + content)
        } else if ('street_start_message' == message_type) {
          updater.newStreet(content.table_html, content.event_html)
        } else if ('game_update_message' == message_type) {
          updater.newAction(content.table_html, content.event_html)
       } else if ('round_result_message' == message_type) {
         updater.roundResult(content.table_html, content.event_html)
       } else if ('ask_message' == message_type) {
         updater.askAction(content.table_html, content.event_html)
       } else {
          window.console.error("unexpected message in updateGame: " + content)
       }
    },

    newStreet: function(table_html, event_html) {
      $("#table").html($(table_html))
      $("#event_box").html($(event_html))
    },

    newAction: function(table_html, event_html) {
      $("#table").html($(table_html))
      $("#event_box").html($(event_html))
    },

    roundResult: function(table_html, event_html) {
      $("#table").html($(table_html))
      $("#event_box").html($(event_html))
    },

    askAction: function(table_html, event_html) {
      $("#table").html($(table_html))
      $("#event_box").html($(event_html))
    }
};
