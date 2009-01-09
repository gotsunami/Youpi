function toggleDisplay(id) {
	var e = document.getElementById(id);
	if (!e) return;

	e.style.display == 'none' ? e.style.display = 'block' : e.style.display = 'none';
}

/*
 * Deletes all children nodes of a child
 *
 */
function removeAllChildrenNodes(node)
{
	if (!node) return;

	// Element ?
	if (node.nodeType != 1) {
		alert('Not an element. Cannot remove children');
		return;
	}

	if (node.hasChildNodes()) {
		for (var n=0; n < node.childNodes.length; n++) {
			node.removeChild(node.childNodes[n]);
		}
	}
}

// Can be used when .innerHTML does not work :(
function emptyContainer(container_id) {
	var container = document.getElementById(container_id);
	var p = container.parentNode;
	p.removeChild(container);
	var container = document.createElement('div');
	container.setAttribute('id', container_id);
	p.appendChild(container);

	return container;
}

/*
 * Reduces string length to max chars
 * Returns a span DOM element
 * '...' are added with a tooltip showing full text
 *
 */
function reduceString(msg, max) {
	var max = max ? max : 20;
	var span = document.createElement('span');
	var rmsg = msg;
	if (!msg) {
		span.appendChild(document.createTextNode('Unknown'));
		return span;
	}

	if (msg.length > max) {
		rmsg = msg.substr(0, max/2) + '...' + msg.substr(msg.length-(max-max/2+3), max-max/2+3);
		span.setAttribute('title', msg);
	}
	span.appendChild(document.createTextNode(rmsg));

	return span;
}

/*
 * Function: getSelect
 * Builds and returns a DOM select node
 *
 * with a supplied ID and a list of options as parameters
 *
 * Parameters:
 *  id - string: unique element id
 *  options - array of strings
 *  size - integer: > 1 for multiple select (defaults to 1)
 *
 * Returns:
 *  DOM select node
 *
 */
function getSelect(id, options, size) {
	size = size ? size : 1;
	var select = document.createElement('select');
	select.setAttribute('id', id);
	if (size > 1) {
		select.setAttribute('size', size);
		select.setAttribute('multiple', 'true');
	}

	var option = null;
	for(var i=0; i<options.length; i++) {
		option = document.createElement('option');
		option.setAttribute('value', i);
		option.appendChild(document.createTextNode(options[i]));
		select.appendChild(option);
	}

	if (size > 1) {
		// Select first option by default
		select.options[0].selected = true;
	}

	return select;
}

function getMessageNode(msg, cssClass, width, mtop) {
	var cls = cssClass || 'tip';
	var w = width || '40%';
	var t = mtop || '30px';

	var div = document.createElement('div');
	var p = document.createElement('p');

	div.setAttribute('class', cls);
	div.setAttribute('align', 'center');
	div.setAttribute('style', 'width: ' + w + '; margin-top: ' + t);
	p.appendChild(document.createTextNode(msg));
	div.appendChild(p);

	return div;
}

function getLoadingHTML(msg)
{
	return '<span><img src="/media/themes/' + guistyle + '/img/misc/running_bar.gif"/> ' + msg + '...</span>';
}

/*
 * Returns a DOM table filled with json_results
 * json_results must look like {'header' : [], 'data' : []}
 *
 */
