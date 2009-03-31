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
 * Class: AdvancedTable
 * Widget to display data into a table with some neat features
 *
 * For convenience, private data member names (both variables and functions) start with an underscore.
 *
 * External Dependancies:
 *  pageswitcher.js - Pagination support with the <PageSwitcher> widget
 *
 * Signals:
 *  advancedTable:selectedImages - signal emitted when calling the <getSelectedColValues> member function
 *
 */
function AdvancedTable() {
	// Group: Constants
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _uid
	 * Unique identifier
	 *
	 */ 
	var _uid = 'ADVT_' + Math.floor(Math.random() * 999999);
	/*
	 * Var: _container
	 * DOM block container element
	 *
	 */
	var _container = null;
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
	var _autoRowIdPrefix = _uid + '.row_';
	/*
	 * Var: _userRowIdPrefix
	 * String prefix used for user-defined row id generation
	 *
	 * Used when when <_colIdxForRowIds> >= 0 
	 *
	 */
	var _userRowIdPrefix = _uid + '.';
	/*
	 * Var: _styles
	 * Array of CSS class names
	 *
	 * See Also:
	 *  <setColStyles>
	 *
	 */ 
	var _styles;
	/*
	 * Var: SERIAL_SELECTED
	 * Char used when all elements in a page are selected (used to fill <_pageStatus>)
	 *
	 */
	var SERIAL_SELECTED = 's';
	/*
	 * Var: SERIAL_UNSELECTED
	 * Char used when all elements in a page are selected (used to fill <_pageStatus>)
	 *
	 */
	var SERIAL_UNSELECTED = 'u';


	// Group: Variables
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _colIdxForRowIds
	 * Column index to use for defining row ids
	 *
	 */
	var _colIdxForRowIds = -1;
	/*
	 * Var: _exclusiveSelectionMode
	 * Exclusive selection mode operation (boolean)
	 *
	 */
	var _exclusiveSelectionMode = false;
	/*
	 * Var: _locked
	 * Lock to prevent overwritting _pageStatus
	 *
	 */
	var _locked = false;
	/*
	 * Var: _postData
	 * Saved POST data
	 *
	 * See Also:
	 *  <loadDataFromQuery>
	 *
	 */
	var _postData = null;
	/*
	 * Var: _pagination
	 * Boolean: whether pagination mode is on [default: false]
	 *
	 */
	var _pagination = false;
	/*
	 * Var: _pageSwitcher
	 * A reference to a pageSwitcher object.
	 *
	 */
	var _pageSwitcher = null;
	/*
	 * Var: _pageStatus
	 * Array of string defining every page status
	 *
	 * Note:
	 * Pagination mode has to be turnedOn (see <activatePagination>)
	 *
	 * Array format:
	 * Each page is formatted 's', 'u' if one chooses 'select all/page' or 'unselect all/page'.
	 * Entries that are manually un/checked add additional information to the page status. 
	 *
	 * For example, if all entries on the page are selected and one manually unchecks rows 2 and 5 
	 * then the pageStatus for this page will be 's,1,4' (0-based indexes, meaning that everything is 
	 * selected on the page except those two rows). Concatenation may occur if 2 (or more) consecutive rows 
	 * are selected on a page: 's,5-15' or 's,5-15,20-21' and so on.
	 *
	 * Example:
	 * A three pages result set may have a page status of
	 * > _pageStatus = ['u,0-1', 's', 's,3']
	 * which means everything on the first page is unselected except the first two rows. The second 
	 * page is fully selected and the third page is almost fully checked except for the fourth row.
	 *
	 * Data Access:
	 * _pageStatus data will be read when restoring (loading) a page. Its data will be written each time the 
	 * current page changes.
	 *
	 */
	var _pageStatus = new Array();
	/*
	 * Var: _mainDiv
	 * Top-level DOM parent div container
	 *
	 */
	var _mainDiv;
	/*
	 * Var: _pageDiv
	 * DOM div for pagination-related stuff
	 *
	 */
	var _pageDiv;
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
	/*
	 * Var: _rowStyles
	 * Array of row custom styles
	 *
	 * Ex: [null, 'style_for_row_1', null, null, 'style_row_4', ...]
	 *
	 * See Also:
	 *  <appendRow>
	 *
	 */
	var _rowStyles = new Array();


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
	 * Function: setColStyles
	 * Uses specified column class names instead of default ones
	 *
	 * Array lenght can be of any size; no checks are made. At rendering time,
	 * if _styles[col_idx] is defined, subsequent style is applied. Exceptions 
	 * are ignored.
	 *
	 * Parameters:
	 *  styles - array of CSS class names, one per column
	 *
	 */ 
	this.setColStyles = function(styles) {
		if (typeof styles != 'object') {
			_error('setColStyles: styles variable must be an array!');
			return;
		}

		_styles = styles;
	}

	/*
	 * Function: setContainer
	 * Sets container parent to use for rendering contents
	 *
	 * Parameters:
	 *  container - string or object: id or DOM node of container element
	 *
	 */ 
	this.setContainer = function(container) {
		_container = container;
	}

	/*
	 * Function: setExclusiveSelectionMode
	 * Defines whether the selection mode should be exclusive.
	 *
	 * Note:
	 *  *Exclusive* means that only _one row can be selected_ at a time.
	 *
	 * Parameters:
	 *  mode - boolean (default: false)
	 *
	 */ 
	this.setExclusiveSelectionMode = function(mode) {
		_exclusiveSelectionMode = typeof mode == 'boolean' ? mode : false;
	}

	/*
	 * Function: getExclusiveSelectionMode
	 * Returns whether the selection mode should be exclusive.
	 *
	 * Returns:
	 *  mode - boolean
	 *
	 */ 
	this.getExclusiveSelectionMode = function(mode) {
		return _exclusiveSelectionMode;
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
		return _container;
	}

	/*
	 * Function: attachEvent
	 * Attach a custom handler to a specific event
	 *
	 * Parameters:
	 *  eventName - string: name of available event
	 *  handler - function: custom handler for that event (can be set to _null_)
	 *
	 * See Also:
	 *  <_events>
	 *
	 */ 
	this.attachEvent = function(eventName, handler) {
		if (typeof handler != 'function' && handler) {
			console.error('bad handler function!');
			return;
		}

		var k = _checkForEventAvailability(eventName);
		if (k == -1) {
			console.error('could not attach unknown event: ' + eventName);
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
		if (k == _events.length)
			return -1;

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
	 * Function: getRowData
	 * Returns an array of a row's cells content
	 *
	 * Parameters:
	 *  row - integer: 0-indexed row selected
	 *
	 */ 
	this.getRowData = function(row) {
		if (typeof row != 'number')
			console.error('row must be an integer!');

		return _rows[row];
	}

	/*
	 * Function: getRoot
	 * Returns root DOM node
	 *
	 * Returns:
	 *  root - DOM node
	 *
	 */ 
	this.getRoot = function() {
		return _mainDiv;
	}		

	/*
	 * Function: _render
	 * Renders widget
	 *
	 */ 
	function _render() {
		_container = $(_container);
		_mainDiv = new Element('div').addClassName('advancedTable');

		_bodyDiv = new Element('div').addClassName('body');
		_bodyTab = new Element('table');

		_pageDiv = new Element('div').addClassName('pagination').hide();
		_mainDiv.insert(_pageDiv);

		if (_headers.length) {
			_headerDiv = new Element('div').addClassName('header');
			_headerTab = new Element('table');
			_mainDiv.insert(_headerDiv);
			_headerDiv.appendChild(_headerTab);
		}

		_mainDiv.insert(_bodyDiv);
		_bodyDiv.insert(_bodyTab);
		_container.insert(_mainDiv);

		var tr, th;
		tr = new Element('tr');
		var cellw = 100.0/_headers.length;

		if (_headers.length) {
			for (var k=0; k < _headers.length; k++) {
				th = new Element('th');
				th.insert(_headers[k]);
				tr.appendChild(th);
			}
			_headerTab.appendChild(tr);
		}

		var handler;
		for (var k=0; k < _rows.length; k++) {
			tr = new Element('tr');
			tr.row_idx = k;
			tr.observe('click', function() {
				if (_exclusiveSelectionMode) _selectAll(false);
				_toggleRowSelection(this.row_idx);
			});

			// Use custom CSS class style for this row?
			if(_rowStyles[k])
				tr.setAttribute('class', _rowStyles[k]);

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
				td = new Element('td');
				try {
					if (_styles[j])
						td.setAttribute('class', _styles[j]);
				} catch(e) {}

				td.insert(row[j]);
				tr.insert(td);
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
	 *  rowStyle - string: CSS row style name
	 *
	 */ 
	this.appendRow = function(data, rowStyle) {
		var j = _rows.length;
		_rows[j] = data;
		if (typeof rowStyle == 'string' && rowStyle.length)
			_rowStyles[j] = rowStyle;
		else
			_rowStyles[j] = null;
	}

	/*
	 * Function: _toggleRowSelection
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
	function _toggleRowSelection(row) {
		var rowId = _bodyTab.childNodes[row].id;
		var r = $(rowId);
		var cls;
		if (r.getAttribute('class') == 'rowSelected')
			_rowStyles[row] ? cls =  _rowStyles[row] : cls = '';
		else
			cls = 'rowSelected';
		r.writeAttribute('class', cls);

	 	// Executes custom handler, if any
		 handler = _getEventHandler('onRowClicked');
		 if (typeof handler == 'function')
		 	handler(cls == 'rowSelected' ? true : false);

		if (!_pageSwitcher) return;
		// In pagination mode

		var cur = _pageSwitcher.getCurrentPage()-1;
		var state = _pageStatus[cur][0] == SERIAL_SELECTED ? false : true;
		if (_pageStatus[cur].length > 1) {
			var sel = _getCurrentPageRowsIdx(state);
			if (sel.length)
				_pageStatus[cur] = _pageStatus[cur].sub(/,.*$/, ',' + sel.toString());
			else
				_pageStatus[cur] = _pageStatus[cur].sub(/,.*$/, '');
		}
		else
			_pageStatus[cur] += ',' + _getCurrentPageRowsIdx(state).toString();
	}

	/*
	 * Function: _getCurrentPageRowsIdx
	 * Get 0-based row indexes on the current page
	 *
	 * Parameters:
	 *  checked - boolean: whether the indexes are related to selected rows
	 *
	 */ 
	function _getCurrentPageRowsIdx(checked) {
		if (typeof checked != 'boolean')
			throw 'checked must be a boolean';

		var idx = new Array();
		_bodyTab.childElements().each(function(tr, k) {
			if (checked) {
				if (tr.hasClassName('rowSelected'))
					idx.push(k);
			}
			else {
				if (!tr.hasClassName('rowSelected'))
					idx.push(k)
			}
		})

		return idx;
	}

	/*
	 * Function: selectAll
	 * Un/select all rows in table
	 *
	 * Parameters:
	 *  See <_selectAll>
	 *
	 */ 
	this.selectAll = function(selected, force) {
		_selectAll(selected, force);
	}	

	/*
	 * Function: empty
	 * Removes all table rows
	 *
	 */ 
	this.empty = function() {
		_rows.length = 0;
		if (_container)
			$(_container).update();
	}	

	/*
	 * Function: _selectAll
	 * Un/select all rows in table (current page)
	 *
	 * Note: can only be called after rendering
	 *
	 * Parameters:
	 *  selected - boolean: if true select all entries of current page
	 *  force - boolean:  if true select all entries on _all_ pages [default: false]
	 *
	 * See Also:
	 *  <render>
	 *
	 */ 
	function _selectAll(selected, force) {
		if (typeof selected != 'boolean') {
			throw 'selected must be a boolean';
			return;
		}
		force = typeof force == 'boolean' ? force : false;

		var rowId, r, cls;
		for (var k=0; k < _rows.length; k++) { 
			rowId = _bodyTab.childNodes[k].id;
			r = $(rowId);
			if (selected) 
				cls = 'rowSelected';
			else {
				// Use custom CSS class style for this row?
				_rowStyles[k] ? cls =  _rowStyles[k] : cls = '';
			}
			if (r) r.writeAttribute('class', cls);
		}	

		if (_pageSwitcher)
			_pageStatus[_pageSwitcher.getCurrentPage()-1] = selected ? SERIAL_SELECTED : SERIAL_UNSELECTED;

		if (!force)
			if (!_pageSwitcher || _locked) return;

		// In pagination mode, reset pages status
		_pageStatus.clear();
		$R(0, _pageSwitcher.getTotalPages()-1).each(function(page) {
			_pageStatus.push(selected ? SERIAL_SELECTED : SERIAL_UNSELECTED);
		});
	}

	/*
	 * Function: getSelectedColsValues
	 * Returns a string of comma-separated columns' values
	 *
	 * Looks for selected rows and builds a selection string with the content 
	 * of the column used to define unique rows ids.
	 *
	 * Returns:
	 *  String of comma-separated selected rows' column's value
	 *
	 */ 
	this.getSelectedColsValues = function() {
		if (!_pagination) {
			var rowId, r, cls, colIdx;
			var selection = '';
			for (var k=0; k < _rows.length; k++) { 
				rowId = _bodyTab.childNodes[k].id;
				r = $(rowId);
				if (r.getAttribute('class') == 'rowSelected') {
					colIdx = _colIdxForRowIds == -1 ? 0 : _colIdxForRowIds;
					selection += _rows[k][colIdx] + ',';
				}
			}	

			return selection.substr(0, selection.length-1);
		}
		else {
			// Pagination mode, we send _pageStatus to the server-side
			// script in order to rebuild the selection
			var xhr = new HttpRequest(
				null,
				// Use default error handler
				null,
				// Custom handler for results
				function(resp) {
					if (resp.Error) {
						throw 'AdvancedTable::getSelectedColValues' + resp.Error;
						return;
					}

					document.fire('advancedTable:selectedImages', resp.idList);
				}	
			);

			// Send HTTP _synchronous_ request
			var post = _postData + '&PageStatus=' + _pageStatus.join('_');
			xhr.send('/youpi/process/query/idListPagination/', post, false);
		}
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
	 * Function: setSelectedRows
	 * Defines row selection
	 *
	 * Parameters:
	 *  rowIds - string of comma-separated rows ids (as returned by <getSelectedColsValues>)
	 *
	 * See Also:
	 *  <getSelectedColsValues>
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
			r = $(selection[k]);
			r.setAttribute('class', 'rowSelected');
		}	
	}

	/*
	 * Function: getSelectedRows
	 * Returns an array of unsigned integer (selected row index in table)
	 *
	 * Returns:
	 *  array of 0-based indexes
	 *
	 */ 
	this.getSelectedRows = function() {
		var idxs = new Array();
		var trs = _bodyDiv.select('tr');
		trs.each(function(tr, k) {
			if (tr.hasClassName('rowSelected'))
				idxs.push(k);
		});

		return idxs;
	}

	/*
	 * Function: rowSelected
	 * Returns true if the row is checked
	 *
	 * Parameters
	 *  row - integer: row 0-based idx
	 *
	 * Returns:
	 *  checked - boolean
	 *
	 */ 
	this.rowSelected = function(row) {
		if (typeof row != 'number') {
			throw "row must be an integer";
			return;
		}

		var tr = $(_bodyTab.childNodes[row].id);
		return tr.hasClassName('rowSelected');
	}

	/*
	 * Function: selectRow
	 * Un/select row
	 *
	 * Parameters
	 *  row - integer: row 0-based idx
	 *  select - boolean: true for selecting row, false to uncheck it (default: true) [optional]
	 *
	 */ 
	this.selectRow = function(row, select) {
		var sel = true;
		if (typeof row != 'number') {
			throw "row must be an integer";
			return;
		}

		if (typeof select != 'undefined') {
			if (typeof select != 'boolean') {
				throw "select must be a boolean";
				return;
			}
			sel = select;
		}

		var tr = $(_bodyTab.childNodes[row].id);
		select ? tr.addClassName('rowSelected') : tr.removeClassName('rowSelected');
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
	 * Function: activatePagination
	 * Activates pagination mode used to navigate through pages
	 *
	 * Parameters:
	 *  on - boolean: true to activate pagination
	 *
	 */ 
	this.activatePagination = function(on) {
		if (typeof on != 'boolean') {
			throw 'on must be a boolean';
			return;
		}

		_pagination = on;
	}

	/*
	 * Function: paginationActivated
	 * Returns true if pagination has been activated
	 *
	 * Returns:
	 *  boolean
	 *
	 */ 
	this.paginationActivated = function() {
		return _pagination;
	}

	/*
	 * Function: loadDataFromQuery
	 * Sends POST data to URL (Ajax query)
	 *
	 * See Also:
	 * <_loadDataFromQuery>
	 *
	 */ 
	this.loadDataFromQuery = function(serverPath, post, handler) {
		_loadDataFromQuery(serverPath, post, handler);
	}

	/*
	 * Function: _loadDataFromQuery
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
	 *  locked - boolean: if true, do not purge _pageStatus content (on page change) [default: false]
	 *
	 */ 
	function _loadDataFromQuery(serverPath, post, handler, locked) {
		if (typeof serverPath != 'string' || typeof post != 'string') {
			_error('loadDataFromQuery: serverPath or POST must be strings!');
			return;
		}

		_locked = typeof locked == 'boolean' ? locked : false;
		_postData = post.sub(/&Page=.*$/, '');
		_container = $(_container);

		var xhr = new HttpRequest(
			_container,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				_container.update();
				_headers = eval(resp['Headers']);
				_rows.length = 0;
				_rows = eval(resp['Content']);
				_render();

				if (typeof handler != 'function' && handler) {
					_error('loadDataFromQuery: bad handler function!');
					return;
				}
				if (handler) handler();

				// Pagination support?
				if (resp.TotalPages && resp.CurrentPage) {
					if (_pagination) {
						_buildPageDiv(serverPath, handler, resp.CurrentPage, resp.TotalPages);
						if (_locked) {
							_setPageState(resp.CurrentPage);
							return;
						}
					}
				}

				_selectAll(true);
			}	
		);

		// Send HTTP POST request
		xhr.send(serverPath, post);
	}

	function _setPageState(page) {
		if (typeof page != 'number')
			throw 'page must be a positive integer';

		var stat = _pageStatus[page-1];
		if (stat == SERIAL_SELECTED) {
			// All selected
			_selectAll(true);

		}
		else if (stat == SERIAL_UNSELECTED) {
			// All unselected
			_selectAll(false);
		}
		else {
			// More complex selection state
			stat[0] == SERIAL_SELECTED ? _selectAll(true) : _selectAll(false);

			// FIXME: serialization
			var rowids = stat.sub(/^.,/, '').split(',');
			rowids.each(function(idx) {
				_toggleRowSelection(idx);
			});
		}
	}

	/*
	 * Function: _buildPageDiv
	 * Add content to the page div
	 *
	 * Parameters:
	 *  serverPath - string: URI for server-side query
	 *  current - integer: current page being displayed
	 *  total - integer: total page count
	 *
	 */ 
	function _buildPageDiv(serverPath, handler, current, total) {
		_pageDiv.update();
		var sall = new Element('input', {type: 'button', value: 'Select page'});
		var uall = new Element('input', {type: 'button', value: 'Unselect page'});
		var pdiv = new Element('span', {id: _uid + 'page_switch_div'});

		// Page switcher widget
		if (!_pageSwitcher) {
			_pageSwitcher = new PageSwitcher(pdiv, function(page) {
				// locked = true to lock _pageStatus content
				_loadDataFromQuery(serverPath, _postData + '&Page=' + page, handler, true);
			});
			_pageSwitcher.setMarginsWidth(6);
		}
		else
			_pageSwitcher.setContainer(pdiv);

		_pageSwitcher.render(current, total);

		sall.observe('click', function() {
			_selectAll(true);
		});

		uall.observe('click', function() {
			_selectAll(false);
		});

		_pageDiv.insert(sall).insert(uall);
		_pageDiv.insert(pdiv);
		_pageDiv.appear();
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
