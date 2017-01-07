$(document).ready(function(){
    namespace = '/hostinfo'
    var socket = io.connect('http://' + document.domain + ':' + location.port + namespace);
    socket.on('connect', function() {
        console.log('connected to the server')
    });
    /* test websocket connect
    socket.on('my_response', function(msg){
        $('#log').append('<br>' + $('<div/>').text(msg.data).html());
    });
    */
    socket.on('update_host', function(all_hosts){
        $('#dataTables-hosts tbody tr').each(function(index){
            //$(this).children().eq(2).text( "233" )
            $(this).children().eq(2).text(all_hosts[$(this).attr('id')]);
        });
    })
})