function getDOMTableFromResults(json_results, style)
{
	if (!json_results) return;

	// Default CSS style for table element
	var style = style || 'history';
	var res = json_results;

	// Table and header
	var table = document.createElement('table');
	var tr = document.createElement('tr');
	table.setAttribute('class', style);

	for (var j=0; j < res['header'].length; j++) {
		var th = document.createElement('th');
		th.appendChild(document.createTextNode(res['header'][j].capitalize()));
		tr.appendChild(th);
	}
	table.appendChild(tr);

	for (var i=0; i < res['data'].length; i++) {
		var tr = document.createElement('tr');

		for (var j=0; j < res['header'].length; j++) {
			var td = document.createElement('td');
			var data = res['data'][i][res['header'][j]];
			// Value's type
			var n;
			switch (data[1]) {
				case 'str':
					n =	document.createTextNode(data[0]);
					break;
				case 'check':
					var n = document.createElement('img');
					var state = data[0] == 0 ? 'off' : 'on';
					n.setAttribute('src', '/media/themes/' + guistyle + '/img/misc/checkbox_' + state + '.gif');
					break;
				case 'exit':
					var n = document.createElement('img');
					var state = data[0] == 0 ? 'success' : 'error';
					n.setAttribute('src', '/media/themes/' + guistyle + '/img/admin/icon_' + state + '.gif');
					break;
				case 'link':
					var n = document.createElement('a');
					n.setAttribute('href', data[2]);
					n.appendChild(document.createTextNode(data[0]));
					break;
				default:
					break;
			}
			td.appendChild(n);
			tr.appendChild(td);
		}

		table.appendChild(tr);
	}

	return table;
}

/*
 * ResultTable Object
 *
 * Usage:
 *
 * var t = new ResultTable();
 * container.appendChild(t.render(json));
 *
 * Serveur response must be a JSON object matching the following structure:
 *
 * json = { 'query'  : 'SQL query here',
 *			'fields' : 'Header fields',
 *			'hidden' : [list of hidden fields by name],
 *			'data'   : [[data1], [data2], ..., [datan]]
 * }
 *
 */
function ResultTable(style) {

	// Default CSS style for table element
	var style = style || 'history';
	
	this.render = function(json) {
		if (!json) {
			return document.createTextNode('Valid JSON response required !');
		}
	
		var resp = json;
	
		// Table and header
		var table = document.createElement('table');
		var tr = document.createElement('tr');
		table.setAttribute('class', style);
	
		for (var j=0; j < resp['fields'].length; j++) {
			var show = true;
			for (var k=0; k < resp['hidden'].length; k++) {
				if (resp['hidden'][k] == resp['fields'][j]) {
					show = false;
					break;
				}
			}
			
			// Hide if needed
			if (!show) continue;

			var th = document.createElement('th');
			th.appendChild(document.createTextNode(resp['fields'][j].capitalize()));
			tr.appendChild(th);
		}
		table.appendChild(tr);
	
		var rowClass;
		for (var i=0; i < resp['data'].length; i++) {
			var tr = document.createElement('tr');

			// Since i starts from 0 which is line #1
			i%2 == 0 ? rowClass = 'impair' : rowClass = 'pair';
			tr.setAttribute('class', rowClass);
	
			for (var j=0; j < resp['fields'].length; j++) {
				var show = true;
				for (var k=0; k < resp['hidden'].length; k++) {
					if (resp['hidden'][k] == resp['fields'][j]) {
						show = false;
						break;
					}
				}
				
				// Hide if needed
				if (!show) continue;

				var td = document.createElement('td');
				td.appendChild(document.createTextNode(resp['data'][i][j]));
				tr.appendChild(td);
			}
	
			table.appendChild(tr);
		}
	
		return table;
	}
}

/*
 * post_url: path to server-side script that MUST return a JSON object
 *           with those mandatory properties:
 *             json = {'data' : [list of json objects], 'header' : [list of header fields]}
 *
 */
function queryUrlDisplayAsTable(container_id, select_limit_id, post_url, style)
{
	var container = document.getElementById(container_id);
	var sel = document.getElementById(select_limit_id);
	var limit;

	sel ? limit = sel.options[sel.selectedIndex].value : limit = 0;

	var xhr = new HttpRequest(
		container.id,
		null, // Use default error handler
		// Custom handler for results
		function(resp) {
			removeAllChildrenNodes(container);
			container.appendChild(getDOMTableFromResults(resp, style));
		}
	);

	post = 	'limit=' + limit;

	// Send HTTP POST request
	xhr.send(post_url, post);
}

