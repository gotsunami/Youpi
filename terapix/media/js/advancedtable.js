/*
 * Class: AdvancedTable
 * Widget to display data into a table with some neat features
 *
 * Note:
 *
 * Please note that this page documents Javascript code. <FileBrowser> is a pseudo-class, 
 * it provides encapsulation and basic public/private features.
 *
 * For convenience, private data member names (both variables and functions) start with an underscore.
 *
 * Constructor Parameters:
 *
 * varName - string: global variable name of instance, used internally for public interface definition
 *
 */
function AdvancedTable(varName) {
	// Group: Constants
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _instance_name
	 * Name of instance in global namespace
	 *
	 */ 
	var _instance_name = varName;
	/*
	 * Var: _container
	 * DOM block container element
	 *
	 */
	var _container = null;
	/*
	 * Var: _container_id
	 * ID of container element
	 *
	 */
	var _container_id;
	/*
	 * Var: _events
	 * Array of available events name that can be registered with custom handlers
	 *
	 */
	var _events = [['onRowClicked', null]];
	/*
	 * Var: _autoRowIdPrefix
	 * String prefix used for automatic row id generation
	 *
	 * Used when when <_colIdxForRowIds> == -1
	 *
	 */
	var _autoRowIdPrefix = _instance_name + '.row_';
	/*
	 * Var: _userRowIdPrefix
	 * String prefix used for user-defined row id generation
	 *
	 * Used when when <_colIdxForRowIds> >= 0 
	 *
	 */
	var _userRowIdPrefix = _instance_name + '.';


	// Group: Variables
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _colIdxForRowIds
	 * Column index to use for defining row ids
	 *
	 */
	var _colIdxForRowIds = -1;
	/*
	 * Var: _mainDiv
	 * Top-level DOM parent div container
	 *
	 */
	var _mainDiv;
	/*
	 * Var: _headerDiv
	 * DOM div containing table's header
	 *
	 */
	var _headerDiv;
	/*
	 * Var: _bodyDiv
	 * DOM div containing table's body
	 *
	 */
	var _bodyDiv;
	/*
	 * Var: _headerTab
	 * DOM table in header
	 *
	 */
	var _headerTab;
	/*
	 * Var: _bodyTab
	 * DOM table in body
	 *
	 */
	var _bodyTab;
	/*
	 * Var: _headers
	 * Array containing headers col names
	 *
	 */
	var _headers = new Array();
	/*
	 * Var: _rows
	 * Array containing rows of data
	 *
	 */
	var _rows = new Array();


	// Group: Functions
	// -----------------------------------------------------------------------------------------------------------------------------

	/*
	 * Function: _error
	 * Displays custom error message
	 *
	 * Parameters:
	 *  msg - string: error message
	 *
	 */ 
	function _error(msg) {
		alert('AdvancedTable::error: ' + msg);
	}

	/*
	 * Function: rowCount
	 * Number of rows in table
	 *
	 * Returns:
	 *  int: number of rows in table
	 *
	 */ 
	this.rowCount = function() {
		return _rows.length;
	}

	/*
	 * Function: setContainer
	 * Sets container parent to use for rendering contents
	 *
	 * Parameters:
	 *  container_id - string: id of container element
	 *
	 */ 
	this.setContainer = function(container_id) {
		/*
		if (typeof container_id != 'string') {
			_error("setContainer: container must be a string id!");
			return;
		}

		var c = document.getElementById(container_id);
		if (!c) {
			_error("setContainer: container id '" + container_id + "' not found!");
			return;
		}
		*/
		_container_id = container_id;
	}

	/*
	 * Function: getContainer
	 * Returns container DOM parent
	 *
	 * Returns:
	 *  container - DOM node
	 *
	 */ 
	this.getContainer = function() {
		return document.getElementById(_container_id);
	}

	/*
	 * Function: attachEvent
	 * Attach a custom handler to a specific event
	 *
	 * Parameters:
	 *  eventName - string: name of available event
	 *  handler - function: custom handler for that event
	 *
	 * See Also:
	 *  <_events>
	 *
	 */ 
	this.attachEvent = function(eventName, handler) {
		if (typeof handler != 'function' && handler) {
			_error('attachEvent: bad handler function!');
			return;
		}
		if (!handler) {
			_error('attachEvent: undefined handler!');
			return;
		}

		var k = _checkForEventAvailability(eventName);
		if (k == -1) {
			_error('attachEvent: could not attach event');
			return;
		}

		_events[k][1] = handler;
	}

	/*
	 * Function: _checkForEventAvailability
	 * Check if an event is available
	 *
	 * Parameters:
	 *  eventName - string: name of available event
	 *
	 * Returns:
	 *  -1 - event is not available
	 *  idx - integer: >= 0 (position in <_events> array
	 *
	 * See Also:
	 *  <_events>
	 *
	 */ 
	function _checkForEventAvailability(eventName) {
		for (var k=0; k < _events.length; k++) {
			if (eventName == _events[k][0])
				break;
		}
		if (k == _events.length) {
			_error("event '" + eventName + "' not available!");
			return -1;
		}	

		return k;
	}

	/*
	 * Function: _getEventHandler
	 * Returns event handler function given an event name 
	 *
	 * Parameters:
	 *  eventName - string: name of available event
	 *
	 * Returns:
	 *  -1 - handler is not available
	 *  function - handler function, can be null (default if not attached)
	 *
	 * See Also:
	 *  <_events>
	 *
	 */ 
	function _getEventHandler(eventName) {
		var k = _checkForEventAvailability(eventName);
		if (k == -1) {
			// Not event of that name
			return -1;
		}

		return _events[k][1];
	}

	/*
	 * Function: render
	 * Renders widget
	 *
	 * Wrapper to private <_render> function.
	 *
	 */ 
	this.render = function() {
		_render();
	}

	/*
	 * Function: _render
	 * Renders widget
	 *
	 */ 
	function _render() {
		if (!_headers.length) {
			_error('No table header defined!')
			return;
		}
		_container = document.getElementById(_container_id);

		_mainDiv = document.createElement('div');
		_mainDiv.setAttribute('class', 'advancedTable');

		_headerDiv = document.createElement('div');
		_headerDiv.setAttribute('class', 'header');

		_bodyDiv = document.createElement('div');
		_bodyDiv.setAttribute('class', 'body');

		_headerTab = document.createElement('table');
		_bodyTab = document.createElement('table');

		_mainDiv.appendChild(_headerDiv);
		_mainDiv.appendChild(_bodyDiv);

		_headerDiv.appendChild(_headerTab);
		_bodyDiv.appendChild(_bodyTab);
		_container.appendChild(_mainDiv);

		var tr, th;
		tr = document.createElement('tr');
		var cellw = 100.0/_headers.length;

		for (var k=0; k < _headers.length; k++) {
			th = document.createElement('th');
//			th.setAttribute('width', cellw + '%;');
			th.appendChild(document.createTextNode(_headers[k]));
			tr.appendChild(th);
		}
		_headerTab.appendChild(tr);

		var handler;
		for (var k=0; k < _rows.length; k++) {
			tr = document.createElement('tr');
			tr.setAttribute('onclick', _instance_name + '.toggleRowSelection(' + k + ');');

			if (_colIdxForRowIds == -1) {
				// Auto row id
				tr.setAttribute('id', _autoRowIdPrefix + k);
			}

			var row = _rows[k];
			for (var j=0; j < row.length; j++) {
				if (_colIdxForRowIds >= 0 && _colIdxForRowIds == j) {
					// User-defined row ids
					tr.setAttribute('id', _userRowIdPrefix + row[j]);
					continue;
				}
				td = document.createElement('td');
				td.appendChild(document.createTextNode(row[j]));
				tr.appendChild(td);
			}
			_bodyTab.appendChild(tr);
		}
	}

	/*
	 * Function: appendRow
	 * Appends a row of data
	 *
	 * Parameters:
	 *  data - Array of string
	 *
	 */ 
	this.appendRow = function(data) {
		_rows[_rows.length] = data;
	}

	/*
	 * Function: toggleRowSelection
	 * Toggles row selection, possibly executes custom handler
	 *
	 * Handler note:
	 * Custom handler can be exectuted if previously registered with <attachEvent> function for
	 * the *onRowClicked* event. Handler function is passed a single *checked* parameter to 
	 * indicate the row's status check.
	 *
	 * Parameters:
	 *  row - integer: 0-indexed row selected
	 *
	 * See Also:
	 *  <attachEvent>, <_getEventHandler>
	 *
	 */ 
	this.toggleRowSelection = function(row) {
		var rowId = _bodyTab.childNodes[row].id;
		var r = document.getElementById(rowId);
		var cls;
		r.getAttribute('class') == 'rowSelected' ? cls = '' : cls = 'rowSelected';
		r.setAttribute('class', cls);

	 	// Executes custom handler, if any
		 handler = _getEventHandler('onRowClicked');
		 if (typeof handler == 'function')
		 	handler(cls == 'rowSelected' ? true : false);
	}

	/*
	 * Function: selectAll
	 * Un/select all rows in table
	 *
	 * Parameters:
	 *  on - boolean: 0-indexed row selected
	 *
	 */ 
	this.selectAll = function(selected) {
		_selectAll(selected);
	}	

	/*
	 * Function: empty
	 * Removes all table rows
	 *
	 */ 
	this.empty = function() {
		_rows.length = 0;
	}	

	/*
	 * Function: _selectAll
	 * Un/select all rows in table
	 *
	 * Note: can only be called after rendering
	 *
	 * Parameters:
	 *  on - boolean: 0-indexed row selected
	 *
	 * See Also:
	 *  <render>
	 *
	 */ 
	function _selectAll(selected) {
		var rowId, r, cls;
		for (var k=0; k < _rows.length; k++) { 
			rowId = _bodyTab.childNodes[k].id;
			r = document.getElementById(rowId);
			selected ? cls = 'rowSelected' : cls = '';
			r.setAttribute('class', cls);
		}	
	}

	/*
	 * Function: getSelectedRows
	 * Returns a string of comma-separated rows ids
	 *
	 * Returns:
	 *  string of comma-separated rows ids (without <_instance_name> prefix)
	 *
	 */ 
	this.getSelectedRows = function() {
		var rowId, r, cls;
		var selection = '';
		for (var k=0; k < _rows.length; k++) { 
			rowId = _bodyTab.childNodes[k].id;
			r = document.getElementById(rowId);
			if (r.getAttribute('class') == 'rowSelected')
				selection += _rows[k][_colIdxForRowIds] + ',';
		}	

		return selection.substr(0, selection.length-1);
	}

	/*
	 * Function: getRowIdPrefix
	 * Returns a row id prefix used to define row ids
	 *
	 * Returns:
	 *  prefix: string
	 *
	 */ 
	this.getRowIdPrefix = function() {
		return _colIdxForRowIds == -1 ? _autoRowIdPrefix : _userRowIdPrefix;
	}

	/*
	 * Function: getSelectedRows
	 * Returns a string of comma-separated rows ids
	 *
	 * Parameters:
	 *  rowIds - string of comma-separated rows ids (as returned by <getSelectedRows>)
	 *
	 * See Also:
	 *  <getSelectedRows>
	 *
	 */ 
	this.setSelectedRows = function(rowIds) {
		var rowId, r, cls;
		if (typeof rowIds != 'string') {
			_error('setSelectedRows: rowIds must be a valid string of comma-separated values!');
			return;
		}

		// First, unselect all
		_selectAll(false);

		if (!rowIds.length)
			return;

		var selection = rowIds.split(',');
		// Then select rows in the selection
		for (var k=0; k < selection.length; k++) { 
			r = document.getElementById(selection[k]);
			r.setAttribute('class', 'rowSelected');
		}	
	}

	/*
	 * Function: setRowIdsFromColumn
	 * Uses column n value for row unique Id  
	 *
	 * Data in column n of response will be used for row ids only and will not be displayed on the screen.
	 *
	 * Parameters:
	 *  n - integer: column index in response
	 *
	 */ 
	this.setRowIdsFromColumn = function(n) {
		if (typeof n != 'number') {
			_error('setRowIdsFromColumn: n must be a number(integer)!');
			return;
		}

		_colIdxForRowIds = n;
	}

	/*
	 * Function: setHeaders
	 * Sets table headers
	 *
	 * Parameters:
	 *  headers - array: array of string elements (column captions)
	 *
	 */ 
	this.setHeaders = function(headers) {
		if (typeof headers != 'object' || !headers) {
			_error('invalid header used. Must be an array of string elements!');
			return;
		}

		_headers = headers;
	}

	/*
	 * Function: loadDataFromQuery
	 * Sends POST data to URL (Ajax query)
	 *
	 * Response format:
	 * The query result must be a JSON object defining table headers and content:
	 *
	 * > {'Headers' : ['column1', 'col2', 'col3', ...], 'Content' : [['row1col1', 'row1col2', 'row1col3', ...], [...]]}
	 *
	 * Parameters:
	 *  serverPath - string: path to server script
	 *  post - string: raw POST data to send to <serverPath>
	 *  handler - function: Callback function when data has been loaded
	 *
	 */ 
	this.loadDataFromQuery = function(serverPath, post, handler) {
		if (typeof serverPath != 'string' || typeof post != 'string') {
			_error('loadDataFromQuery: serverPath or POST must be strings!');
			return;
		}

		_container = document.getElementById(_container_id);

		var xhr = new HttpRequest(
			_container.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				_container.innerHTML = '';
				_headers = eval(resp['Headers']);
				_rows.length = 0;
				_rows = eval(resp['Content']);
				_render();
				_selectAll(true);

				if (typeof handler != 'function' && handler) {
					_error('loadDataFromQuery: bad handler function!');
					return;
				}
				if (handler) handler();
			}	
		);

		// Send HTTP POST request
		xhr.send(serverPath, post);
	}

	/*
	 * Function: _init
	 * Init function called at instanciation
	 *
	 */ 
	function _init() {
	}

	_init();
}
