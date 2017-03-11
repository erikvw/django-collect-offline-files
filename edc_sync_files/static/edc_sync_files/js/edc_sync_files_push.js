
class FileTransferPush {

  constructor(fileName, hostName, urlNode, urlServer, userName, apiToken, host) {
	  this.fileName = fileName;
	  this.hostName = hostName;
	  this.urlNode = urlNode;
	  this.urlServer = urlServer;
	  this.userName = userName;
	  this.apiToken = apiToken;
	  this.data = [];
	  this.host = host;
  } 

  getRegisteredFiles() {
	  /*
	   * GET CLIENT FILES
	   */
	  return $.ajax({
		url: this.urlNode,
		type: 'GET',
		dataType: 'json',
		contentType: 'application/json',
		data: {
			action: 'get-files',
		}
	 });
  }
  
  determineFilesToTransfer() {
	  /*
	   * 2. REST TO SERVER.
	   */
	  var registeredFiles = this.getRegisteredFiles();
	  registeredFiles.then( function( data ) {
		  registered-files = data.registered-files.toString();
		  return $.ajax({
				url: this.urlServer,
				type: 'GET',
				dataType: 'json',
				contentType: 'application/json',
				data: {
					action: 'determine-files-to-transfer',
				}
		  });
	  });

	  registeredFiles.fail(function(){
		  console.log('error');
	  });
  }
  
  displayFilesToTransfer() {
	  var filesToTransfer = this.determineFilesToTransfer();
	  filesToTransfer.then( function( data ) {
		$.each( data.mediafiles, function(idx,  mediaFile  ) {
			idx = idx + 1;
			spanElemStatus = "<span id="+mediaFile.filename+"></span>"
			files.push(mediaFile.filename);
			$("<tr><td>"+idx+"</td><td>"+mediaFile.filename+"</td><td>"+mediaFile.filesize+"</td><td>"+spanElemStatus+"</td></tr>").appendTo("#id-table-body");
		});
	  });
  }
  
  sendFile() {
	$('#id-table-body tr').each(function() {
	    var filename = $(this).find("td").eq(1).html();
	    var transfer_file = $.ajax({
			async: false,
			url: this.urlNode,
			type: 'GET',
			dataType: 'json',
			contentType: 'application/json',
			data: {
				action: 'transfer-file',
				filename: filename
			}
	  });
	    transfer_file.done( function(){
	    	$(this).find("td").eq(3).html("<span class='glyphicon glyphicon-saved'></span>");
	    });
	    transfer_file.fail( function(){
	    	$(this).find("td").eq(3).html("<span class='glyphicon glyphicon-alert'></span>");
	    });
	});
  }
  displayProgresStatus(message, alert_class) {
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
 
  createHistory(fileName) {
	  return $.ajax({
			url: this.urlServer,
			type: 'PUT',
			dataType: 'json',
			contentType: 'application/json',
			data: {
				filename: this.fileName,
				hostname: this.hostName
			}
	  });  
  }
}