/*
 * Used in templates results.html and single_result.html
 *
 */
function results_showDetails(pname, id, fullpage) {
	var fullpage = fullpage ? true : false;
	var div = document.getElementById('infopanel');
	var r = new HttpRequest(
		div.id,
		null,
		// Custom handler for results
		function(resp) {
			div.innerHTML = '';
			if (fullpage) {
				var a = document.createElement('a');
				a.setAttribute('href', '/youpi/results/' + pname + '/' + id + '/');
				a.appendChild(document.createTextNode("Click here to see a full page result for '" + resp['result']['Title'] + "'"));
				div.appendChild(document.createTextNode('[ '));
				div.appendChild(a);
				div.appendChild(document.createTextNode(' ]'));
			}
			// Global variable
			currentReturnedData = resp['result'];
			eval(pname + ".resultsShowEntryDetails('" + div.id + "')");
		}
	);

	var post = 'Plugin=' + pname + '&Method=getTaskInfo&TaskId=' + id;
	r.send('/youpi/process/plugin/', post);
}

/*
 * Common to every plugins. Call this function from your plugin plugin_XXX.js code
 * to add output directory support to your plugin.
 *
 */
function plugin_enableOutputDirectory(div_id, data_path) {
	var div = document.getElementById(div_id);
	var p = document.createElement('p');
	p.setAttribute('style', 'margin-top: 30px; font-size: 12px;');
	p.appendChild(document.createTextNode('By default, all data produced will be stored into '));
	var tt = document.createElement('tt');
	tt.setAttribute('style', 'color: green');
	tt.appendChild(document.createTextNode(data_path));
	p.appendChild(tt);
	p.appendChild(document.createTextNode('.'));
	div.appendChild(p);
	
	p = document.createElement('p');
	p.setAttribute('style', 'margin-top: 30px; font-size: 12px; font-weight: bold;');
	p.appendChild(document.createTextNode('For convenience, you can append a custom directory suffix that will be used to save output data '));
	var u = document.createElement('u');
	u.appendChild(document.createTextNode('for this cart item only'));
	p.appendChild(u);
	p.appendChild(document.createTextNode(':'));
	p.appendChild(document.createElement('br'));
	var d = document.createElement('div');
	d.setAttribute('style', 'width: 60%; background-color: lightgray; padding: 10px; margin-top: 10px;');
	var tt = document.createElement('tt');
	tt.appendChild(document.createTextNode(data_path));
	var input = document.createElement('input');
	input.setAttribute('id', 'output_path_input');
	input.setAttribute('type', 'text');
	input.setAttribute('size', '20');
	tt.appendChild(input);
	d.appendChild(tt);
	d.appendChild(document.createTextNode('/'));
	p.appendChild(d);
	div.appendChild(p);
}

/*
 * Function: validate_container
 * Checks whether a container is valid.
 *
 * Parameters:
 *  container - string of DOM element for rendering content
 *
 * Returns:
 *  DOM element or null
 *
 */ 
function validate_container(container) {
	var d;
	if (typeof container == 'string' && container.length) {
		d = document.getElementById(container);
		if (!d) {
			_error("bad container '" + container + "' used!");
		return null;
		}
	}
	else if (typeof container == 'object') {
		d = container;
	}
else {
		_error('container must be string or a DOM object!');
		return null;
	}

	return d;
}

/*
 * Class: DropdownBox
 *
 * Dependencies:
 *  scriptaculous.js - 3rdParty Javascript library
 *
 * Constructor Parameters:
 *  container - DOM object or string: name of parent DOM block container
 *  title - string: box's title
 *
 */
