// (esversion: 6)
var socket = io();
socket.on('connect', function() {
    console.log( "Connected..." );
} );

socket.on( 'disconnect', function() {
    console.log( "Disconnected..." );
} );

socket.on( 'neighbors', function(data){
    $('#contacts').html( data );
} )


socket.on( 'msg-notify', function (data) {
    // console.log("Yippie")
    if (data.tpuid == uid) {
        if ( data.uid != tpuid ) {
            pushNotify( data.title, data.msg );
            // $('#msg_alert')[0].play();
            // console.log( data.msg );
        }
    }
} )

socket.on( 'rebound-join', function(data) {
    socket.send( 'join', room = data );
})


function recomputeNeighbors(pos){
    crd = pos.coords;
    console.log(crd);
    socket.emit( "neighbors", data = {'x': crd.latitude, 'y': crd.longitude} )
}

function NavigationError(err){
    socket.emit( "neighbors", data = {'loadPrev': true} )
    console.warn( err );
}

socket.on('new-friend', function (data) {
    if (( data.uid == uid ) | (data.tpuid == uid)) {
        $.ajax({
            'url': '/friends',
            success: function(data){
                $('#chats').html( data )
            }
        });
        if ( data.uid == uid ) {
            pushNotify("You have a new homie", data.msg);
        }
        
        if ( tpuid == data.tpuid ) {
            displayHomie( data.tpuid );
        };
    }
})

socket.on( 'spit', function(data){
    alert( data );
} )

socket.on( 'push', function(data) {
    // alert(data.uid)
    // alert(data.tpuid)
    if ( data.uid == uid ) {
        pushNotify( "New notification from Neighborhood", data.msg );
        

        if ( data.tpuid == tpuid ) {
            displayHomie( data.tpuid );
        }
        
    }
    
} )

var loc, options;
options = {
    enableHighAccuracy: true,
    timeout: 5000,
    maximumAge: 0
  };

console.log("rice");
loc = navigator.geolocation.watchPosition(recomputeNeighbors, NavigationError, options);
console.log(loc)