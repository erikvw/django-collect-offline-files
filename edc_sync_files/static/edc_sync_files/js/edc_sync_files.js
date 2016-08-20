//var mediaCountUrl = Urls[ 'edc-sync:media-count' ]();

function edcSyncMediaFilesReady(hosts, url) {
	/* Prepare page elements */
	var hosts = JSON.parse( hosts );

	// make elements for each host, set the onClick event
	$.each( hosts, function( host ) {
		ip_address = host;
		var divId = 'id-nav-pull-resources';
		makePageElementsMediaDiv( divId, host );
		mediaCount( ip_address, url);
		/* this is the onClick event that starts the data transfer for this host.*/
		$( '#id-link-pull-' + host.replace( ':', '-' ).split( '.' ).join( '-' ) ).click( function (e) {
			e.preventDefault();
			ip_address = $( this ).val();
			displayProgresStatus('Transferring files from host:'+host, 'alert-info');
			//$( "#alert-progress-status" ).show();
			 $( "#id-tx-spinner" ).addClass('fa-spin');
			var mediaData = mediaCount( ip_address, url );
			mediaData.done( function( data ) {
				$.each( data.mediafiles, function(idx, filename ) {
					 idx = idx + 1;
					 displayProgresStatus('Transferring files from host:'+data.host, 'alert-info');
					 //addRowProgressStatus(filename);
					 processMediaFiles( data.host, filename, url , idx, data.mediafiles.length);
				});
				if (data.mediafiles.length == 0) {
					displayProgresStatus('No media files found on host: '+ip_address, 'alert-success');
					$( "#id-tx-spinner" ).removeClass('fa-spin');
				}
			});
			mediaData.fail(function( jqXHR, textStatus, errorThrown ) {
				$( "#id-tx-spinner" ).removeClass('fa-spin');
				displayProgresStatus('An error occurred while trying to copy media file from:'+ip_address+ '. Got '+ errorThrown, 'alert-danger');
			} );
			mediaData.then(function(){
				displayProgresStatus('Transferring files from host:'+data.host, 'alert-info');
			});
		});
	});
}

function mediaCount(host, url) {
	/* 
	 * Count media files on a remote machine.
	 * 1. GET on the server.
	 * 2. Connect to remote machine with paramiko
	 * 3. Get remote machine file information and check it again the server
	 * 4. return a list of media file to copy.
	 */

	var mediaCountResponse = $.ajax({
		url: url,
		type: 'GET',
		dataType: 'json',
		data: {
			host: host,
			action: 'media-count'
		},
	}).promise();

	mediaCountResponse.done(function( data ) {
		/* On a success display the result */
		var mediaCount = data.mediafiles.length;
		$( "#id-link-pull-" + host ).text( mediaCount );
	} );
	mediaCountResponse.fail(function() {
		console.log("Error occurred");
		//displayProgresStatus('An error occurred trying to copy media file from:'+errorThrown, 'alert-danger');
	} ); 
	return mediaCountResponse;
}

function processMediaFiles ( host, filename, url, sent_media, total_media) {
	/*
	 * Pull a single media from a host.
	 * 1. GET on a server to pull media file.
	 * 2. Connect to host with paramiko then sftp.get file.
	 * 3. On success, create a history record in the server.
	 */
	$("#id-tx-spinner").addClass( 'fa-spin' );
	$("#id-media-count").text( " " + sent_media + "/" +  total_media + "." );
	
	var pendingMediaFiles = $.ajax({
		url: url,
		type: 'GET',
		dataType: 'json',
		data: {
			action: 'pull',
			host: host,
			filename: filename,
		}
	}).promise();

	pendingMediaFiles.done(function( data ) {
		/* on success */ 
		if( sent_media == 0 && total_media == 0) {
			displayProgresStatus('No media found on host: '+data.host, 'alert-success');	
		} else if (sent_media == total_media) {
			displayProgresStatus('All media file(s) have been transferred to server. Copied from host:'+data.host+'. ', 'alert-success');
		} else {
			//displayProgresStatus('Transferring files from host:'+data.host, 'alert-info');
		}
	});

	pendingMediaFiles.fail(function(jqXHR, textStatus, errorThrown) {
		/* Display error */
		displayProgresStatus('An error occurred trying to copy media file from:'+host+'. Got '+errorThrown, 'alert-danger');
	});

	pendingMediaFiles.always(function() {
		/* stop the spinner */
		$("#id-tx-spinner").removeClass( 'fa-spin' );
	});
}

function makePageElementsMediaDiv ( divId, host ) {
	/* Make and update page elements.
	   The "id-link-fetch- ... " onClick function pokes the API and starts the data
	   transfer and updates.*/
	var host_string = host.replace( ':', '-' ).split( '.' ).join( '-' );
	var anchorId = 'id-link-pull-' + host_string;
	var li = '<li><a id="' + anchorId + '">Fetch \'Media Files\' from ' + host + '&nbsp;<span id="id-hostname-' + host_string +'"></span>&nbsp;<span id="id-media-count-' + host_string + '" class="badge pull-right">?</span></a></li>';
	$( '#id-nav-pull-resources' ).append( li );
	$( '#id-link-pull-' + host_string ).attr( 'href', '#' );
	$( '#id-link-pull-' + host_string ).val(host);
}

function displayProgresStatus(message, alert_class) {
	if (alert_class == 'alert-danger' ) {
		$("#id-media-message").text( message );
		$("#alert-progress-status").removeClass( 'alert-info' ).addClass( 'alert-danger' );	
	} else if ( alert_class == 'alert-success' ) {
		$("#id-media-message").text( message );
		$("#alert-progress-status").removeClass( 'alert-info' ).addClass( 'alert-success' );	
	} else {
		
		$("#id-media-message").text( message );
		$("#alert-progress-status").removeClass( 'alert-danger' ).addClass( 'alert-info' );	
	}
	$( "#alert-progress-status" ).show();
}

//function addRowProgressStatus(filename) {
//	$("<tr><td>"+filename+"</td><td>Doe</td><td>john@example.com</td></tr>").appendTo("#id-table-body");
//}
