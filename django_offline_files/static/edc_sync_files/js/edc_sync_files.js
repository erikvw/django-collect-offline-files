//var mediaCountUrl = Urls[ 'edc-sync:media-count' ]();

function edcSyncMediaFilesReady(hosts, url) {
	/* Prepare page elements */
	var hosts = JSON.parse( hosts );

	// make elements for each host, set the onClick event
	idx = 0;
	$.each( hosts, function( host ) {
		ip_address = host;
		var divId = 'id-nav-pull-resources';
		makePageElementsMediaDiv( divId, host );
		mediaCount( ip_address, url);
		
		/* this is the onClick event that starts the data transfer for this host.*/
		$( '#id-link-pull-' + host.replace( ':', '-' ).split( '.' ).join( '-' ) ).click( function (e) {
			e.preventDefault();
			ip_address = $( this ).val();
			displayProgresStatus('Checking for media files from host:'+host+'. Please wait this may take a few minutes.', 'alert-info');
			 $( "#id-tx-spinner" ).addClass('fa-spin');
			 getFiles(ip_address, url);
			 $("#btn-copy-files").val(ip_address);
		});
	});

	$("#btn-copy-files").on('click', function () {
		mediaFiles = []
		$(this).text("Copying...");
		displayProgresStatus('Transferring files. In Progress...wait.', 'alert-info');
		ip_address = $( this ).val();
		$('#id-table-body tr').each(function() {
		    var filename = $(this).find("td").eq(1).html();
		    mediaFiles.push(filename);
		    $(this).find("td").eq(3).append("<span class='fas fa-spinner fa-spin'></span>");
		    iconElement = $(this);
		    transferFile(ip_address, filename, url, iconElement);
		});
		if ( mediaFiles.length == 0 ) {
			displayProgresStatus('No files found in :'+host+'.', 'alert-success');
		}
		$(this).text("Copy All To Server");
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
		$( "#id-media-count-" + host.replace( ':', '-' ).split( '.' ).join( '-' )  ).text( mediaCount );
	} );
	mediaCountResponse.fail(function(x, y, errorThrown) {
		console.log('An error occurred trying to copy media file from:'+errorThrown);
		//displayProgresStatus('An error occurred trying to copy media file from:'+errorThrown, 'alert-danger');
	} ); 
	return mediaCountResponse;
}

function getFiles(host, url) {
	var mediaFiles = $.ajax({
		url: url,
		type: 'GET',
		dataType: 'json',
		data: {
			host: host,
			action: 'media-files'
		},
	}).promise();
	
	mediaFiles.done(function( data ) {
		idx = 0;
		$("#id-table-body tr").remove();
		var files = []
		$.each( data.mediafiles, function(idx,  mediaFile  ) {
			idx = idx + 1;
			spanElemStatus = "<span id="+mediaFile.filename+"></span>"
			files.push(mediaFile.filename);
			$("<tr><td>"+idx+"</td><td>"+mediaFile.filename+"</td><td>"+mediaFile.filesize+"</td><td>"+spanElemStatus+"</td></tr>").appendTo("#id-table-body");
		});
		$("#id-tx-spinner").removeClass( 'fa-spin' );
		$("#id-host-media-files").val(files.toString());
		if (data.mediafiles.length > 0) {
			$("#id-file-table").show();
			$("#btn-copy-files").show();
			$("#btn-copy-div").show();
			displayProgresStatus('Files to be transfer from from:'+host+'.', 'alert-info');
		} else {
			displayProgresStatus('Done. No files to transfer from host: '+host+'.', 'alert-success');
		}
	});

	mediaFiles.fail(function(jqXHR, textStatus, errorThrown) {
		displayProgresStatus('An error occurred while trying to copy media file from:'+host+' Got '+errorThrown+'.Contact Systems Engineer.', 'alert-danger');
		$( "#id-tx-spinner" ).addRemove('fa-spin');
	});
	return mediaFiles;
}

function transferFile(host, filename, url, iconElement) {
	$("#id-tx-spinner").addClass( 'fa-spin' );
	var transfer = $.ajax({
		async: false,
		url: url,
		type: 'GET',
		dataType: 'json',
		data: {
			action: 'pull',
			host: host,
			filename: filename,
		}
	}).promise();
	
	transfer.done(function( data ) {
		$("#id-tx-spinner").removeClass( 'fa-spin' );
		updateIcon(iconElement, 'success');
	});

	transfer.fail(function(jqXHR, textStatus, errorThrown){
		$("#id-tx-spinner").removeClass( 'fa-spin' );
		updateIcon(iconElement, 'error');
		displayProgresStatus('An error occurred while trying to copy media file from:'+host+' Got '+errorThrown+'. Contact Systems Engineer.', 'alert-danger');
	});
	return transfer;
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


function trackFileTransfer(url, mediaFiles) {
	var transferStatus = $.ajax({
		url: url,
		type: 'GET',
		dataType: 'json',
		data: {
			mediaFiles: mediaFiles,
			action: 'track-transfer'
		},
	}).promise();

	transferStatus.done(function( data ) {
		/* On a success display the result */
		updateFileTransfer(transferStatus);
	} );
	transferStatus.fail(function() {
		alert("Error occurred tracking");
		//displayProgresStatus('An error occurred trying to copy media file from:'+errorThrown, 'alert-danger');
	}); 
}

function updateFileTransfer(transferStatus) {
	transferStatus.then(function(data) {
		$.each( data, function( fileStatus ) {
			alert(fileStatus.filename);
			//console.log(fileStatus.filename);
		});
	});
}

function updateIcon(iconElement, status) {
	if (status=='success') {
		iconElement.find("td").eq(3).html("<span class='glyphicon glyphicon-saved alert-success'></span>");
	} else if(status=='error') {
		iconElement.find("td").eq(3).html("<span class='glyphicon glyphicon-remove alert-danger'></span>");
	}
}

