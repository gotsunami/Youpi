/*
 * Class: PageSwitcher
 * Widget offering page switching capabilities for a data source
 *
 * Constructor Parameters:
 *  container - string or DOM node: name of parent DOM block container
 *  handler - function: custom handler called each time a page is selected
 *
 */
function PageSwitcher(container, handler) {
	// Group: Constants
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _container
	 * Parent DOM container
	 *
	 */ 
	var _container;
	/*
	 * Var: _handler
	 * Handler function called when a page is selected
	 *
	 */ 
	var _handler;


	// Group: Variables
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _margins
	 * Number of pages displayed before and after current page (when possible)
	 *
	 */
	var _margins = 5;
	/*
	 * Var: _curPage
	 * Current page number
	 *
	 */
	var _curPage;
	/*
	 * Var: _totalPages
	 * Pages count
	 *
	 */
	var _totalPages;


	// Group: Functions
	// -----------------------------------------------------------------------------------------------------------------------------

	/*
	 * Function: setContainer
	 * Sets widget parent container
	 *
	 * Parameters:
	 *  container - string or DOM node container
	 *
	 */ 
	this.setContainer = function(container) {
		_container = $(container);
		if (!container)
			throw 'container must be a valid DOM container';
	}

	/*
	 * Function: getContainer
	 * Return widget parent container
	 *
	 * Returns:
	 *  DOM container
	 *
	 */ 
	this.getContainer = function() {
		return _container;
	}

	/*
	 * Function: setMarginsWidth
	 * Defines margins length
	 *
	 * Parameters:
	 *  width - integer: margin width
	 *
	 */ 
	this.setMarginsWidth = function(width) {
		if (typeof width != 'number')
			throw 'width must be an integer';

		_margins = width;
	}

	/*
	 * Function: getMarginsWidth
	 * Returns margins length
	 *
	 * Returns:
	 *  Margins width
	 *
	 */ 
	this.getMarginsWidth = function() {
		return _margins;
	}

	/*
	 * Function: getCurrentPage
	 * Returns current page number
	 *
	 * Returns:
	 *  page int
	 *
	 */ 
	this.getCurrentPage = function() {
		return _curPage;
	}

	/*
	 * Function: getTotalPages
	 * Returns total page number
	 *
	 * Returns:
	 *  Total page count
	 *
	 */ 
	this.getTotalPages = function() {
		return _totalPages;
	}

	/*
	 * Function: render
	 * Renders widget
	 *
	 * Parameters:
	 *  curPage - integer: current page number
	 *  pageCount - integer: total page count
	 *
	 */ 
	this.render = function(curPage, pageCount) {
		if (typeof curPage != 'number' || typeof pageCount != 'number') {
			throw 'render: curPage and pageCount must be integers';
			return;
		}
		_curPage = curPage;
		_totalPages = pageCount;
		_container.update();
		_container.addClassName('pageSwitcher');
		_container.insert('Page ');

		if (curPage > 1) {
			var a = new Element('a', {src: '#', title: 'Show page ' + (curPage-1)}).update('<');
			a.observe('click', function() {
				_handler(curPage-1);
			});
			_container.insert(a);
		}

		if (pageCount < 6) {
			for (var k=1; k <= pageCount; k++) {
				if (curPage == k)
					_container.insert(new Element('span').update(k));
				else {
					var a = new Element('a', {src: '#'}).update(k);
					a.switch_to_page = k;
					a.observe('click', function() {
						_handler(this.switch_to_page);
					});
					_container.insert(a);
				}
			}
		}
		else {
			var step, a;
			if (curPage > _margins+1) {
				// Last page
				a = new Element('a', {src: '#'}).update(1);
				a.observe('click', function() {
					_handler(1);
				});
				_container.insert(a);
				// ...
				_container.insert(' ... ');
			}
			if (curPage > 1) {
				// Before
				step = curPage-_margins > 0 ? curPage-_margins : curPage-1;
				for (var k=step; k < curPage; k++) {
					var a = new Element('a', {src: '#'}).update(k);
					a.switch_to_page = k;
					a.observe('click', function() {
						_handler(this.switch_to_page);
					});
					_container.insert(a);
				}
			}

			// Current non-linked page
			_container.insert(new Element('span').update(curPage));

			if (curPage < pageCount) {
				// After
				step = curPage <= (pageCount-_margins) ? curPage+_margins : curPage + 1;
				for (var k=curPage+1; k <= step; k++) {
					var a = new Element('a', {src: '#'}).update(k);
					a.switch_to_page = k;
					a.observe('click', function() {
						_handler(this.switch_to_page);
					});
					_container.insert(a);
				}
			}
			if (curPage < pageCount-2) {
				// ...
				_container.insert(' ... ');
				// Last page
				a = new Element('a', {src: '#'}).update(pageCount);
				a.observe('click', function() {
					_handler(pageCount);
				});
				_container.insert(a);
			}
		}

		if (curPage < pageCount) {
			var a = new Element('a', {src: '#', title: 'Show page ' + (curPage+1)}).update('>');
			a.observe('click', function() {
				_handler(curPage+1);
			});
			_container.insert(a);
		}
	}

	/*
	 * Function: _main
	 * MEP
	 *
	 */ 
	function _main() {
		_container = $(container);
		if (!container)
			throw 'container must be a valid DOM container';
		if (typeof handler != 'function') 
			throw 'handler must be a valid handler function';

		_handler = handler;
	}

	_main();
}
