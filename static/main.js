/**
 * Created by denis on 3/8/16.
 */
var token = '';
$.ajax({
    type: "GET",
    url: '/api/auth/token/',
    success: function (data){
        console.log(data);
        token = data['X-Token']
    }
});

var socket = io('http://192.168.72.148:3000/');

socket.on('news', function (data) {
    console.log(data);
});
socket.on('server-got-message', function (data) {
    $('#messages').append('<li>'+ data.message + '</li>');
});
socket.on('connect', function(){
    console.log(token);
    socket.emit('authentication', {token: token});
    socket.on('authenticated', function() {
        console.log('Yo!');
    });
    socket.on('unauthorized', function(err){
        console.log("Noooo!: ", err.message);
    });
});

function sendMessage(message) {
    socket.emit('client-sent-message', {message: message})
}