function DropdownBox(container, title) 
{
	// Group: Constants
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _container
	 * Top-level DOM container
	 *
	 */
	var _container = $(container);


	// Group: Variables
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _title
	 * Box's title
	 *
	 */
	var _title;
	/*
	 * Var: _contentContainer
	 * Content DOM DIV container
	 *
	 */
	var _contentContainer;
	/*
	 * Var: _isTopLevelContainer
	 * true is the box is defined as a top level container (default: true)
	 *
	 */
	var _isTopLevelContainer = true;
	/*
	 * Var: _onClickHandler
	 * custom function handler to execute in response to onclick events on label
	 *
	 */
	var _onClickHandler = null;
	/*
	 * Var: _stateOpen
	 * true if the dropdown box is opened (default: false)
	 *
	 */
	var _stateOpen = false;
	/*
	 * Var: _titleNode
	 * DOM label node for box's title
	 *
	 */
	var _titleNode;
	/*
	 * Var: _mainDiv
	 * Main DIV (clickable) DOM node
	 *
	 */
	var _mainDiv;


	// Group: Functions
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
  	 * Function: _main
	 * Main entry point
	 *
	 */
	function _main() {
		_title = title;

		if (!_container.hasAttribute('id')) {
			_container.setAttribute('id', 'dropdown_box_' + Math.random() + '_div');
		}

		var topDiv = document.createElement('div');
		topDiv.setAttribute('class', 'ebox');
		_mainDiv = document.createElement('div');

		_mainDiv.observe('click', function() { 
			_toggleState();
			if (_onClickHandler)
				_onClickHandler();
		});

		_titleNode = new Element('label').insert(_title);
		var cdiv = document.createElement('div');
		cdiv.setAttribute('style', 'display: none;');
		cdiv.setAttribute('id', _container.getAttribute('id') + '_' + Math.random() + '_content');
		_contentContainer = cdiv;
		_mainDiv.appendChild(_titleNode);
		topDiv.appendChild(_mainDiv);
		topDiv.appendChild(cdiv);
		_container.appendChild(topDiv);

		_setOpen(false);
	}

	/*
  	 * Function: getRootNode
	 * Returns root (top-level) DOM node
	 *
	 * Returns:
	 *  Top-level DOM container
	 *
	 */
	this.getRootNode = function() {
		return _container;
	}

	/*
  	 * Function: setTitle
	 * Sets box's main title
	 *
	 */
	this.setTitle = function(title) {
		if (typeof title == 'string') {
			_title = title;
			_titleNode.innerHTML = '';
			_titleNode.appendChild(document.createTextNode(_title));
		}
		else
			alert('dbox::setTitle error: bad title, must be a string!');
	}

	/*
  	 * Function: getContentNode
	 * Returns content DOM node
	 *
	 * Returns:
	 *  Content DIV DOM container
	 *
	 */
	this.getContentNode = function() {
		return _contentContainer;
	}

	/*
  	 * Function: setTopLevelContainer
	 * Indicates whether the box is a top-level container
	 *
	 * CSS styles used depend on this parameter.
	 *
	 * Parameters:
	 *  is_top - boolean: True if top-level container
	 *
	 */
	this.setTopLevelContainer = function(is_top) {
		_isTopLevelContainer = (typeof is_top == 'boolean' && is_top) ? true : false;
		_setOpen(_stateOpen);
	}

	/*
  	 * Function: isTopLevelContainer
	 * Returns true if the box has been defined as a top level container 
	 *
	 * Returns:
	 *  boolean
	 *
	 */
	this.isTopLevelContainer = function() {
		return _isTopLevelContainer;
	}

	/*
  	 * Function: setOnClickHandler
	 * Defines custom handler function for OnClick box's events
	 *
	 * Parameters:
	 *  handler - function: custom handler function
	 *
	 */
	this.setOnClickHandler = function(handler) {
		_onClickHandler = typeof handler == 'function' ? handler : null;
	}

	/*
  	 * Function: getOnClickHandler
	 * Returns custom handler used
	 *
	 * Returns:
	 *  function handler or null
	 *
	 */
	this.getOnClickHandler = function() {
		return _onClickHandler;
	}

	/*
  	 * Function: isOpen
	 * Returns box's open state
	 *
	 * Returns:
	 *  boolean - true if open; otherwise false
	 *
	 */
	this.isOpen = function() {
		return _stateOpen;
	}

	/*
  	 * Function: setOpen
	 * Defines whether the box is open
	 *
	 * Parameters:
	 *  open - boolean
	 *
	 */
	this.setOpen = function(open) {
		_setOpen(open);
	}

	/*
  	 * Function: _toggleState
	 * Toggles box's state (opened or closed) 
	 *
	 */
	function _toggleState() {
		_stateOpen = !_stateOpen;
		_setOpen(_stateOpen);
	}

	/*
  	 * Function: _setOpen
	 * Defines whether the box is open
	 *
	 * Parameters:
	 *  open - boolean
	 *
	 */
	function _setOpen(open) {
		var gfx;
		_stateOpen = (typeof open == 'boolean' && open) ? true : false;
		_mainDiv.setAttribute('class', 'banner_' + (_stateOpen ? 'opened' : 'closed') + (!_isTopLevelContainer ? '_child' : ''));
		_stateOpen ? $(_contentContainer).show() : $(_contentContainer).hide();
	}

	/*
  	 * Function: _main
	 * Main entry point
	 *
	 */
	_main();
}


