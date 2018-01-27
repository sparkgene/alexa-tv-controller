var awsIot = require('aws-iot-device-sdk');
var exec = require('child_process').exec;

var shadowName = "tv-controller"
var thingShadows = awsIot.thingShadow({
   keyPath: "/home/pi/alexa-tv-controller/raspberrypi/certs/private.pem.key",
  certPath: "/home/pi/alexa-tv-controller/raspberrypi/certs/certificate.pem.crt",
    caPath: "/home/pi/alexa-tv-controller/raspberrypi/certs/ca.pem",
  clientId: "tv-controller",
    region: "ap-northeast-1",
    host: "your-endpoint.iot.ap-northeast-1.amazonaws.com"
});

var clientTokenGet, clientTokenUpdate, command_counter=0, requested_command;

var control_home_tv = function(command, counter){
  console.log("counter:" + counter);
  if(command_counter == 0 || command_counter == counter){
    // reset local command counter
    command_counter = counter;
    console.log("no change do nothing");
    return;
  }

  // execute command
  if(command == "tv_on"){
    requested_command = "echo 'on 0' | cec-client -s";
  }
  else{
    requested_command = "echo 'standby 0' | cec-client -s";
  }
  console.log("execute:" + requested_command);
  exec(requested_command, function(err, stdout, stderr){
    if (err) {
      console.log(err);
      return;
    }
    console.log(stdout);
    // update shadow
    clientTokenUpdate = thingShadows.update(shadowName, {
      "state":{
        "reported": {
          "counter": counter,
          "command": command,
        }
      }
    });
  });
}

thingShadows.on('connect', function() {
    console.log('connected');
    thingShadows.register( shadowName );
    console.log('registered');
    setTimeout( function() {
       clientTokenGet = thingShadows.get(shadowName);
    }, 1000 );
});

thingShadows.on('status', function(thingName, stat, clientToken, stateObject) {
    console.log('received ' + stat + ' on ' + thingName + ': ' + JSON.stringify(stateObject));
    if( stat == "accepted" ){
      if( clientTokenGet == clientToken ){
        if(requested_command === undefined){
          requested_command = stateObject.state.desired.command;
        }
        // result of get event
        control_home_tv(stateObject.state.desired.command, stateObject.state.desired.counter);
      }
      else if( clientTokenUpdate == clientToken){
        // result of update event
        console.log("update accepted");
      }
    }
});

thingShadows.on('delta', function(thingName, stateObject) {
    console.log('received delta on ' + thingName + ': ' + JSON.stringify(stateObject));
    control_home_tv(stateObject.state.command, stateObject.state.counter);
});

thingShadows.on('timeout', function(thingName, clientToken) {
     console.log('received timeout on ' + operation + ': ' + clientToken);
});

process.on('SIGINT', function() {
  process.exit();
});