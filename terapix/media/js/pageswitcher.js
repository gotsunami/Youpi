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
 * Class: PageSwitcher
 * Widget offering page switching capabilities for a data source
 *
 * Constructor Parameters:
 *  container - string or DOM node: name of parent DOM block container
 *  handler - function: custom handler called each time a page is selected
 *
 */
var  PageSwitcher = Class.create({
		
		
	// Group: Constants
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _container
	 * Parent DOM container
	 *
	 */ 
	_container: null,
	/*
	 * Var: _handler
	 * Handler function called when a page is selected
	 *
	 */ 
	_handler: null,


	// Group: Variables
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _margins
	 * Number of pages displayed before and after current page (when possible)
	 *
	 */
	_margins: 5,
	/*
	 * Var: _curPage
	 * Current page number
	 *
	 */
	_curPage: 0,
	/*
	 * Var: _totalPages
	 * Pages count
	 *
	 */
	_totalPages: 0,


	// Group: Functions
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: initialize
	 * Constructor
	 *
	 */ 
	initialize: function(container, handler) {
		this._container = $(container);
		if (!container)
			throw 'container must be a valid DOM container';
		if (typeof handler != 'function') 
			throw 'handler must be a valid handler function';

		this._handler = handler;
	},

	/*
	 * Function: setContainer
	 * Sets widget parent container
	 *
	 * Parameters:
	 *  container - string or DOM node container
	 *
	 */ 
	setContainer: function(container) {
		if (!container)
			throw 'container must be a valid DOM container';
		this._container = $(container);
	},

	/*
	 * Function: getContainer
	 * Return widget parent container
	 *
	 * Returns:
	 *  DOM container
	 *
	 */ 
	getContainer: function() {
		return this._container;
	},

	/*
	 * Function: setMarginsWidth
	 * Defines margins length
	 *
	 * Parameters:
	 *  width - integer: margin width
	 *
	 */ 
	setMarginsWidth: function(width) {
		if (typeof width != 'number')
			throw 'width must be an integer';

		this._margins = width;
	},

	/*
	 * Function: getMarginsWidth
	 * Returns margins length
	 *
	 * Returns:
	 *  Margins width
	 *
	 */ 
	getMarginsWidth: function() {
		return this._margins;
	},

	/*
	 * Function: getCurrentPage
	 * Returns current page number
	 *
	 * Returns:
	 *  page int
	 *
	 */ 
	getCurrentPage: function() {
		return this._curPage;
	},

	/*
	 * Function: getTotalPages
	 * Returns total page number
	 *
	 * Returns:
	 *  Total page count
	 *
	 */ 
	getTotalPages: function() {
		return this._totalPages;
	},

	/*
	 * Function: render
	 * Renders widget
	 *
	 * Parameters:
	 *  curPage - integer: current page number
	 *  pageCount - integer: total page count
	 *
	 */ 
	render: function(curPage, pageCount) {
		if (typeof curPage != 'number' || typeof pageCount != 'number') {
			throw 'render: curPage and pageCount must be integers';
			return;
		}
		this._curPage = curPage;
		this._totalPages = pageCount;
		this._container.update();
		this._container.addClassName('pageSwitcher');
		this._container.insert('Page ');

		if (curPage > 1) {
			var a = new Element('a', {src: '#', title: 'Show page ' + (curPage-1)}).update('<');
			a.observe('click', function() {
				this._handler(curPage-1);
			}.bind(this));
			this._container.insert(a);
		}

		if (pageCount < 6) {
			for (var k=1; k <= pageCount; k++) {
				if (curPage == k)
					this._container.insert(new Element('span').update(k));
				else {
					var a = new Element('a', {src: '#', title: 'Show page ' + k}).update(k);
					a._switchToPage = k;
					a._this = this;
					a.observe('click', function() {
						this._this._handler(this._switchToPage);
					});
					this._container.insert(a);
				}
			}
		}
		else {
			var step, a;
			if (curPage > this._margins+1) {
				// Last page
				a = new Element('a', {src: '#'}).update(1);
				a.observe('click', function() {
					this._handler(1);
				}.bind(this));
				this._container.insert(a);
				// ...
				this._container.insert(' ... ');
			}
			if (curPage > 1) {
				// Before
				step = curPage-this._margins > 0 ? curPage-this._margins : curPage-1;
				for (var k=step; k < curPage; k++) {
					var a = new Element('a', {src: '#', title: 'Show page ' + k}).update(k);
					a._switchToPage = k;
					a._this = this;
					a.observe('click', function() {
						this._this._handler(this._switchToPage);
					});
					this._container.insert(a);
				}
			}

			// Current non-linked page
			this._container.insert(new Element('span').update(curPage));

			if (curPage < pageCount) {
				// After
				step = curPage <= (pageCount-this._margins) ? curPage+this._margins : curPage + 1;
				for (var k=curPage+1; k <= step; k++) {
					var a = new Element('a', {src: '#', title: 'Show page ' + k}).update(k);
					a._switchToPage = k;
					a._this = this;
					a.observe('click', function() {
						this._this._handler(this._switchToPage);
					});
					this._container.insert(a);
				}
			}
			if (curPage < pageCount-2) {
				// ...
				this._container.insert(' ... ');
				// Last page
				a = new Element('a', {src: '#', title: 'Show page ' + pageCount}).update(pageCount);
				a.observe('click', function() {
					this._handler(pageCount);
				}.bind(this));
				this._container.insert(a);
			}
		}

		if (curPage < pageCount) {
			var a = new Element('a', {src: '#', title: 'Show page ' + (curPage+1)}).update('>');
			a.observe('click', function() {
				this._handler(curPage+1);
			}.bind(this));
			this._container.insert(a);
		}

		// Goto page facility
		var gt = new Element('select');
		gt._this = this;
		gt.observe('change', function() {
			this._this._handler(this.selectedIndex + 1);
		});
		for (var k=1; k<=pageCount; k++)
			gt.insert(new Element('option', {value: k}).update('page ' + k));
		var curopt = gt.options[curPage - 1];
		curopt.writeAttribute('selected', 'selected');
		this._container.insert(gt);
	}
});