/*
 * Class: Logger
 * Class providing logging facilities
 *
 * Note:
 *
 * Please note that this page documents Javascript code. <Logger> is a pseudo-class, 
 * it provides encapsulation and basic public/private features.
 *
 * Constructor Parameters:
 *
 * container - object or string: name of parent DOM block container
 *
 */
function Logger(container) 
{
	// Group: Constants
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _log
	 * Top-level DOM container
	 *
	 */
	var _log;


	// Group: Functions
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: _init
	 * Main entry point
	 *
	 */ 
	function _init() {
		if (typeof container == 'object') {
			_log = container;
		}
		else if (typeof container == 'string') {
			_log = document.getElementById(container);
		}
	
		if (!_log) {
			alert('logger error: no valid container defined!');
		}
	}

	/*
	 * Function: msg_status
	 * Display a status message
	 *
	 * Parameters:
	 *  msg - string: message
	 *
	 */ 
	this.msg_status = function(msg) {
		var line = document.createElement('div');
		line.setAttribute('class', 'logger_status');
		line.appendChild(document.createTextNode(msg));
		_log.appendChild(line);
	}

	/*
	 * Function: clear
	 * Clear log
	 *
	 */ 
	this.clear = function() {
		_log.innerHTML = '';
	}

	/*
	 * Function: msg_ok
	 * Display an 'OK' message
	 *
	 * Parameters:
	 *  msg - string: message
	 *
	 */ 
	this.msg_ok = function(msg) {
		var line = document.createElement('div');
		line.setAttribute('class', 'logger_ok');
		line.appendChild(document.createTextNode(msg));
		_log.appendChild(line);
	}

	/*
	 * Function: msg_warning
	 * Display a warning message
	 *
	 * Parameters:
	 *  msg - string: message
	 *
	 */ 
	this.msg_warning = function(msg) {
		var line = document.createElement('div');
		line.setAttribute('class', 'logger_warning');
		line.appendChild(document.createTextNode(msg));
		_log.appendChild(line);
	}

	/*
	 * Function: msg_error
	 * Display an error message
	 *
	 * Parameters:
	 *  msg - string: message
	 *  alertBox - boolean: whether to display an alert box on the screen
	 *
	 */ 
	this.msg_error = function(msg, alertBox) {
		var do_ab = alertBox ? true : false;
		var line = document.createElement('div');
		line.setAttribute('class', 'logger_error');
		line.appendChild(document.createTextNode(msg));
		_log.appendChild(line);
		if (do_ab)
			alert('Error: ' + msg);
	}

	_init();
}

