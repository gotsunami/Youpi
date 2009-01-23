function  setup(param) {

	var post = '';

	var value = $F(param + '_input');

	if (param == 'create_survey') {
		post += '&Survey=' + value;
		}

	else if (param == 'create_instrument') { 
		
		var survey = $F('select_survey_list');
		post += '&Survey=' + survey + '&Instrument=' + value;
		}
	
	else if(param == 'create_release') {
		var survey = $F('select_survey_list');
		var instrument = $F('select_instrument_list');
		post +=  '&Survey=' + survey + '&Instrument=' + instrument + '&Release=' + value;
		}


    var xhr = new HttpRequest(
            null,
            null,   
            // Custom handler for results
            function(resp) {

				var log = new Logger(param + '_log');
				log.clear();
				if (resp['Error'].length) {
					log.msg_error(resp['Error']);
					return;
				}
				if (resp['Warning'].length) {
					log.msg_warning(resp['Warning']);
					return;
				}
				else {
					log.msg_ok('OK : '+ param + ' saved...');
					if (param == 'create_survey') {
						$('create_instrument').show()
						var select = $('select_survey_list');
						var option = document.createElement('option');
						option.update(value);
						select.appendChild(option);
						}
					else if (param == 'create_instrument') {
						$('create_release').show();
						var select = $('select_instrument_list');
						option = document.createElement('option');
						option.update(value);
						select.appendChild(option);
					}
					else if (param == 'create_release') {
						var select = $('select_release_list');
						option = document.createElement('option');
						option.update(value);
						select.appendChild(option);
					}
				}
			}
    );

    post += '&Param=' + param + '&Value=' + value;
    xhr.send('/youpi/newindex/', post);
}


function kselect(param) {
	
	var post = '';
	if (param == 'select_survey_list') {
		var name = $F('select_survey_list');
		}
	else if (param == 'select_instrument_list') {
			var name = $F('select_instrument_list');
			}
	else if (param == 'select_release_list') {
			var name = $F('select_release_list');
			}

    var xhr = new HttpRequest(
            null,
            null,   
            // Custom handler for results
            function(resp) {

				var log = new Logger(param + '_log');
				log.clear();
				if (resp['Error'].length) {
					log.msg_error(resp['Error']);
					return;
				}
				if (resp['Warning'].length) {
					log.msg_warning(resp['Warning']);
					return;
				}
				else {
					if (param == 'select_survey_list') {
						list_instrument = resp['list_instrument'];
						var select = $('select_instrument_list');
						var chil = select.childElements();
						chil.each(function(node){node.remove();});
						$('or2').show();
						$('select_instrument').show();
						$('create_instrument').show();
						$('instrument_text').update('Add instrument for survey : <B> ' + name + '</B>');
						for (var i = 0 ; i < list_instrument.length ; i++) {
							var option = document.createElement('option');
							option.update(list_instrument[i]);
							select.appendChild(option);
							}
					}
					if (param == 'select_instrument_list') {
						list_release = resp['list_release'];
						var select = $('select_release_list');
						var chil = select.childElements();
						chil.each(function(node){node.remove();});
						$('or3').show();
						$('select_release').show();
						$('create_release').show();
						$('release_text').update('Add release for instrument : <B> ' + name + '</B>');
						for (var i = 0 ; i < list_release.length ; i++) {
							var option = document.createElement('option');
							option.update(list_release[i]);
							select.appendChild(option);
							}

					}
					if (param == 'select_release_list') {
					}

				}
			}
    );
    post += '&Param=' + param + '&Value=' + name;
    xhr.send('/youpi/newindex/', post);
}


