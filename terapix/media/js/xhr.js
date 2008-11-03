
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
 * Note:
 *
 * Please note that this page documents Javascript code. <HttpRequest> is a pseudo-class, 
 * it provides encapsulation and basic public/private features.
 *
 * Constructor Parameters:
 *
 * cont - string or DOM element: name of parent DOM block container
 * errorHandler - function code with one argument (error message)
 * resultHandler - function code with one argument (json object ready to be parsed)
 *
 * Please note that default hanlders are provided if related constructor args are missing.
 *
 */
function HttpRequest(cont, errorHandler, resultHandler) {
	var busy_msg = 'Loading data';
	var xhr = createXMLHttpRequest();
	var container;

	if (typeof cont == 'string')
		container = document.getElementById(cont);
	else if (typeof cont == 'object')
		container = cont;
	else if (typeof cont != 'undefined') {
		alert("HttpRequest: bad container of type '" + typeof cont + "'!");
		return;
	}

	if (!container) {
		// Create fake container (does not attach it to the DOM tree)
		container = document.createElement('div');
	}

	// Defaut handlers
	if (!errorHandler) {
		var errorHandler = function(msg) {
			var div = document.createElement('div');
			var p = document.createElement('p');

			div.setAttribute('class', 'warning');
			div.setAttribute('style', 'width: 40%');
			p.appendChild(document.createTextNode(msg));
			div.appendChild(p);
			removeAllChildrenNodes(container);
			container.appendChild(div);
		}
	}

	var resultHandler = resultHandler || function(json) { alert(json); }

	function createXMLHttpRequest() {
		try { return new ActiveXObject(Msxml2.XMLHTTP); } catch (e) {}
		try { return new ActiveXObject(Microsoft.XMLHTTP); } catch (e) {}
		try { return new XMLHttpRequest(); } catch(e) {}
		alert("XMLHttpRequest not supported");
	
		return null;
	}

	if (!xhr) return;

	this.setBusyMsg = function(msg) {
		busy_msg = msg ? msg : busy_msg;
	}

	this.getBusyMsg = function() {
		return busy_msg;
	}

	/*
	 * Send async HTTP request.
	 * path: path to server-side script
	 * data: string for POST data (i.e. "a=2&c=try")
	 *
	 */
	this.send = function(path, data) {
		xhr.open('post', path);
		xhr.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');

		xhr.onreadystatechange = function() {
			if (xhr.readyState == 1) {
				try {
					container.innerHTML = getLoadingHTML(busy_msg);
				} catch(e) {
					container.innerHTML = busy_msg + '...';
				}
			}
			else if (xhr.readyState == 4) {
				if (xhr.status != 200) {
					var xhrError = 'Request error. ' + xhr.responseText;
					errorHandler(xhrError);
					return;
				}
	
				// Parses JSON response
				var resp = eval('(' + xhr.responseText + ')');
				this.lastResponse = resp;
				resultHandler(resp);
			}
		}
		xhr.send(data)
	}
}
