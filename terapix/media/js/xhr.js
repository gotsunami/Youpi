/*****************************************************************************
 *
 * Copyright (c) 2008-2009 Terapix Youpi development team. All Rights Reserved.
 *                    Mathias Monnerville <monnerville@iap.fr>
 *                    Gregory Semah <semah@iap.fr>
 *
 * This program is Free Software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 *****************************************************************************/


/*
 * Function: createXMLHttpRequest
 * Creates a new XMLHttpRequest object
 *
 * Returns:
 *
 * new XMLHttpRequest instance
 *
 */
function createXMLHttpRequest() {
	try { return new ActiveXObject(Msxml2.XMLHTTP); } catch (e) {}
	try { return new ActiveXObject(Microsoft.XMLHTTP); } catch (e) {}
	try { return new XMLHttpRequest(); } catch(e) {}
	alert("XMLHttpRequest not supported");

	return null;
}

/*
 * Class: HttpRequest
 * Simple implementation for handling AJAX HTTP requests
 *
 * Constructor Parameters:
 *  cont - string or DOM element: name of parent DOM block container
 *  errorHandler - function code with one argument (error message)
 *  resultHandler - function code with one argument (json object ready to be parsed)
 *
 * Please note that default hanlders are provided if related constructor args are missing.
 *
 */
function HttpRequest(cont, errorHandler, resultHandler) {
	var _busy_msg = 'Loading data';
	var _xhr;
	var _container = $(cont);
	var _errorHandler;
	var _resultHandler;
	/*
	 * Var: _customAnimatedImage
	 * Custom path to (animated) image to be displayed while waiting
	 * for Ajax response
	 *
	 */
	var _customAnimatedImage = null;

	function _main() {
		_xhr = _createXMLHttpRequest();
		if (!_xhr) 
			console.error('No XMLHTTP request support found.');

		if (!_container) {
			// Create fake container (does not attach it to the DOM tree)
			_container = new Element('div');
		}

		// Defaut handlers
		if (!errorHandler) {
			var errorHandler = function(msg) {
				var p = new Element('p');
				p.update(msg);
				var div = new Element('div', {'class': 'warning', 'style': 'width: 40%'});
				div.insert(p);

				_container.update();
				_container.insert(div);
			}
		}

		_errorHandler = errorHandler;
		_resultHandler = typeof resultHandler == 'function' ? resultHandler : function(json) { alert(json); }
	}

	function _createXMLHttpRequest() {
		try { return new ActiveXObject(Msxml2.XMLHTTP); } catch (e) {}
		try { return new ActiveXObject(Microsoft.XMLHTTP); } catch (e) {}
		try { return new XMLHttpRequest(); } catch(e) {}
		alert("XMLHttpRequest not supported");
	
		return null;
	}


	this.setBusyMsg = function(msg) {
		_busy_msg = typeof msg == 'string' && msg.length ? msg : _busy_msg;
	}

	this.getBusyMsg = function() {
		return _busy_msg;
	}

	// path can be null
	this.setCustomAnimatedImage = function(path) {
		_customAnimatedImage = path;
	}

	/*
	 * Sends async HTTP request
	 *
	 * Parameters:
	 *  path - string: path to server-side script
	 *  data - string for POST data (i.e. "a=2&c=try")
	 *  async - boolean: whether the call is asynchronous [default: true]
	 *
	 */
	this.send = function(path, data, async) {
		async = typeof async == 'boolean' ? async : true;
		_xhr.open('post', path, async);
		_xhr.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');

		if (async) {
			_xhr.onreadystatechange = function() {
				if (_xhr.readyState == 1) {
					if (_customAnimatedImage) {
						var rt = new Element('table').setStyle({width: '100%', height: '100%'});
						var rtr, rtd;
						rtr = new Element('tr');
						rtd = new Element('td').setStyle({
							textAlign: 'center', 
							verticalAlign: 'middle', 
							color: 'brown', 
							fontSize: '9px'
						});
						rtr.insert(rtd);
						var img = new Element('img', {src: _customAnimatedImage});
						rtd.insert(img).insert(new Element('br')).insert(_busy_msg);
						rt.insert(rtr);
						_container.update(rt);
					}
					else {
						try {
							_container.update(getLoadingHTML(_busy_msg));
						} catch(e) {
							_container.update(_busy_msg + '...');
						}
					}
				}
				else if (_xhr.readyState == 4) {
					if (_xhr.status != 200) {
						var xhrError = 'Request error. ' + _xhr.responseText;
						_errorHandler(xhrError);
						return;
					}
		
					// Parses JSON response
					var resp = eval('(' + _xhr.responseText + ')');
					this.lastResponse = resp;
					_resultHandler(resp);
				}
			}
		}
		_xhr.send(data)

		if (!async) {
			var resp = eval('(' + _xhr.responseText + ')');
			this.lastResponse = resp;
			_resultHandler(resp);
		}
	}

	_main();
}
